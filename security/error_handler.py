"""
Centralized Error Handling with Security Reporting

Provides:
- Structured error handling with automatic SIEM reporting
- Security violation detection and escalation
- Connection protection via Boundary Daemon
- Automatic retry with exponential backoff
- Error categorization and aggregation
"""

import asyncio
import functools
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Optional, TypeVar

from .boundary_daemon import (
    PolicyDecision,
    PolicyQuery,
    ResourceType,
    get_daemon,
)
from .boundary_siem import Severity, get_siem

logger = logging.getLogger(__name__)

T = TypeVar('T')


class ErrorCategory(str, Enum):
    """Categories of errors for handling and reporting."""
    NETWORK = "network"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    VALIDATION = "validation"
    DATABASE = "database"
    LLM = "llm"
    TOOL = "tool"
    SECURITY = "security"
    CONFIGURATION = "configuration"
    RESOURCE = "resource"
    INTERNAL = "internal"
    UNKNOWN = "unknown"


class ErrorSeverity(Enum):
    """Error severity levels."""
    DEBUG = (0, Severity.UNKNOWN)
    INFO = (1, Severity.LOW)
    WARNING = (2, Severity.LOW)
    ERROR = (3, Severity.MEDIUM)
    CRITICAL = (4, Severity.HIGH)
    SECURITY = (5, Severity.CRITICAL)

    def __init__(self, level: int, siem_severity: int):
        self.level = level
        self.siem_severity = siem_severity


@dataclass
class ErrorContext:
    """Context information for error handling."""
    operation: str
    component: str = "unknown"
    user: Optional[str] = None
    ip_address: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    resource: Optional[str] = None
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class HandledError:
    """Structured error with metadata."""
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    original_error: Optional[Exception] = None
    context: Optional[ErrorContext] = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    error_code: Optional[str] = None
    recoverable: bool = True
    reported: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "category": self.category.value,
            "severity": self.severity.name,
            "message": self.message,
            "error_code": self.error_code,
            "timestamp": self.timestamp,
            "recoverable": self.recoverable,
            "context": {
                "operation": self.context.operation if self.context else None,
                "component": self.context.component if self.context else None,
            } if self.context else None,
        }


# Security violation patterns
SECURITY_PATTERNS = [
    # SQL Injection
    (r"(?i)(union\s+select|;\s*drop|;\s*delete|;\s*update|--\s*$)", "sql_injection"),
    # Command Injection
    (r"(?i)(\||;|`|\$\(|&&|\|\|).*?(rm|cat|wget|curl|bash|sh|nc)", "command_injection"),
    # Path Traversal
    (r"(?:\.\./|\.\.\\|%2e%2e%2f|%2e%2e/|\.%2e/)", "path_traversal"),
    # XSS
    (r"(?i)(<script|javascript:|on\w+\s*=)", "xss_attempt"),
    # Prompt Injection (basic patterns)
    (r"(?i)(ignore\s+(previous|above|all)\s+instructions|system\s+prompt)", "prompt_injection"),
]


class SecurityViolationError(Exception):
    """Exception for security violations."""

    def __init__(
        self,
        violation_type: str,
        message: str,
        details: Optional[dict[str, Any]] = None
    ):
        super().__init__(message)
        self.violation_type = violation_type
        self.details = details or {}


class PolicyDeniedError(Exception):
    """Exception when policy denies an operation."""

    def __init__(self, resource: str, action: str, reason: str):
        super().__init__(f"Policy denied: {action} on {resource} - {reason}")
        self.resource = resource
        self.action = action
        self.reason = reason


