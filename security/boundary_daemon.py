"""
Boundary Daemon Integration for Synth Mind

Provides connection protection and policy enforcement via Boundary Daemon:
- Policy decision queries (allow/deny for operations)
- Connection protection (network access control)
- Boundary mode awareness (OPEN, RESTRICTED, TRUSTED, AIRGAP, etc.)
- Audit logging to daemon
- Automatic lockdown on security violations
"""

import asyncio
import json
import logging
import os
import socket
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from threading import Lock
import hashlib

logger = logging.getLogger(__name__)


class BoundaryMode(str, Enum):
    """Boundary daemon operating modes."""
    OPEN = "open"              # Full network access
    RESTRICTED = "restricted"  # Limited tool access
    TRUSTED = "trusted"        # VPN-only connections
    AIRGAP = "airgap"          # Complete network isolation
    COLDROOM = "coldroom"      # Offline, display-only
    LOCKDOWN = "lockdown"      # Emergency total restriction


class PolicyDecision(str, Enum):
    """Policy decision outcomes."""
    ALLOW = "allow"
    DENY = "deny"
    AUDIT = "audit"  # Allow but log
    UNKNOWN = "unknown"


class ResourceType(str, Enum):
    """Types of resources for policy queries."""
    NETWORK = "network"
    FILE = "file"
    PROCESS = "process"
    TOOL = "tool"
    API = "api"
    LLM = "llm"
    MEMORY = "memory"


@dataclass
class PolicyQuery:
    """Query for policy decision."""
    resource_type: ResourceType
    action: str
    target: str
    context: Dict[str, Any] = field(default_factory=dict)
    actor: Optional[str] = None
    session_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "resource_type": self.resource_type.value,
            "action": self.action,
            "target": self.target,
            "context": self.context,
            "actor": self.actor,
            "session_id": self.session_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


@dataclass
class PolicyResponse:
    """Response from policy query."""
    decision: PolicyDecision
    reason: Optional[str] = None
    expires_at: Optional[str] = None
    constraints: Dict[str, Any] = field(default_factory=dict)
    audit_required: bool = False

    @classmethod
    def deny(cls, reason: str = "Policy denied") -> "PolicyResponse":
        return cls(decision=PolicyDecision.DENY, reason=reason)

    @classmethod
    def allow(cls, reason: str = "Policy allowed") -> "PolicyResponse":
        return cls(decision=PolicyDecision.ALLOW, reason=reason)

    @classmethod
    def default_deny(cls) -> "PolicyResponse":
        """Fail closed - deny on uncertainty."""
        return cls(decision=PolicyDecision.DENY, reason="Default deny - daemon unavailable")


@dataclass
class DaemonConfig:
    """Configuration for Boundary Daemon connection."""

    # Connection settings
    socket_path: str = "/var/run/boundary/daemon.sock"
    api_url: str = "http://localhost:9090"
    use_socket: bool = True  # Prefer Unix socket

    # Authentication
    api_token: Optional[str] = None
    client_cert: Optional[str] = None
    client_key: Optional[str] = None

    # Timeout settings
    connect_timeout: float = 2.0
    query_timeout: float = 1.0

    # Retry settings
    max_retries: int = 2
    retry_delay: float = 0.5

    # Behavior settings
    fail_closed: bool = True  # Deny on daemon unavailable
    cache_decisions: bool = True
    cache_ttl: float = 60.0  # seconds

    # Mode restrictions
    allowed_modes: List[BoundaryMode] = field(default_factory=lambda: [
        BoundaryMode.OPEN,
        BoundaryMode.RESTRICTED,
        BoundaryMode.TRUSTED,
    ])

    # Feature flags
    enabled: bool = True
    enforce_policy: bool = True  # If False, log only
    audit_all: bool = False


