"""
IP Firewall for Synth Mind Dashboard API.

Provides IP-based access control with whitelist/blacklist support.
Supports CIDR notation and peer IP management.
"""

import ipaddress
import json
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union


class FirewallMode(Enum):
    """Firewall operation modes."""
    DISABLED = "disabled"       # No IP filtering
    WHITELIST = "whitelist"     # Only allow listed IPs
    BLACKLIST = "blacklist"     # Block listed IPs, allow others
    PEERS_ONLY = "peers_only"   # Only allow configured peers + localhost


@dataclass
class FirewallConfig:
    """Configuration for IP firewall."""
    # Enable/disable firewall
    enabled: bool = True

    # Firewall mode
    mode: FirewallMode = FirewallMode.BLACKLIST

    # IP lists
    whitelist: List[str] = field(default_factory=list)
    blacklist: List[str] = field(default_factory=list)

    # Always allowed IPs (localhost, etc.)
    always_allowed: List[str] = field(default_factory=lambda: [
        "127.0.0.1",
        "::1",
        "localhost",
    ])

    # Peer configuration file
    peers_file: str = "config/peers.txt"

    # Block duration for repeated violations (seconds)
    block_duration: int = 300  # 5 minutes

    # Max violations before auto-block
    max_violations: int = 10

    # Log blocked requests
    log_blocked: bool = True

    # Rules file for persistence
    rules_file: str = "config/firewall_rules.json"


