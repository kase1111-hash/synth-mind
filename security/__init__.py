"""
Synth Mind Security Module

Provides integration with Boundary security infrastructure:
- Boundary SIEM: Security event reporting and monitoring
- Boundary Daemon: Policy enforcement and connection protection
- Error Handler: Centralized error handling with security reporting

Usage:
    from security import init_security, get_siem, get_daemon

    # Initialize security (typically at startup)
    init_security()

    # Report security events
    get_siem().report_auth_event("login", success=True, username="admin")

    # Check policies
    response = get_daemon().check_tool_access("shell", "execute")
    if response.decision == PolicyDecision.DENY:
        raise PolicyDeniedError(...)

    # Handle errors with automatic reporting
    @with_error_handling(component="api")
    def my_function():
        ...
"""

from .boundary_daemon import (
    BoundaryDaemon,
    BoundaryMode,
    DaemonConfig,
    PolicyDecision,
    PolicyQuery,
    PolicyResponse,
    ResourceType,
    check_policy,
    get_daemon,
    init_daemon,
)
from .boundary_siem import (
    BoundarySIEM,
    EventCategory,
    SecurityEvent,
    Severity,
    SIEMConfig,
    get_siem,
    init_siem,
    report_event,
)
from .error_handler import (
    ErrorCategory,
    ErrorContext,
    ErrorHandler,
    ErrorSeverity,
    HandledError,
    PolicyDeniedError,
    SecurityViolationError,
    check_input_security,
    get_error_handler,
    handle_error,
    with_error_handling,
    with_policy_check,
    with_retry,
)

__all__ = [
    # SIEM
    "BoundarySIEM",
    "SIEMConfig",
    "SecurityEvent",
    "Severity",
    "EventCategory",
    "get_siem",
    "init_siem",
    "report_event",
    # Daemon
    "BoundaryDaemon",
    "DaemonConfig",
    "BoundaryMode",
    "PolicyDecision",
    "PolicyQuery",
    "PolicyResponse",
    "ResourceType",
    "get_daemon",
    "init_daemon",
    "check_policy",
    # Error Handler
    "ErrorHandler",
    "ErrorContext",
    "ErrorCategory",
    "ErrorSeverity",
    "HandledError",
    "SecurityViolationError",
    "PolicyDeniedError",
    "get_error_handler",
    "handle_error",
    "with_error_handling",
    "with_policy_check",
    "with_retry",
    "check_input_security",
    # Convenience
    "init_security",
    "SecurityConfig",
]


import logging
import os
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class SecurityConfig:
    """Combined security configuration."""

    # SIEM settings
    siem_enabled: bool = True
    siem_api_url: str = "http://localhost:8080"
    siem_api_token: Optional[str] = None
    siem_cef_enabled: bool = False
    siem_cef_host: str = "localhost"
    siem_cef_port: int = 1514

    # Daemon settings
    daemon_enabled: bool = True
    daemon_socket_path: str = "/var/run/boundary/daemon.sock"
    daemon_api_url: str = "http://localhost:9090"
    daemon_fail_closed: bool = True
    daemon_enforce_policy: bool = True

    @classmethod
    def from_env(cls) -> "SecurityConfig":
        """Load configuration from environment variables."""
        return cls(
            siem_enabled=os.getenv("BOUNDARY_SIEM_ENABLED", "true").lower() == "true",
            siem_api_url=os.getenv("BOUNDARY_SIEM_URL", "http://localhost:8080"),
            siem_api_token=os.getenv("BOUNDARY_SIEM_TOKEN"),
            siem_cef_enabled=os.getenv("BOUNDARY_SIEM_CEF_ENABLED", "false").lower() == "true",
            siem_cef_host=os.getenv("BOUNDARY_SIEM_CEF_HOST", "localhost"),
            siem_cef_port=int(os.getenv("BOUNDARY_SIEM_CEF_PORT", "1514")),
            daemon_enabled=os.getenv("BOUNDARY_DAEMON_ENABLED", "true").lower() == "true",
            daemon_socket_path=os.getenv("BOUNDARY_DAEMON_SOCKET", "/var/run/boundary/daemon.sock"),
            daemon_api_url=os.getenv("BOUNDARY_DAEMON_URL", "http://localhost:9090"),
            daemon_fail_closed=os.getenv("BOUNDARY_DAEMON_FAIL_CLOSED", "true").lower() == "true",
            daemon_enforce_policy=os.getenv("BOUNDARY_DAEMON_ENFORCE", "true").lower() == "true",
        )


def init_security(config: Optional[SecurityConfig] = None) -> tuple:
    """
    Initialize all security components.

    Args:
        config: Optional SecurityConfig. If not provided, loads from environment.

    Returns:
        Tuple of (BoundarySIEM, BoundaryDaemon) instances
    """
    if config is None:
        config = SecurityConfig.from_env()

    # Initialize SIEM
    siem = None
    if config.siem_enabled:
        siem_config = SIEMConfig(
            api_url=config.siem_api_url,
            api_token=config.siem_api_token,
            cef_enabled=config.siem_cef_enabled,
            cef_host=config.siem_cef_host,
            cef_port=config.siem_cef_port,
            enabled=True,
        )
        siem = init_siem(siem_config)
        logger.info(f"Boundary SIEM initialized: {config.siem_api_url}")

    # Initialize Daemon
    daemon = None
    if config.daemon_enabled:
        daemon_config = DaemonConfig(
            socket_path=config.daemon_socket_path,
            api_url=config.daemon_api_url,
            fail_closed=config.daemon_fail_closed,
            enforce_policy=config.daemon_enforce_policy,
            enabled=True,
        )
        daemon = init_daemon(daemon_config)
        if daemon.is_connected():
            logger.info(f"Boundary Daemon connected: mode={daemon.get_current_mode().value}")
        else:
            logger.warning("Boundary Daemon not available - running in standalone mode")

    # Report system startup
    if siem:
        siem.report_system_event(
            action="startup",
            message="Synth Mind security initialized",
            details={
                "siem_enabled": config.siem_enabled,
                "daemon_enabled": config.daemon_enabled,
                "daemon_connected": daemon.is_connected() if daemon else False,
            }
        )

    return siem, daemon