class BoundaryDaemon:
    """
    Boundary Daemon client for Synth Mind.

    Provides:
    - Policy decision queries
    - Connection protection
    - Boundary mode awareness
    - Audit logging
    - Automatic lockdown triggers
    """

    def __init__(self, config: Optional[DaemonConfig] = None):
        self.config = config or DaemonConfig()
        self._socket: Optional[socket.socket] = None
        self._current_mode: BoundaryMode = BoundaryMode.OPEN
        self._decision_cache: Dict[str, Tuple[PolicyResponse, float]] = {}
        self._cache_lock = Lock()
        self._connected = False
        self._last_health_check = 0.0
        self._stats = {
            "queries_total": 0,
            "queries_allowed": 0,
            "queries_denied": 0,
            "cache_hits": 0,
            "connection_failures": 0,
            "last_error": None,
        }

    def connect(self) -> bool:
        """Connect to the Boundary Daemon."""
        if not self.config.enabled:
            logger.info("Boundary Daemon integration disabled")
            return False

        try:
            if self.config.use_socket and os.path.exists(self.config.socket_path):
                self._socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                self._socket.settimeout(self.config.connect_timeout)
                self._socket.connect(self.config.socket_path)
                self._connected = True
                logger.info(f"Connected to Boundary Daemon via socket: {self.config.socket_path}")
            else:
                # Fall back to HTTP API
                self._connected = self._check_api_health()
                if self._connected:
                    logger.info(f"Connected to Boundary Daemon via API: {self.config.api_url}")

            if self._connected:
                self._fetch_current_mode()

            return self._connected

        except Exception as e:
            self._stats["connection_failures"] += 1
            self._stats["last_error"] = str(e)
            logger.warning(f"Failed to connect to Boundary Daemon: {e}")
            return False

    def disconnect(self):
        """Disconnect from the daemon."""
        if self._socket:
            try:
                self._socket.close()
            except:
                pass
            self._socket = None
        self._connected = False

    def _check_api_health(self) -> bool:
        """Check if HTTP API is available."""
        try:
            import urllib.request
            req = urllib.request.Request(
                f"{self.config.api_url}/health",
                method="GET"
            )
            with urllib.request.urlopen(req, timeout=self.config.connect_timeout) as resp:
                return resp.status == 200
        except:
            return False

    def _fetch_current_mode(self):
        """Fetch current boundary mode from daemon."""
        try:
            response = self._query_daemon({"command": "get_mode"})
            if response and "mode" in response:
                self._current_mode = BoundaryMode(response["mode"])
                logger.info(f"Boundary mode: {self._current_mode.value}")
        except Exception as e:
            logger.debug(f"Failed to fetch boundary mode: {e}")

    def _query_daemon(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Send query to daemon and get response."""
        if self._socket:
            return self._query_socket(request)
        else:
            return self._query_http(request)

    def _query_socket(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Query via Unix socket."""
        if not self._socket:
            return None

        try:
            # Send request
            data = json.dumps(request).encode() + b"\n"
            self._socket.sendall(data)

            # Receive response
            self._socket.settimeout(self.config.query_timeout)
            response_data = b""
            while True:
                chunk = self._socket.recv(4096)
                if not chunk:
                    break
                response_data += chunk
                if b"\n" in chunk:
                    break

            return json.loads(response_data.decode().strip())

        except Exception as e:
            self._stats["last_error"] = str(e)
            return None

    def _query_http(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Query via HTTP API."""
        try:
            import urllib.request

            headers = {"Content-Type": "application/json"}
            if self.config.api_token:
                headers["Authorization"] = f"Bearer {self.config.api_token}"

            req = urllib.request.Request(
                f"{self.config.api_url}/api/v1/policy/query",
                data=json.dumps(request).encode(),
                headers=headers,
                method="POST"
            )

            with urllib.request.urlopen(req, timeout=self.config.query_timeout) as resp:
                return json.loads(resp.read().decode())

        except Exception as e:
            self._stats["last_error"] = str(e)
            return None

    def _get_cache_key(self, query: PolicyQuery) -> str:
        """Generate cache key for policy query."""
        content = f"{query.resource_type.value}:{query.action}:{query.target}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def _get_cached_decision(self, key: str) -> Optional[PolicyResponse]:
        """Get cached policy decision if valid."""
        if not self.config.cache_decisions:
            return None

        with self._cache_lock:
            if key in self._decision_cache:
                response, timestamp = self._decision_cache[key]
                if time.time() - timestamp < self.config.cache_ttl:
                    self._stats["cache_hits"] += 1
                    return response
                else:
                    del self._decision_cache[key]
        return None

    def _cache_decision(self, key: str, response: PolicyResponse):
        """Cache a policy decision."""
        if self.config.cache_decisions:
            with self._cache_lock:
                self._decision_cache[key] = (response, time.time())

    def query_policy(self, query: PolicyQuery) -> PolicyResponse:
        """
        Query the daemon for a policy decision.

        Returns ALLOW, DENY, or AUDIT based on current mode and policies.
        Fails closed (DENY) if daemon is unavailable and fail_closed is True.
        """
        if not self.config.enabled:
            return PolicyResponse.allow("Daemon disabled")

        self._stats["queries_total"] += 1

        # Check cache first
        cache_key = self._get_cache_key(query)
        cached = self._get_cached_decision(cache_key)
        if cached:
            return cached

        # Check if current mode allows this type of operation
        mode_decision = self._check_mode_restrictions(query)
        if mode_decision.decision == PolicyDecision.DENY:
            self._stats["queries_denied"] += 1
            return mode_decision

        # Query the daemon
        try:
            request = {
                "command": "query_policy",
                "query": query.to_dict(),
            }

            response_data = self._query_daemon(request)

            if response_data:
                response = PolicyResponse(
                    decision=PolicyDecision(response_data.get("decision", "deny")),
                    reason=response_data.get("reason"),
                    expires_at=response_data.get("expires_at"),
                    constraints=response_data.get("constraints", {}),
                    audit_required=response_data.get("audit_required", False),
                )
            else:
                response = self._handle_unavailable()

        except Exception as e:
            self._stats["last_error"] = str(e)
            response = self._handle_unavailable()

        # Update stats and cache
        if response.decision == PolicyDecision.ALLOW:
            self._stats["queries_allowed"] += 1
        else:
            self._stats["queries_denied"] += 1

        self._cache_decision(cache_key, response)
        return response

    def _check_mode_restrictions(self, query: PolicyQuery) -> PolicyResponse:
        """Check if operation is allowed in current mode."""

        # LOCKDOWN denies everything
        if self._current_mode == BoundaryMode.LOCKDOWN:
            return PolicyResponse.deny("System in LOCKDOWN mode")

        # COLDROOM only allows display operations
        if self._current_mode == BoundaryMode.COLDROOM:
            if query.action not in ("read", "display", "view"):
                return PolicyResponse.deny("COLDROOM mode - read-only operations only")

        # AIRGAP denies network operations
        if self._current_mode == BoundaryMode.AIRGAP:
            if query.resource_type == ResourceType.NETWORK:
                return PolicyResponse.deny("AIRGAP mode - no network access")
            if query.resource_type == ResourceType.LLM and "local" not in query.target.lower():
                return PolicyResponse.deny("AIRGAP mode - only local LLM allowed")

        # TRUSTED requires VPN for network
        if self._current_mode == BoundaryMode.TRUSTED:
            if query.resource_type == ResourceType.NETWORK:
                if not query.context.get("via_vpn", False):
                    return PolicyResponse(
                        decision=PolicyDecision.AUDIT,
                        reason="TRUSTED mode - network access logged",
                        audit_required=True
                    )

        # RESTRICTED limits tool access
        if self._current_mode == BoundaryMode.RESTRICTED:
            if query.resource_type == ResourceType.TOOL:
                restricted_tools = ["shell", "code_execute", "file_write"]
                if query.target in restricted_tools:
                    return PolicyResponse.deny(f"RESTRICTED mode - {query.target} not allowed")

        return PolicyResponse.allow("Mode check passed")

    def _handle_unavailable(self) -> PolicyResponse:
        """Handle daemon unavailable situation."""
        self._stats["connection_failures"] += 1

        if self.config.fail_closed:
            return PolicyResponse.default_deny()
        else:
            return PolicyResponse(
                decision=PolicyDecision.AUDIT,
                reason="Daemon unavailable - allowing with audit",
                audit_required=True
            )

    def check_network_access(
        self,
        host: str,
        port: int,
        protocol: str = "tcp"
    ) -> PolicyResponse:
        """Check if network access to host:port is allowed."""
        query = PolicyQuery(
            resource_type=ResourceType.NETWORK,
            action="connect",
            target=f"{host}:{port}",
            context={"protocol": protocol}
        )
        return self.query_policy(query)

    def check_tool_access(
        self,
        tool_name: str,
        action: str = "execute",
        context: Optional[Dict[str, Any]] = None
    ) -> PolicyResponse:
        """Check if tool execution is allowed."""
        query = PolicyQuery(
            resource_type=ResourceType.TOOL,
            action=action,
            target=tool_name,
            context=context or {}
        )
        return self.query_policy(query)

    def check_llm_access(
        self,
        provider: str,
        model: str,
        action: str = "generate"
    ) -> PolicyResponse:
        """Check if LLM API access is allowed."""
        query = PolicyQuery(
            resource_type=ResourceType.LLM,
            action=action,
            target=f"{provider}/{model}",
            context={"provider": provider, "model": model}
        )
        return self.query_policy(query)

    def check_file_access(
        self,
        path: str,
        action: str = "read"
    ) -> PolicyResponse:
        """Check if file access is allowed."""
        query = PolicyQuery(
            resource_type=ResourceType.FILE,
            action=action,
            target=path,
        )
        return self.query_policy(query)

    def report_violation(
        self,
        violation_type: str,
        description: str,
        severity: str = "high",
        details: Optional[Dict[str, Any]] = None
    ):
        """Report a security violation to the daemon."""
        try:
            request = {
                "command": "report_violation",
                "violation": {
                    "type": violation_type,
                    "description": description,
                    "severity": severity,
                    "details": details or {},
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "source": "synth-mind",
                }
            }
            self._query_daemon(request)
        except Exception as e:
            logger.debug(f"Failed to report violation: {e}")

    def request_mode_change(
        self,
        target_mode: BoundaryMode,
        reason: str
    ) -> bool:
        """Request a mode change from the daemon."""
        try:
            request = {
                "command": "request_mode_change",
                "target_mode": target_mode.value,
                "reason": reason,
                "source": "synth-mind",
            }
            response = self._query_daemon(request)
            if response and response.get("approved"):
                self._current_mode = target_mode
                return True
            return False
        except:
            return False

    def trigger_lockdown(self, reason: str):
        """Trigger emergency lockdown."""
        try:
            request = {
                "command": "trigger_lockdown",
                "reason": reason,
                "source": "synth-mind",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            self._query_daemon(request)
            self._current_mode = BoundaryMode.LOCKDOWN
            logger.critical(f"LOCKDOWN triggered: {reason}")
        except Exception as e:
            logger.error(f"Failed to trigger lockdown: {e}")

    def get_current_mode(self) -> BoundaryMode:
        """Get current boundary mode."""
        return self._current_mode

    def is_connected(self) -> bool:
        """Check if connected to daemon."""
        return self._connected

    def get_stats(self) -> Dict[str, Any]:
        """Get client statistics."""
        return {
            **self._stats,
            "connected": self._connected,
            "current_mode": self._current_mode.value,
            "cache_size": len(self._decision_cache),
            "enabled": self.config.enabled,
        }


# Global daemon client instance
_daemon_client: Optional[BoundaryDaemon] = None


def get_daemon() -> Optional[BoundaryDaemon]:
    """Get the global daemon client instance."""
    return _daemon_client


def init_daemon(config: Optional[DaemonConfig] = None) -> BoundaryDaemon:
    """Initialize and connect the global daemon client."""
    global _daemon_client

    if _daemon_client is not None:
        _daemon_client.disconnect()

    _daemon_client = BoundaryDaemon(config)
    _daemon_client.connect()

    return _daemon_client


def check_policy(query: PolicyQuery) -> PolicyResponse:
    """Check policy using the global daemon client."""
    if _daemon_client:
        return _daemon_client.query_policy(query)
    return PolicyResponse.allow("Daemon not initialized")
