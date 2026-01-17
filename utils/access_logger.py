"""
Access Logger for Synth Mind Dashboard API.

Provides HTTP access logging with support for multiple formats and destinations.
"""

import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Optional


class LogFormat(Enum):
    """Supported log formats."""
    JSON = "json"           # Structured JSON logs
    COMMON = "common"       # Apache Common Log Format
    COMBINED = "combined"   # Apache Combined Log Format
    SIMPLE = "simple"       # Simple human-readable format


@dataclass
class AccessLogConfig:
    """Configuration for access logging."""
    # Enable/disable logging
    enabled: bool = True

    # Log format
    format: LogFormat = LogFormat.JSON

    # Log destinations
    log_to_file: bool = True
    log_to_stdout: bool = False

    # File settings
    log_file: str = "state/access.log"
    max_bytes: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5

    # What to log
    log_request_headers: bool = False
    log_response_headers: bool = False
    log_user_agent: bool = True
    log_referer: bool = True

    # Excluded paths (don't log these)
    excluded_paths: list = field(default_factory=lambda: ["/ws", "/favicon.ico"])

    # Sensitive headers to redact
    redacted_headers: list = field(default_factory=lambda: [
        "authorization", "cookie", "set-cookie", "x-api-key"
    ])


class AccessLogger:
    """
    HTTP access logger with support for multiple formats.

    Logs request/response information for monitoring and debugging.
    """

    def __init__(self, config: AccessLogConfig = None):
        """
        Initialize access logger.

        Args:
            config: Access log configuration
        """
        self.config = config or AccessLogConfig()
        self._logger = None
        self._setup_logger()

    def _setup_logger(self):
        """Set up the logging infrastructure."""
        if not self.config.enabled:
            return

        # Create logger
        self._logger = logging.getLogger("synth_mind.access")
        self._logger.setLevel(logging.INFO)
        self._logger.propagate = False  # Don't propagate to root logger

        # Clear existing handlers
        self._logger.handlers.clear()

        # Add file handler if enabled
        if self.config.log_to_file:
            log_path = Path(self.config.log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            file_handler = RotatingFileHandler(
                str(log_path),
                maxBytes=self.config.max_bytes,
                backupCount=self.config.backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(logging.INFO)
            file_handler.setFormatter(logging.Formatter('%(message)s'))
            self._logger.addHandler(file_handler)

        # Add stdout handler if enabled
        if self.config.log_to_stdout:
            stdout_handler = logging.StreamHandler()
            stdout_handler.setLevel(logging.INFO)
            stdout_handler.setFormatter(logging.Formatter('%(message)s'))
            self._logger.addHandler(stdout_handler)

    def _format_json(self, entry: dict[str, Any]) -> str:
        """Format log entry as JSON."""
        return json.dumps(entry, default=str)

    def _format_common(self, entry: dict[str, Any]) -> str:
        """
        Format log entry in Apache Common Log Format.
        Format: host ident authuser date request status bytes
        """
        host = entry.get("client_ip", "-")
        ident = "-"
        authuser = entry.get("user", "-") or "-"
        date = datetime.fromisoformat(entry["timestamp"]).strftime("[%d/%b/%Y:%H:%M:%S %z]")
        if not date.endswith("]"):
            date = datetime.fromisoformat(entry["timestamp"]).strftime("[%d/%b/%Y:%H:%M:%S +0000]")
        request = f"{entry.get('method', 'GET')} {entry.get('path', '/')} HTTP/1.1"
        status = entry.get("status_code", 200)
        bytes_sent = entry.get("response_size", 0) or "-"

        return f'{host} {ident} {authuser} {date} "{request}" {status} {bytes_sent}'

    def _format_combined(self, entry: dict[str, Any]) -> str:
        """
        Format log entry in Apache Combined Log Format.
        Extends Common format with referer and user-agent.
        """
        common = self._format_common(entry)
        referer = entry.get("referer", "-") or "-"
        user_agent = entry.get("user_agent", "-") or "-"

        return f'{common} "{referer}" "{user_agent}"'

    def _format_simple(self, entry: dict[str, Any]) -> str:
        """Format log entry in simple human-readable format."""
        timestamp = entry.get("timestamp", "")[:19]  # Trim to seconds
        method = entry.get("method", "GET")
        path = entry.get("path", "/")
        status = entry.get("status_code", 200)
        duration_ms = entry.get("duration_ms", 0)
        client_ip = entry.get("client_ip", "-")
        user = entry.get("user", "-") or "-"

        return f"{timestamp} | {method:6} | {status} | {duration_ms:6.1f}ms | {client_ip:15} | {user:15} | {path}"

    def _redact_headers(self, headers: dict[str, str]) -> dict[str, str]:
        """Redact sensitive headers."""
        if not headers:
            return {}

        redacted = {}
        for key, value in headers.items():
            if key.lower() in self.config.redacted_headers:
                redacted[key] = "[REDACTED]"
            else:
                redacted[key] = value
        return redacted

    def log_request(
        self,
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
        client_ip: str,
        user: Optional[str] = None,
        user_agent: Optional[str] = None,
        referer: Optional[str] = None,
        request_headers: Optional[dict[str, str]] = None,
        response_headers: Optional[dict[str, str]] = None,
        response_size: Optional[int] = None,
        extra: Optional[dict[str, Any]] = None
    ):
        """
        Log an HTTP request.

        Args:
            method: HTTP method (GET, POST, etc.)
            path: Request path
            status_code: HTTP response status code
            duration_ms: Request duration in milliseconds
            client_ip: Client IP address
            user: Authenticated username (if any)
            user_agent: User-Agent header
            referer: Referer header
            request_headers: All request headers (will be redacted)
            response_headers: All response headers (will be redacted)
            response_size: Response body size in bytes
            extra: Additional fields to include
        """
        if not self.config.enabled or not self._logger:
            return

        # Check excluded paths
        if any(path.startswith(excluded) for excluded in self.config.excluded_paths):
            return

        # Build log entry
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "method": method,
            "path": path,
            "status_code": status_code,
            "duration_ms": round(duration_ms, 2),
            "client_ip": client_ip,
        }

        # Optional fields
        if user:
            entry["user"] = user

        if self.config.log_user_agent and user_agent:
            entry["user_agent"] = user_agent

        if self.config.log_referer and referer:
            entry["referer"] = referer

        if response_size is not None:
            entry["response_size"] = response_size

        if self.config.log_request_headers and request_headers:
            entry["request_headers"] = self._redact_headers(request_headers)

        if self.config.log_response_headers and response_headers:
            entry["response_headers"] = self._redact_headers(response_headers)

        if extra:
            entry.update(extra)

        # Format based on configured format
        if self.config.format == LogFormat.JSON:
            log_line = self._format_json(entry)
        elif self.config.format == LogFormat.COMMON:
            log_line = self._format_common(entry)
        elif self.config.format == LogFormat.COMBINED:
            log_line = self._format_combined(entry)
        else:  # SIMPLE
            log_line = self._format_simple(entry)

        # Write log
        self._logger.info(log_line)

    def get_stats(self) -> dict[str, Any]:
        """Get logging statistics."""
        stats = {
            "enabled": self.config.enabled,
            "format": self.config.format.value,
            "log_file": self.config.log_file if self.config.log_to_file else None,
            "log_to_stdout": self.config.log_to_stdout,
        }

        # Check log file size
        if self.config.log_to_file:
            log_path = Path(self.config.log_file)
            if log_path.exists():
                stats["log_file_size"] = log_path.stat().st_size
                stats["log_file_size_mb"] = round(log_path.stat().st_size / (1024 * 1024), 2)

                # Count backup files
                backup_count = len(list(log_path.parent.glob(f"{log_path.name}.*")))
                stats["backup_files"] = backup_count

        return stats


def create_access_log_middleware(access_logger: AccessLogger):
    """
    Create an aiohttp middleware for access logging.

    Args:
        access_logger: AccessLogger instance

    Returns:
        aiohttp middleware function
    """
    from aiohttp import web

    @web.middleware
    async def access_log_middleware(request, handler):
        # Record start time
        start_time = time.perf_counter()

        # Get client IP (support for proxies)
        client_ip = request.headers.get(
            'X-Forwarded-For',
            request.headers.get('X-Real-IP', request.remote)
        )
        if client_ip and ',' in client_ip:
            client_ip = client_ip.split(',')[0].strip()

        # Get user info if available
        user = None
        if hasattr(request, 'user') and request.user:
            user = request.user.get('sub') or request.user.get('username')
        elif 'user' in request:
            user_info = request['user']
            if isinstance(user_info, dict):
                user = user_info.get('sub') or user_info.get('username')

        # Process request
        try:
            response = await handler(request)
            status_code = response.status
        except web.HTTPException as e:
            status_code = e.status
            raise
        except Exception:
            status_code = 500
            raise
        finally:
            # Calculate duration
            duration_ms = (time.perf_counter() - start_time) * 1000

            # Get response size if available
            response_size = None
            if 'response' in dir() and hasattr(response, 'content_length'):
                response_size = response.content_length

            # Log the request
            access_logger.log_request(
                method=request.method,
                path=request.path,
                status_code=status_code,
                duration_ms=duration_ms,
                client_ip=client_ip,
                user=user,
                user_agent=request.headers.get('User-Agent'),
                referer=request.headers.get('Referer'),
                response_size=response_size
            )

        return response

    return access_log_middleware


# CLI interface for log analysis
if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Access Log Utilities")
    parser.add_argument("--stats", action="store_true", help="Show log statistics")
    parser.add_argument("--tail", type=int, default=0, help="Show last N log entries")
    parser.add_argument("--log-file", type=str, default="state/access.log",
                       help="Path to log file")
    parser.add_argument("--format", type=str, default="json",
                       choices=["json", "common", "combined", "simple"],
                       help="Log format for parsing")

    args = parser.parse_args()

    log_path = Path(args.log_file)

    if args.stats:
        if not log_path.exists():
            print(f"Log file not found: {log_path}")
            sys.exit(1)

        size = log_path.stat().st_size
        line_count = sum(1 for _ in open(log_path))

        print(f"Log file: {log_path}")
        print(f"Size: {size / 1024:.2f} KB ({size / (1024*1024):.2f} MB)")
        print(f"Lines: {line_count}")

        # Count status codes if JSON format
        if args.format == "json":
            status_counts = {}
            method_counts = {}
            try:
                with open(log_path) as f:
                    for line in f:
                        try:
                            entry = json.loads(line.strip())
                            status = entry.get("status_code", "unknown")
                            method = entry.get("method", "unknown")
                            status_counts[status] = status_counts.get(status, 0) + 1
                            method_counts[method] = method_counts.get(method, 0) + 1
                        except json.JSONDecodeError:
                            pass

                print("\nStatus code distribution:")
                for status, count in sorted(status_counts.items()):
                    print(f"  {status}: {count}")

                print("\nMethod distribution:")
                for method, count in sorted(method_counts.items()):
                    print(f"  {method}: {count}")

            except Exception as e:
                print(f"Error parsing log: {e}")

    elif args.tail > 0:
        if not log_path.exists():
            print(f"Log file not found: {log_path}")
            sys.exit(1)

        with open(log_path) as f:
            lines = f.readlines()
            for line in lines[-args.tail:]:
                print(line.rstrip())

    else:
        parser.print_help()
