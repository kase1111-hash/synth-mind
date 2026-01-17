"""
Boundary SIEM Integration for Synth Mind

Provides security event reporting to Boundary SIEM for:
- Authentication events (login, logout, failed attempts)
- API access events (requests, errors, rate limits)
- Security violations (injection attempts, unauthorized access)
- System events (startup, shutdown, errors)
- Cognitive events (project creation, tool execution)
"""

import hashlib
import json
import logging
import socket
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import IntEnum
from queue import Queue
from threading import Lock, Thread
from typing import Any, Optional

try:
    import aiohttp
except ImportError:
    aiohttp = None

logger = logging.getLogger(__name__)


class Severity(IntEnum):
    """CEF Severity levels (0-10)."""
    UNKNOWN = 0
    LOW = 3
    MEDIUM = 5
    HIGH = 7
    CRITICAL = 10


class EventCategory(str):
    """Event categories for classification."""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    ACCESS = "access"
    NETWORK = "network"
    SYSTEM = "system"
    APPLICATION = "application"
    SECURITY = "security"
    COGNITIVE = "cognitive"


@dataclass
class SecurityEvent:
    """Security event for SIEM reporting."""

    # Required fields
    action: str
    outcome: str  # "success", "failure", "unknown"
    severity: int = Severity.LOW

    # Source information
    source_product: str = "synth-mind"
    source_host: str = field(default_factory=socket.gethostname)
    source_version: str = "0.1.0-alpha"

    # Event metadata
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    event_id: str = ""
    category: str = EventCategory.APPLICATION

    # Actor information
    actor_user: Optional[str] = None
    actor_ip: Optional[str] = None
    actor_session: Optional[str] = None

    # Target information
    target_resource: Optional[str] = None
    target_action: Optional[str] = None

    # Additional context
    message: Optional[str] = None
    details: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)

    # Error information
    error_code: Optional[str] = None
    error_message: Optional[str] = None

    def __post_init__(self):
        """Generate event ID if not provided."""
        if not self.event_id:
            # Create deterministic ID from event content
            content = f"{self.timestamp}{self.action}{self.source_host}"
            self.event_id = hashlib.sha256(content.encode()).hexdigest()[:16]

    def to_json(self) -> dict[str, Any]:
        """Convert to JSON format for HTTP API."""
        return {
            "timestamp": self.timestamp,
            "event_id": self.event_id,
            "source": {
                "product": self.source_product,
                "host": self.source_host,
                "version": self.source_version,
            },
            "action": self.action,
            "outcome": self.outcome,
            "severity": self.severity,
            "category": self.category,
            "actor": {
                "user": self.actor_user,
                "ip": self.actor_ip,
                "session": self.actor_session,
            } if any([self.actor_user, self.actor_ip, self.actor_session]) else None,
            "target": {
                "resource": self.target_resource,
                "action": self.target_action,
            } if any([self.target_resource, self.target_action]) else None,
            "message": self.message,
            "details": self.details if self.details else None,
            "tags": self.tags if self.tags else None,
            "error": {
                "code": self.error_code,
                "message": self.error_message,
            } if self.error_code or self.error_message else None,
        }

    def to_cef(self) -> str:
        """Convert to CEF (Common Event Format) string."""
        # CEF:Version|Device Vendor|Device Product|Device Version|Signature ID|Name|Severity|Extension

        # Build extension key-value pairs
        extensions = []

        if self.actor_ip:
            extensions.append(f"src={self.actor_ip}")
        if self.actor_user:
            extensions.append(f"suser={self.actor_user}")
        if self.target_resource:
            extensions.append(f"destinationServiceName={self.target_resource}")
        if self.message:
            # Escape special characters in message
            msg = self.message.replace("\\", "\\\\").replace("=", "\\=")
            extensions.append(f"msg={msg}")
        if self.outcome:
            extensions.append(f"outcome={self.outcome}")

        extension_str = " ".join(extensions)

        # Create signature ID from action
        sig_id = hashlib.md5(self.action.encode()).hexdigest()[:8]

        return (
            f"CEF:0|Boundary|SynthMind|{self.source_version}|"
            f"{sig_id}|{self.action}|{self.severity}|{extension_str}"
        )


@dataclass
class SIEMConfig:
    """Configuration for Boundary SIEM connection."""

    # HTTP API settings
    api_url: str = "http://localhost:8080"
    api_token: Optional[str] = None
    api_timeout: float = 5.0

    # CEF/Syslog settings
    cef_enabled: bool = False
    cef_host: str = "localhost"
    cef_port: int = 1514
    cef_protocol: str = "tcp"  # "tcp" or "udp"

    # Batching settings
    batch_size: int = 100
    batch_timeout: float = 5.0

    # Retry settings
    max_retries: int = 3
    retry_delay: float = 1.0
    retry_backoff: float = 2.0

    # Filtering
    min_severity: int = Severity.LOW
    enabled_categories: list[str] = field(default_factory=lambda: [
        EventCategory.AUTHENTICATION,
        EventCategory.AUTHORIZATION,
        EventCategory.SECURITY,
        EventCategory.SYSTEM,
    ])

    # Feature flags
    enabled: bool = True
    async_mode: bool = True


