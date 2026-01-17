"""
Rate Limiter for Synth Mind Dashboard API.

Implements a sliding window rate limiter with configurable limits per endpoint type.
Supports IP-based and token-based rate limiting.
"""

import asyncio
import time
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class RateLimitTier(Enum):
    """Rate limit tiers for different endpoint types."""
    STRICT = "strict"       # Auth endpoints (login, setup)
    STANDARD = "standard"   # Normal API endpoints
    RELAXED = "relaxed"     # Read-only endpoints
    WEBSOCKET = "websocket" # WebSocket connections


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""
    # Requests per window for each tier
    strict_limit: int = 5           # 5 requests per window (auth endpoints)
    standard_limit: int = 60        # 60 requests per window (normal API)
    relaxed_limit: int = 120        # 120 requests per window (read-only)
    websocket_limit: int = 10       # 10 new connections per window

    # Window size in seconds
    window_seconds: int = 60

    # Cleanup interval for expired entries
    cleanup_interval: int = 300     # 5 minutes

    # Enable/disable rate limiting
    enabled: bool = True

    # Whitelist IPs (never rate limited)
    whitelist: list[str] = field(default_factory=lambda: ["127.0.0.1", "::1"])

    # Block duration after exceeding limit (seconds)
    block_duration: int = 60


@dataclass
class RequestRecord:
    """Record of requests from a client."""
    timestamps: list[float] = field(default_factory=list)
    blocked_until: float = 0.0


class RateLimiter:
    """
    Sliding window rate limiter.

    Tracks request counts per client (IP or token) within a sliding time window.
    Different limits apply to different endpoint tiers.
    """

    # Endpoint to tier mapping
    ENDPOINT_TIERS: dict[str, RateLimitTier] = {
        # Strict tier - authentication endpoints
        "/api/auth/login": RateLimitTier.STRICT,
        "/api/auth/setup": RateLimitTier.STRICT,
        "/api/auth/refresh": RateLimitTier.STRICT,

        # Relaxed tier - read-only endpoints
        "/": RateLimitTier.RELAXED,
        "/timeline": RateLimitTier.RELAXED,
        "/api/state": RateLimitTier.RELAXED,
        "/api/auth/status": RateLimitTier.RELAXED,
        "/api/timeline": RateLimitTier.RELAXED,
        "/api/federated/stats": RateLimitTier.RELAXED,
        "/api/collab/stats": RateLimitTier.RELAXED,

        # WebSocket tier
        "/ws": RateLimitTier.WEBSOCKET,
    }

    def __init__(self, config: RateLimitConfig = None):
        """
        Initialize rate limiter.

        Args:
            config: Rate limit configuration
        """
        self.config = config or RateLimitConfig()

        # Track requests per client per tier
        # Structure: {tier: {client_id: RequestRecord}}
        self._requests: dict[RateLimitTier, dict[str, RequestRecord]] = defaultdict(
            lambda: defaultdict(RequestRecord)
        )

        # Lock for thread-safe access
        self._lock = asyncio.Lock()

        # Last cleanup time
        self._last_cleanup = time.time()

    def get_tier_for_endpoint(self, path: str) -> RateLimitTier:
        """Get the rate limit tier for an endpoint."""
        # Exact match first
        if path in self.ENDPOINT_TIERS:
            return self.ENDPOINT_TIERS[path]

        # Check prefix matches for dynamic routes
        for endpoint, tier in self.ENDPOINT_TIERS.items():
            if path.startswith(endpoint):
                return tier

        # Default to standard tier
        return RateLimitTier.STANDARD

    def get_limit_for_tier(self, tier: RateLimitTier) -> int:
        """Get the request limit for a tier."""
        limits = {
            RateLimitTier.STRICT: self.config.strict_limit,
            RateLimitTier.STANDARD: self.config.standard_limit,
            RateLimitTier.RELAXED: self.config.relaxed_limit,
            RateLimitTier.WEBSOCKET: self.config.websocket_limit,
        }
        return limits.get(tier, self.config.standard_limit)

    def _get_client_id(self, ip: str, token: Optional[str] = None) -> str:
        """
        Get client identifier.

        Uses token if available (for authenticated requests),
        otherwise falls back to IP address.
        """
        if token:
            # Use first 16 chars of token as identifier
            return f"token:{token[:16]}"
        return f"ip:{ip}"

    def _cleanup_expired(self, tier: RateLimitTier):
        """Remove expired request records."""
        now = time.time()
        cutoff = now - self.config.window_seconds

        tier_requests = self._requests[tier]
        expired_clients = []

        for client_id, record in tier_requests.items():
            # Remove old timestamps
            record.timestamps = [ts for ts in record.timestamps if ts > cutoff]

            # Mark for removal if no recent requests and not blocked
            if not record.timestamps and record.blocked_until < now:
                expired_clients.append(client_id)

        # Remove expired clients
        for client_id in expired_clients:
            del tier_requests[client_id]

    async def check_rate_limit(
        self,
        ip: str,
        path: str,
        token: Optional[str] = None
    ) -> tuple[bool, dict]:
        """
        Check if request is allowed under rate limit.

        Args:
            ip: Client IP address
            path: Request path
            token: Optional auth token

        Returns:
            Tuple of (allowed, info_dict)
            info_dict contains: remaining, limit, reset_time, retry_after (if blocked)
        """
        if not self.config.enabled:
            return True, {"remaining": -1, "limit": -1, "reset_time": 0}

        # Check whitelist
        if ip in self.config.whitelist:
            return True, {"remaining": -1, "limit": -1, "reset_time": 0, "whitelisted": True}

        tier = self.get_tier_for_endpoint(path)
        limit = self.get_limit_for_tier(tier)
        client_id = self._get_client_id(ip, token)
        now = time.time()
        window_start = now - self.config.window_seconds

        async with self._lock:
            # Periodic cleanup
            if now - self._last_cleanup > self.config.cleanup_interval:
                for t in RateLimitTier:
                    self._cleanup_expired(t)
                self._last_cleanup = now

            record = self._requests[tier][client_id]

            # Check if client is blocked
            if record.blocked_until > now:
                retry_after = int(record.blocked_until - now)
                return False, {
                    "remaining": 0,
                    "limit": limit,
                    "reset_time": int(record.blocked_until),
                    "retry_after": retry_after,
                    "blocked": True
                }

            # Filter to current window
            record.timestamps = [ts for ts in record.timestamps if ts > window_start]
            current_count = len(record.timestamps)

            # Check if limit exceeded
            if current_count >= limit:
                # Block the client
                record.blocked_until = now + self.config.block_duration
                return False, {
                    "remaining": 0,
                    "limit": limit,
                    "reset_time": int(record.blocked_until),
                    "retry_after": self.config.block_duration,
                    "blocked": True
                }

            # Add current request
            record.timestamps.append(now)
            remaining = limit - current_count - 1

            # Calculate reset time (when oldest request expires)
            if record.timestamps:
                reset_time = int(record.timestamps[0] + self.config.window_seconds)
            else:
                reset_time = int(now + self.config.window_seconds)

            return True, {
                "remaining": remaining,
                "limit": limit,
                "reset_time": reset_time,
                "tier": tier.value
            }

    async def record_request(
        self,
        ip: str,
        path: str,
        token: Optional[str] = None
    ):
        """
        Record a request (use when check_rate_limit wasn't called first).

        This is useful for recording requests after they complete.
        """
        if not self.config.enabled:
            return

        if ip in self.config.whitelist:
            return

        tier = self.get_tier_for_endpoint(path)
        client_id = self._get_client_id(ip, token)
        now = time.time()

        async with self._lock:
            self._requests[tier][client_id].timestamps.append(now)

    def get_stats(self) -> dict:
        """Get rate limiter statistics."""
        stats = {
            "enabled": self.config.enabled,
            "window_seconds": self.config.window_seconds,
            "tiers": {}
        }

        for tier in RateLimitTier:
            tier_requests = self._requests[tier]
            active_clients = sum(1 for r in tier_requests.values() if r.timestamps)
            blocked_clients = sum(
                1 for r in tier_requests.values()
                if r.blocked_until > time.time()
            )
            stats["tiers"][tier.value] = {
                "limit": self.get_limit_for_tier(tier),
                "active_clients": active_clients,
                "blocked_clients": blocked_clients
            }

        return stats

    def reset_client(self, ip: str, token: Optional[str] = None):
        """Reset rate limit for a specific client."""
        client_id = self._get_client_id(ip, token)
        for tier in RateLimitTier:
            if client_id in self._requests[tier]:
                del self._requests[tier][client_id]

    def reset_all(self):
        """Reset all rate limits."""
        self._requests.clear()