class IPFirewall:
    """
    IP-based firewall with whitelist/blacklist support.

    Provides access control based on client IP addresses.
    Supports CIDR notation for network ranges.
    """

    def __init__(self, config: FirewallConfig = None):
        """
        Initialize IP firewall.

        Args:
            config: Firewall configuration
        """
        self.config = config or FirewallConfig()

        # Parsed IP networks for efficient matching
        self._whitelist_networks: List[Union[ipaddress.IPv4Network, ipaddress.IPv6Network]] = []
        self._blacklist_networks: List[Union[ipaddress.IPv4Network, ipaddress.IPv6Network]] = []
        self._always_allowed: Set[str] = set()
        self._peer_ips: Set[str] = set()

        # Violation tracking
        self._violations: Dict[str, List[float]] = {}  # IP -> list of timestamps
        self._auto_blocked: Dict[str, float] = {}  # IP -> block expiry time

        # Blocked request log
        self._blocked_log: List[Dict] = []
        self._max_log_entries = 1000

        # Initialize
        self._parse_config()
        self._load_peers()
        self._load_rules()

    def _parse_ip_list(self, ip_list: List[str]) -> List[Union[ipaddress.IPv4Network, ipaddress.IPv6Network]]:
        """Parse a list of IPs/CIDRs into network objects."""
        networks = []
        for ip_str in ip_list:
            try:
                ip_str = ip_str.strip()
                if not ip_str or ip_str.startswith('#'):
                    continue

                # Handle CIDR notation
                if '/' in ip_str:
                    networks.append(ipaddress.ip_network(ip_str, strict=False))
                else:
                    # Single IP - convert to /32 or /128 network
                    ip = ipaddress.ip_address(ip_str)
                    if isinstance(ip, ipaddress.IPv4Address):
                        networks.append(ipaddress.ip_network(f"{ip_str}/32"))
                    else:
                        networks.append(ipaddress.ip_network(f"{ip_str}/128"))
            except ValueError as e:
                print(f"Warning: Invalid IP/CIDR '{ip_str}': {e}")
        return networks

    def _parse_config(self):
        """Parse configuration into internal structures."""
        self._whitelist_networks = self._parse_ip_list(self.config.whitelist)
        self._blacklist_networks = self._parse_ip_list(self.config.blacklist)

        # Parse always-allowed IPs
        for ip_str in self.config.always_allowed:
            ip_str = ip_str.strip().lower()
            if ip_str == 'localhost':
                self._always_allowed.add('127.0.0.1')
                self._always_allowed.add('::1')
            else:
                self._always_allowed.add(ip_str)

    def _load_peers(self):
        """Load peer IPs from configuration file."""
        peers_path = Path(self.config.peers_file)
        if not peers_path.exists():
            return

        try:
            with open(peers_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue

                    # Extract IP from URL if present
                    if '://' in line:
                        # Parse URL to get host
                        from urllib.parse import urlparse
                        parsed = urlparse(line)
                        host = parsed.hostname
                        if host:
                            self._peer_ips.add(host)
                    else:
                        # Assume it's just an IP/hostname
                        self._peer_ips.add(line)

            print(f"Loaded {len(self._peer_ips)} peer IPs from {peers_path}")
        except Exception as e:
            print(f"Warning: Could not load peers file: {e}")

    def _load_rules(self):
        """Load persistent rules from file."""
        rules_path = Path(self.config.rules_file)
        if not rules_path.exists():
            return

        try:
            with open(rules_path, 'r') as f:
                data = json.load(f)

            # Load dynamic blacklist
            if 'blacklist' in data:
                additional = self._parse_ip_list(data['blacklist'])
                self._blacklist_networks.extend(additional)

            # Load dynamic whitelist
            if 'whitelist' in data:
                additional = self._parse_ip_list(data['whitelist'])
                self._whitelist_networks.extend(additional)

            print(f"Loaded firewall rules from {rules_path}")
        except Exception as e:
            print(f"Warning: Could not load firewall rules: {e}")

    def _save_rules(self):
        """Save current rules to file."""
        rules_path = Path(self.config.rules_file)
        rules_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            'whitelist': [str(n) for n in self._whitelist_networks],
            'blacklist': [str(n) for n in self._blacklist_networks],
            'updated_at': datetime.utcnow().isoformat()
        }

        try:
            with open(rules_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save firewall rules: {e}")

    def _ip_in_networks(
        self,
        ip: Union[ipaddress.IPv4Address, ipaddress.IPv6Address],
        networks: List[Union[ipaddress.IPv4Network, ipaddress.IPv6Network]]
    ) -> bool:
        """Check if an IP is in any of the given networks."""
        for network in networks:
            try:
                if ip in network:
                    return True
            except TypeError:
                # IPv4/IPv6 mismatch, skip
                continue
        return False

    def _record_violation(self, ip: str):
        """Record a violation for an IP address."""
        now = time.time()

        if ip not in self._violations:
            self._violations[ip] = []

        # Add new violation
        self._violations[ip].append(now)

        # Clean old violations (older than block_duration)
        cutoff = now - self.config.block_duration
        self._violations[ip] = [t for t in self._violations[ip] if t > cutoff]

        # Check if should auto-block
        if len(self._violations[ip]) >= self.config.max_violations:
            self._auto_blocked[ip] = now + self.config.block_duration
            print(f"Auto-blocked IP {ip} for {self.config.block_duration}s due to repeated violations")

    def _log_blocked(self, ip: str, reason: str, path: str = None):
        """Log a blocked request."""
        if not self.config.log_blocked:
            return

        entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'ip': ip,
            'reason': reason,
            'path': path
        }

        self._blocked_log.append(entry)

        # Limit log size
        if len(self._blocked_log) > self._max_log_entries:
            self._blocked_log = self._blocked_log[-self._max_log_entries:]

    def check_ip(self, ip_str: str, path: str = None) -> Tuple[bool, str]:
        """
        Check if an IP address is allowed.

        Args:
            ip_str: IP address to check
            path: Optional request path for logging

        Returns:
            Tuple of (allowed, reason)
        """
        if not self.config.enabled:
            return True, "Firewall disabled"

        # Normalize IP
        ip_str = ip_str.strip()

        # Handle X-Forwarded-For format
        if ',' in ip_str:
            ip_str = ip_str.split(',')[0].strip()

        # Check always-allowed first
        if ip_str in self._always_allowed:
            return True, "Always allowed"

        # Check auto-blocked
        if ip_str in self._auto_blocked:
            if time.time() < self._auto_blocked[ip_str]:
                self._log_blocked(ip_str, "Auto-blocked", path)
                return False, "Auto-blocked due to repeated violations"
            else:
                # Block expired
                del self._auto_blocked[ip_str]

        # Parse IP address
        try:
            ip = ipaddress.ip_address(ip_str)
        except ValueError:
            # Invalid IP format - block by default
            self._log_blocked(ip_str, "Invalid IP format", path)
            return False, f"Invalid IP address format: {ip_str}"

        # Apply mode-specific logic
        if self.config.mode == FirewallMode.DISABLED:
            return True, "Firewall disabled"

        elif self.config.mode == FirewallMode.WHITELIST:
            # Only allow if in whitelist
            if self._ip_in_networks(ip, self._whitelist_networks):
                return True, "Whitelisted"
            self._record_violation(ip_str)
            self._log_blocked(ip_str, "Not in whitelist", path)
            return False, "IP not in whitelist"

        elif self.config.mode == FirewallMode.BLACKLIST:
            # Block if in blacklist
            if self._ip_in_networks(ip, self._blacklist_networks):
                self._record_violation(ip_str)
                self._log_blocked(ip_str, "Blacklisted", path)
                return False, "IP is blacklisted"
            return True, "Allowed"

        elif self.config.mode == FirewallMode.PEERS_ONLY:
            # Only allow peers and localhost
            if ip_str in self._peer_ips:
                return True, "Registered peer"
            # Also check if IP matches peer hostnames
            if any(ip_str == peer for peer in self._peer_ips):
                return True, "Registered peer"
            self._record_violation(ip_str)
            self._log_blocked(ip_str, "Not a registered peer", path)
            return False, "IP not a registered peer"

        return True, "Allowed"

    def add_to_whitelist(self, ip_or_cidr: str) -> bool:
        """Add an IP or CIDR to the whitelist."""
        try:
            networks = self._parse_ip_list([ip_or_cidr])
            if networks:
                self._whitelist_networks.extend(networks)
                self._save_rules()
                return True
        except Exception as e:
            print(f"Error adding to whitelist: {e}")
        return False

    def add_to_blacklist(self, ip_or_cidr: str) -> bool:
        """Add an IP or CIDR to the blacklist."""
        try:
            networks = self._parse_ip_list([ip_or_cidr])
            if networks:
                self._blacklist_networks.extend(networks)
                self._save_rules()
                return True
        except Exception as e:
            print(f"Error adding to blacklist: {e}")
        return False

    def remove_from_whitelist(self, ip_or_cidr: str) -> bool:
        """Remove an IP or CIDR from the whitelist."""
        try:
            networks = self._parse_ip_list([ip_or_cidr])
            for network in networks:
                if network in self._whitelist_networks:
                    self._whitelist_networks.remove(network)
            self._save_rules()
            return True
        except Exception:
            return False

    def remove_from_blacklist(self, ip_or_cidr: str) -> bool:
        """Remove an IP or CIDR from the blacklist."""
        try:
            networks = self._parse_ip_list([ip_or_cidr])
            for network in networks:
                if network in self._blacklist_networks:
                    self._blacklist_networks.remove(network)
            self._save_rules()
            return True
        except Exception:
            return False

    def add_peer(self, ip_or_host: str):
        """Add a peer IP or hostname."""
        self._peer_ips.add(ip_or_host.strip())

    def remove_peer(self, ip_or_host: str):
        """Remove a peer IP or hostname."""
        self._peer_ips.discard(ip_or_host.strip())

    def unblock_ip(self, ip: str):
        """Remove an IP from auto-block."""
        if ip in self._auto_blocked:
            del self._auto_blocked[ip]
        if ip in self._violations:
            del self._violations[ip]

    def get_stats(self) -> Dict:
        """Get firewall statistics."""
        now = time.time()

        return {
            "enabled": self.config.enabled,
            "mode": self.config.mode.value,
            "whitelist_rules": len(self._whitelist_networks),
            "blacklist_rules": len(self._blacklist_networks),
            "peer_ips": len(self._peer_ips),
            "auto_blocked": len([ip for ip, exp in self._auto_blocked.items() if exp > now]),
            "recent_violations": sum(
                len([t for t in times if t > now - 300])
                for times in self._violations.values()
            ),
            "blocked_requests_logged": len(self._blocked_log),
        }

    def get_blocked_log(self, limit: int = 100) -> List[Dict]:
        """Get recent blocked request log."""
        return self._blocked_log[-limit:]

    def get_rules(self) -> Dict:
        """Get current firewall rules."""
        return {
            "whitelist": [str(n) for n in self._whitelist_networks],
            "blacklist": [str(n) for n in self._blacklist_networks],
            "always_allowed": list(self._always_allowed),
            "peers": list(self._peer_ips),
            "auto_blocked": {
                ip: datetime.fromtimestamp(exp).isoformat()
                for ip, exp in self._auto_blocked.items()
                if exp > time.time()
            }
        }