class BoundarySIEM:
    """
    Boundary SIEM client for Synth Mind.

    Provides:
    - Event reporting via HTTP API and CEF/Syslog
    - Automatic batching and retry logic
    - Async and sync modes
    - Event filtering by severity and category
    """

    def __init__(self, config: Optional[SIEMConfig] = None):
        self.config = config or SIEMConfig()
        self._event_queue: Queue = Queue()
        self._batch: list[SecurityEvent] = []
        self._batch_lock = Lock()
        self._running = False
        self._worker_thread: Optional[Thread] = None
        self._cef_socket: Optional[socket.socket] = None
        self._session: Optional[aiohttp.ClientSession] = None
        self._stats = {
            "events_sent": 0,
            "events_failed": 0,
            "batches_sent": 0,
            "last_error": None,
            "last_send_time": None,
        }

    def start(self):
        """Start the background event sender."""
        if not self.config.enabled:
            logger.info("Boundary SIEM integration disabled")
            return

        self._running = True

        if self.config.async_mode:
            self._worker_thread = Thread(target=self._worker_loop, daemon=True)
            self._worker_thread.start()
            logger.info(f"Boundary SIEM client started (API: {self.config.api_url})")

        if self.config.cef_enabled:
            self._connect_cef()

    def stop(self):
        """Stop the background sender and flush remaining events."""
        self._running = False
        self._flush_batch()

        if self._cef_socket:
            self._cef_socket.close()
            self._cef_socket = None

        if self._worker_thread:
            self._worker_thread.join(timeout=5.0)

    def _connect_cef(self):
        """Connect to CEF/Syslog receiver."""
        try:
            if self.config.cef_protocol == "tcp":
                self._cef_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self._cef_socket.connect((self.config.cef_host, self.config.cef_port))
            else:
                self._cef_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            logger.info(f"Connected to CEF receiver at {self.config.cef_host}:{self.config.cef_port}")
        except Exception as e:
            logger.warning(f"Failed to connect to CEF receiver: {e}")
            self._cef_socket = None

    def _should_send(self, event: SecurityEvent) -> bool:
        """Check if event should be sent based on filters."""
        if event.severity < self.config.min_severity:
            return False
        if event.category not in self.config.enabled_categories:
            return False
        return True

    def report(self, event: SecurityEvent):
        """
        Report a security event to SIEM.

        In async mode, events are queued and sent in batches.
        In sync mode, events are sent immediately.
        """
        if not self.config.enabled:
            return

        if not self._should_send(event):
            return

        if self.config.async_mode:
            self._event_queue.put(event)
        else:
            self._send_event(event)

    def report_auth_event(
        self,
        action: str,
        success: bool,
        username: Optional[str] = None,
        ip_address: Optional[str] = None,
        reason: Optional[str] = None,
    ):
        """Report an authentication event."""
        event = SecurityEvent(
            action=f"auth.{action}",
            outcome="success" if success else "failure",
            severity=Severity.LOW if success else Severity.MEDIUM,
            category=EventCategory.AUTHENTICATION,
            actor_user=username,
            actor_ip=ip_address,
            message=reason,
            tags=["authentication"],
        )
        self.report(event)

    def report_access_event(
        self,
        resource: str,
        action: str,
        allowed: bool,
        username: Optional[str] = None,
        ip_address: Optional[str] = None,
        reason: Optional[str] = None,
    ):
        """Report an access/authorization event."""
        event = SecurityEvent(
            action=f"access.{action}",
            outcome="success" if allowed else "failure",
            severity=Severity.LOW if allowed else Severity.HIGH,
            category=EventCategory.AUTHORIZATION,
            actor_user=username,
            actor_ip=ip_address,
            target_resource=resource,
            message=reason,
            tags=["authorization", "access"],
        )
        self.report(event)

    def report_security_violation(
        self,
        violation_type: str,
        description: str,
        ip_address: Optional[str] = None,
        username: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ):
        """Report a security violation (injection, tampering, etc.)."""
        event = SecurityEvent(
            action=f"security.{violation_type}",
            outcome="failure",
            severity=Severity.HIGH,
            category=EventCategory.SECURITY,
            actor_user=username,
            actor_ip=ip_address,
            message=description,
            details=details or {},
            tags=["security", "violation", violation_type],
        )
        self.report(event)

    def report_error(
        self,
        error_type: str,
        error_message: str,
        error_code: Optional[str] = None,
        severity: int = Severity.MEDIUM,
        details: Optional[dict[str, Any]] = None,
    ):
        """Report a system or application error."""
        event = SecurityEvent(
            action=f"error.{error_type}",
            outcome="failure",
            severity=severity,
            category=EventCategory.SYSTEM,
            error_code=error_code,
            error_message=error_message,
            message=error_message,
            details=details or {},
            tags=["error", error_type],
        )
        self.report(event)

    def report_system_event(
        self,
        action: str,
        message: str,
        severity: int = Severity.LOW,
        details: Optional[dict[str, Any]] = None,
    ):
        """Report a system event (startup, shutdown, config change)."""
        event = SecurityEvent(
            action=f"system.{action}",
            outcome="success",
            severity=severity,
            category=EventCategory.SYSTEM,
            message=message,
            details=details or {},
            tags=["system", action],
        )
        self.report(event)

    def report_cognitive_event(
        self,
        action: str,
        outcome: str,
        details: Optional[dict[str, Any]] = None,
    ):
        """Report a cognitive/AI event (tool use, project action)."""
        event = SecurityEvent(
            action=f"cognitive.{action}",
            outcome=outcome,
            severity=Severity.LOW,
            category=EventCategory.COGNITIVE,
            details=details or {},
            tags=["cognitive", "ai", action],
        )
        self.report(event)

    def _worker_loop(self):
        """Background worker for batch sending."""
        last_flush = time.time()

        while self._running:
            try:
                # Get events from queue
                while not self._event_queue.empty():
                    event = self._event_queue.get_nowait()
                    with self._batch_lock:
                        self._batch.append(event)

                # Check if we should flush
                should_flush = False
                with self._batch_lock:
                    if len(self._batch) >= self.config.batch_size:
                        should_flush = True
                    elif len(self._batch) > 0 and (time.time() - last_flush) >= self.config.batch_timeout:
                        should_flush = True

                if should_flush:
                    self._flush_batch()
                    last_flush = time.time()

                time.sleep(0.1)

            except Exception as e:
                logger.error(f"SIEM worker error: {e}")
                time.sleep(1.0)

    def _flush_batch(self):
        """Send all batched events."""
        with self._batch_lock:
            if not self._batch:
                return

            events_to_send = self._batch.copy()
            self._batch.clear()

        # Send via HTTP API
        self._send_batch_http(events_to_send)

        # Send via CEF if enabled
        if self.config.cef_enabled and self._cef_socket:
            for event in events_to_send:
                self._send_cef(event)

    def _send_event(self, event: SecurityEvent):
        """Send a single event immediately."""
        self._send_batch_http([event])

        if self.config.cef_enabled and self._cef_socket:
            self._send_cef(event)

    def _send_batch_http(self, events: list[SecurityEvent]):
        """Send events via HTTP API."""
        if not events:
            return

        headers = {
            "Content-Type": "application/json",
        }
        if self.config.api_token:
            headers["Authorization"] = f"Bearer {self.config.api_token}"

        # Send each event (could be optimized for batch endpoint)
        for event in events:
            payload = event.to_json()

            for attempt in range(self.config.max_retries):
                try:
                    import urllib.error
                    import urllib.request

                    req = urllib.request.Request(
                        f"{self.config.api_url}/api/v1/events",
                        data=json.dumps(payload).encode(),
                        headers=headers,
                        method="POST",
                    )

                    with urllib.request.urlopen(req, timeout=self.config.api_timeout) as resp:
                        if resp.status in (200, 201, 202):
                            self._stats["events_sent"] += 1
                            break
                        else:
                            raise Exception(f"HTTP {resp.status}")

                except urllib.error.URLError as e:
                    delay = self.config.retry_delay * (self.config.retry_backoff ** attempt)
                    if attempt < self.config.max_retries - 1:
                        time.sleep(delay)
                    else:
                        self._stats["events_failed"] += 1
                        self._stats["last_error"] = str(e)
                        logger.debug(f"Failed to send event to SIEM: {e}")

                except Exception as e:
                    self._stats["events_failed"] += 1
                    self._stats["last_error"] = str(e)
                    break

        self._stats["batches_sent"] += 1
        self._stats["last_send_time"] = datetime.now(timezone.utc).isoformat()

    def _send_cef(self, event: SecurityEvent):
        """Send event via CEF/Syslog."""
        if not self._cef_socket:
            return

        try:
            cef_message = event.to_cef() + "\n"

            if self.config.cef_protocol == "tcp":
                self._cef_socket.sendall(cef_message.encode())
            else:
                self._cef_socket.sendto(
                    cef_message.encode(),
                    (self.config.cef_host, self.config.cef_port)
                )
        except Exception as e:
            logger.debug(f"Failed to send CEF event: {e}")
            # Try to reconnect
            self._connect_cef()

    def get_stats(self) -> dict[str, Any]:
        """Get client statistics."""
        return {
            **self._stats,
            "queue_size": self._event_queue.qsize(),
            "batch_size": len(self._batch),
            "enabled": self.config.enabled,
            "api_url": self.config.api_url,
        }


# Global SIEM client instance
_siem_client: Optional[BoundarySIEM] = None


def get_siem() -> Optional[BoundarySIEM]:
    """Get the global SIEM client instance."""
    return _siem_client


def init_siem(config: Optional[SIEMConfig] = None) -> BoundarySIEM:
    """Initialize and start the global SIEM client."""
    global _siem_client

    if _siem_client is not None:
        _siem_client.stop()

    _siem_client = BoundarySIEM(config)
    _siem_client.start()

    return _siem_client


def report_event(event: SecurityEvent):
    """Report an event using the global SIEM client."""
    if _siem_client:
        _siem_client.report(event)