def create_rate_limit_middleware(rate_limiter: RateLimiter):
    """
    Create an aiohttp middleware for rate limiting.

    Args:
        rate_limiter: RateLimiter instance

    Returns:
        aiohttp middleware function
    """
    from aiohttp import web

    @web.middleware
    async def rate_limit_middleware(request, handler):
        # Get client IP (support for proxies)
        ip = request.headers.get(
            'X-Forwarded-For',
            request.headers.get('X-Real-IP', request.remote)
        )
        # Take first IP if multiple (X-Forwarded-For can be comma-separated)
        if ip and ',' in ip:
            ip = ip.split(',')[0].strip()

        # Get token if present
        auth_header = request.headers.get('Authorization', '')
        token = auth_header[7:] if auth_header.startswith('Bearer ') else None

        # Check rate limit
        allowed, info = await rate_limiter.check_rate_limit(
            ip=ip,
            path=request.path,
            token=token
        )

        if not allowed:
            # Return 429 Too Many Requests
            return web.json_response(
                {
                    "error": "Rate limit exceeded",
                    "retry_after": info.get("retry_after", 60),
                    "limit": info.get("limit"),
                    "message": f"Too many requests. Please wait {info.get('retry_after', 60)} seconds."
                },
                status=429,
                headers={
                    "Retry-After": str(info.get("retry_after", 60)),
                    "X-RateLimit-Limit": str(info.get("limit", 0)),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(info.get("reset_time", 0))
                }
            )

        # Process request
        response = await handler(request)

        # Add rate limit headers to response
        if hasattr(response, 'headers'):
            response.headers["X-RateLimit-Limit"] = str(info.get("limit", -1))
            response.headers["X-RateLimit-Remaining"] = str(info.get("remaining", -1))
            response.headers["X-RateLimit-Reset"] = str(info.get("reset_time", 0))

        return response

    return rate_limit_middleware