def create_firewall_middleware(firewall: IPFirewall):
    """
    Create an aiohttp middleware for IP filtering.

    Args:
        firewall: IPFirewall instance

    Returns:
        aiohttp middleware function
    """
    from aiohttp import web

    @web.middleware
    async def firewall_middleware(request, handler):
        # Get client IP (support for proxies)
        ip = request.headers.get(
            'X-Forwarded-For',
            request.headers.get('X-Real-IP', request.remote)
        )

        # Check if IP is allowed
        allowed, reason = firewall.check_ip(ip, request.path)

        if not allowed:
            return web.json_response(
                {
                    "error": "Access denied",
                    "reason": reason,
                    "message": "Your IP address is not allowed to access this resource."
                },
                status=403
            )

        return await handler(request)

    return firewall_middleware


# CLI interface
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="IP Firewall Utilities")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Check command
    check_parser = subparsers.add_parser("check", help="Check if an IP is allowed")
    check_parser.add_argument("ip", help="IP address to check")
    check_parser.add_argument("--mode", choices=["whitelist", "blacklist", "peers_only"],
                             default="blacklist", help="Firewall mode")

    # Add command
    add_parser = subparsers.add_parser("add", help="Add IP to whitelist or blacklist")
    add_parser.add_argument("ip", help="IP address or CIDR")
    add_parser.add_argument("--whitelist", action="store_true", help="Add to whitelist")
    add_parser.add_argument("--blacklist", action="store_true", help="Add to blacklist")

    # List command
    list_parser = subparsers.add_parser("list", help="List current rules")

    # Stats command
    stats_parser = subparsers.add_parser("stats", help="Show firewall statistics")

    args = parser.parse_args()

    if args.command == "check":
        mode_map = {
            "whitelist": FirewallMode.WHITELIST,
            "blacklist": FirewallMode.BLACKLIST,
            "peers_only": FirewallMode.PEERS_ONLY,
        }
        config = FirewallConfig(mode=mode_map[args.mode])
        firewall = IPFirewall(config)
        allowed, reason = firewall.check_ip(args.ip)
        print(f"IP: {args.ip}")
        print(f"Allowed: {allowed}")
        print(f"Reason: {reason}")

    elif args.command == "add":
        firewall = IPFirewall()
        if args.whitelist:
            success = firewall.add_to_whitelist(args.ip)
            print(f"Added {args.ip} to whitelist: {success}")
        elif args.blacklist:
            success = firewall.add_to_blacklist(args.ip)
            print(f"Added {args.ip} to blacklist: {success}")
        else:
            print("Specify --whitelist or --blacklist")

    elif args.command == "list":
        firewall = IPFirewall()
        rules = firewall.get_rules()
        print("Current Firewall Rules:")
        print(f"\nWhitelist ({len(rules['whitelist'])} rules):")
        for ip in rules['whitelist']:
            print(f"  {ip}")
        print(f"\nBlacklist ({len(rules['blacklist'])} rules):")
        for ip in rules['blacklist']:
            print(f"  {ip}")
        print(f"\nAlways Allowed:")
        for ip in rules['always_allowed']:
            print(f"  {ip}")
        print(f"\nPeers ({len(rules['peers'])}):")
        for ip in rules['peers']:
            print(f"  {ip}")

    elif args.command == "stats":
        firewall = IPFirewall()
        stats = firewall.get_stats()
        print("Firewall Statistics:")
        for key, value in stats.items():
            print(f"  {key}: {value}")

    else:
        parser.print_help()