class ErrorHandler:
    """
    Centralized error handler with security integration.

    Features:
    - Automatic error categorization
    - SIEM event reporting
    - Security violation detection
    - Policy enforcement via daemon
    - Retry logic with backoff
    - Error aggregation and stats
    """

    def __init__(self):
        self._error_counts: dict[str, int] = {}
        self._recent_errors: list[HandledError] = []
        self._max_recent = 100
        self._violation_count = 0
        self._lockdown_threshold = 5  # Violations before lockdown

    def handle(
        self,
        error: Exception,
        context: Optional[ErrorContext] = None,
        reraise: bool = True
    ) -> HandledError:
        """
        Handle an exception with automatic categorization and reporting.

        Args:
            error: The exception to handle
            context: Optional context about the operation
            reraise: Whether to re-raise the exception after handling

        Returns:
            HandledError with structured error information
        """
        # Categorize the error
        category, severity = self._categorize_error(error)

        # Check for security violations
        security_violation = self._check_security_violation(error, context)
        if security_violation:
            category = ErrorCategory.SECURITY
            severity = ErrorSeverity.SECURITY
            self._handle_security_violation(security_violation, error, context)

        # Create structured error
        handled = HandledError(
            category=category,
            severity=severity,
            message=str(error),
            original_error=error,
            context=context,
            error_code=self._get_error_code(error),
            recoverable=self._is_recoverable(error),
        )

        # Update stats
        self._update_stats(handled)

        # Report to SIEM
        self._report_to_siem(handled)

        # Log locally
        self._log_error(handled)

        if reraise:
            raise error

        return handled

    def _categorize_error(self, error: Exception) -> tuple[ErrorCategory, ErrorSeverity]:
        """Categorize an error based on its type and message."""
        error_type = type(error).__name__
        error_msg = str(error).lower()

        # Network errors
        if any(t in error_type for t in ["Connection", "Timeout", "Socket", "HTTP"]):
            return ErrorCategory.NETWORK, ErrorSeverity.WARNING

        if any(t in error_type for t in ["URLError", "RequestException"]):
            return ErrorCategory.NETWORK, ErrorSeverity.WARNING

        # Authentication errors
        if any(t in error_type for t in ["Auth", "Token", "Credential"]):
            return ErrorCategory.AUTHENTICATION, ErrorSeverity.WARNING

        if "unauthorized" in error_msg or "401" in error_msg:
            return ErrorCategory.AUTHENTICATION, ErrorSeverity.WARNING

        # Authorization errors
        if "forbidden" in error_msg or "403" in error_msg or "permission" in error_msg:
            return ErrorCategory.AUTHORIZATION, ErrorSeverity.WARNING

        # Validation errors
        if any(t in error_type for t in ["Validation", "ValueError", "TypeError"]):
            return ErrorCategory.VALIDATION, ErrorSeverity.INFO

        # Database errors
        if any(t in error_type for t in ["SQL", "Database", "Integrity"]):
            return ErrorCategory.DATABASE, ErrorSeverity.ERROR

        # Security-specific errors
        if isinstance(error, SecurityViolationError):
            return ErrorCategory.SECURITY, ErrorSeverity.SECURITY

        if isinstance(error, PolicyDeniedError):
            return ErrorCategory.AUTHORIZATION, ErrorSeverity.WARNING

        # LLM errors
        if any(t in error_type for t in ["API", "RateLimit", "Anthropic", "OpenAI"]):
            return ErrorCategory.LLM, ErrorSeverity.WARNING

        # Resource errors
        if any(t in error_type for t in ["Memory", "Resource", "Limit"]):
            return ErrorCategory.RESOURCE, ErrorSeverity.ERROR

        # Default
        return ErrorCategory.UNKNOWN, ErrorSeverity.ERROR

    def _check_security_violation(
        self,
        error: Exception,
        context: Optional[ErrorContext]
    ) -> Optional[str]:
        """Check if error indicates a security violation."""
        if isinstance(error, SecurityViolationError):
            return error.violation_type

        # Check error message for security patterns
        error_msg = str(error)
        for pattern, violation_type in SECURITY_PATTERNS:
            if re.search(pattern, error_msg):
                return violation_type

        # Check context details if available
        if context and context.details:
            for _key, value in context.details.items():
                if isinstance(value, str):
                    for pattern, violation_type in SECURITY_PATTERNS:
                        if re.search(pattern, value):
                            return violation_type

        return None

    def _handle_security_violation(
        self,
        violation_type: str,
        error: Exception,
        context: Optional[ErrorContext]
    ):
        """Handle a detected security violation."""
        self._violation_count += 1

        # Report to SIEM
        siem = get_siem()
        if siem:
            siem.report_security_violation(
                violation_type=violation_type,
                description=str(error),
                ip_address=context.ip_address if context else None,
                username=context.user if context else None,
                details={
                    "operation": context.operation if context else None,
                    "component": context.component if context else None,
                    "violation_count": self._violation_count,
                }
            )

        # Report to daemon
        daemon = get_daemon()
        if daemon:
            daemon.report_violation(
                violation_type=violation_type,
                description=str(error),
                severity="critical" if self._violation_count > 3 else "high",
                details=context.details if context else {}
            )

            # Trigger lockdown if threshold exceeded
            if self._violation_count >= self._lockdown_threshold:
                daemon.trigger_lockdown(
                    f"Security violation threshold exceeded: {self._violation_count} violations"
                )

    def _get_error_code(self, error: Exception) -> Optional[str]:
        """Extract or generate error code."""
        if hasattr(error, 'code'):
            return str(error.code)
        if hasattr(error, 'errno'):
            return str(error.errno)
        if hasattr(error, 'status_code'):
            return str(error.status_code)
        return None

    def _is_recoverable(self, error: Exception) -> bool:
        """Determine if error is recoverable."""
        error_type = type(error).__name__

        # Non-recoverable errors
        non_recoverable = [
            "SystemExit", "KeyboardInterrupt", "MemoryError",
            "SecurityViolationError", "PolicyDeniedError"
        ]
        if error_type in non_recoverable:
            return False

        # Recoverable errors
        recoverable = [
            "ConnectionError", "TimeoutError", "RateLimitError",
            "TemporaryError", "RetryableError"
        ]
        if error_type in recoverable:
            return True

        # Default based on message
        msg = str(error).lower()
        if any(word in msg for word in ["temporary", "retry", "timeout"]):
            return True
        if any(word in msg for word in ["fatal", "critical", "corrupt"]):
            return False

        return True

    def _update_stats(self, handled: HandledError):
        """Update error statistics."""
        key = f"{handled.category.value}:{handled.severity.name}"
        self._error_counts[key] = self._error_counts.get(key, 0) + 1

        # Keep recent errors
        self._recent_errors.append(handled)
        if len(self._recent_errors) > self._max_recent:
            self._recent_errors.pop(0)

    def _report_to_siem(self, handled: HandledError):
        """Report error to SIEM."""
        siem = get_siem()
        if not siem:
            return

        siem.report_error(
            error_type=handled.category.value,
            error_message=handled.message,
            error_code=handled.error_code,
            severity=handled.severity.siem_severity,
            details={
                "recoverable": handled.recoverable,
                "context": handled.context.details if handled.context else {},
            }
        )
        handled.reported = True

    def _log_error(self, handled: HandledError):
        """Log error locally."""
        log_msg = f"[{handled.category.value}] {handled.message}"

        if handled.context:
            log_msg += f" (operation={handled.context.operation})"

        if handled.severity.level >= ErrorSeverity.CRITICAL.level:
            logger.critical(log_msg)
        elif handled.severity.level >= ErrorSeverity.ERROR.level:
            logger.error(log_msg)
        elif handled.severity.level >= ErrorSeverity.WARNING.level:
            logger.warning(log_msg)
        else:
            logger.info(log_msg)

    def get_stats(self) -> dict[str, Any]:
        """Get error statistics."""
        return {
            "error_counts": dict(self._error_counts),
            "recent_errors": len(self._recent_errors),
            "violation_count": self._violation_count,
            "lockdown_threshold": self._lockdown_threshold,
        }

    def get_recent_errors(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get recent errors."""
        return [e.to_dict() for e in self._recent_errors[-limit:]]


# Global error handler instance
_error_handler = ErrorHandler()


def get_error_handler() -> ErrorHandler:
    """Get the global error handler."""
    return _error_handler


def handle_error(
    error: Exception,
    context: Optional[ErrorContext] = None,
    reraise: bool = True
) -> HandledError:
    """Handle an error using the global handler."""
    return _error_handler.handle(error, context, reraise)


def with_error_handling(
    component: str = "unknown",
    operation: Optional[str] = None,
    reraise: bool = True
):
    """
    Decorator for automatic error handling.

    Usage:
        @with_error_handling(component="api", operation="get_state")
        def get_state():
            ...

        @with_error_handling(component="llm")
        async def generate_response():
            ...
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        op_name = operation or func.__name__

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            context = ErrorContext(
                operation=op_name,
                component=component,
                details={"args_count": len(args), "kwargs_keys": list(kwargs.keys())}
            )
            try:
                return func(*args, **kwargs)
            except Exception as e:
                handle_error(e, context, reraise=reraise)
                if not reraise:
                    return None

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            context = ErrorContext(
                operation=op_name,
                component=component,
                details={"args_count": len(args), "kwargs_keys": list(kwargs.keys())}
            )
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                handle_error(e, context, reraise=reraise)
                if not reraise:
                    return None

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def with_policy_check(
    resource_type: ResourceType,
    action: str,
    get_target: Optional[Callable[..., str]] = None
):
    """
    Decorator for policy-checked operations.

    Usage:
        @with_policy_check(ResourceType.TOOL, "execute", lambda name: name)
        def execute_tool(name: str):
            ...
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            daemon = get_daemon()
            if not daemon:
                return func(*args, **kwargs)

            # Determine target
            if get_target:
                target = get_target(*args, **kwargs)
            elif args:
                target = str(args[0])
            else:
                target = func.__name__

            # Query policy
            query = PolicyQuery(
                resource_type=resource_type,
                action=action,
                target=target
            )
            response = daemon.query_policy(query)

            if response.decision == PolicyDecision.DENY:
                raise PolicyDeniedError(target, action, response.reason or "Policy denied")

            return func(*args, **kwargs)

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            daemon = get_daemon()
            if not daemon:
                return await func(*args, **kwargs)

            if get_target:
                target = get_target(*args, **kwargs)
            elif args:
                target = str(args[0])
            else:
                target = func.__name__

            query = PolicyQuery(
                resource_type=resource_type,
                action=action,
                target=target
            )
            response = daemon.query_policy(query)

            if response.decision == PolicyDecision.DENY:
                raise PolicyDeniedError(target, action, response.reason or "Policy denied")

            return await func(*args, **kwargs)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return wrapper

    return decorator


def with_retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple[type[Exception], ...] = (Exception,)
):
    """
    Decorator for automatic retry with exponential backoff.

    Usage:
        @with_retry(max_attempts=3, exceptions=(ConnectionError, TimeoutError))
        async def fetch_data():
            ...
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        wait = delay * (backoff ** attempt)
                        logger.debug(f"Retry {attempt + 1}/{max_attempts} after {wait}s: {e}")
                        import time
                        time.sleep(wait)
            raise last_error

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        wait = delay * (backoff ** attempt)
                        logger.debug(f"Retry {attempt + 1}/{max_attempts} after {wait}s: {e}")
                        await asyncio.sleep(wait)
            raise last_error

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def check_input_security(value: str, context: str = "input") -> str:
    """
    Check input string for security violations.

    Raises SecurityViolationError if a violation is detected.
    """
    for pattern, violation_type in SECURITY_PATTERNS:
        if re.search(pattern, value):
            raise SecurityViolationError(
                violation_type=violation_type,
                message=f"Security violation detected in {context}",
                details={"pattern": pattern, "context": context}
            )
    return value
