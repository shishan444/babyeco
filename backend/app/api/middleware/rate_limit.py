"""Rate limiting middleware for API endpoints.

This module provides rate limiting functionality to prevent abuse
of sensitive endpoints like login, registration, and device binding.
"""

import time
from collections import defaultdict
from dataclasses import dataclass
from typing import Callable, Literal

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse


@dataclass
class RateLimitRecord:
    """Record of rate limit attempts."""

    count: int
    window_start: float
    blocked_until: float | None = None


EndpointType = Literal["login", "register", "bind", "default"]


class InMemoryRateLimiter:
    """In-memory rate limiter using sliding window algorithm.

    @MX:NOTE
    Stores rate limit data in memory.
    For production, use Redis for distributed rate limiting.
    Data is automatically cleaned up after window expires.

    Limits:
    - Login: 5 attempts per 15 minutes per IP
    - Registration: 3 attempts per hour per IP
    - Device binding: 10 attempts per hour per device
    """

    def __init__(self) -> None:
        """Initialize rate limiter with default limits."""
        # Storage: {ip_or_key: {endpoint_name: RateLimitRecord}}
        self._limits: dict[str, dict[str, RateLimitRecord]] = defaultdict(
            lambda: defaultdict(lambda: RateLimitRecord(count=0, window_start=time.time()))
        )

        # Rate limit configurations
        self._configs: dict[str, dict[str, int]] = {
            "login": {"max_requests": 5, "window_seconds": 900},  # 15 minutes
            "register": {"max_requests": 3, "window_seconds": 3600},  # 1 hour
            "bind": {"max_requests": 10, "window_seconds": 3600},  # 1 hour
            "default": {"max_requests": 100, "window_seconds": 60},  # 1 minute
        }

    def _get_key(self, request: Request, endpoint_type: str) -> str:
        """Get the rate limit key for a request.

        @MX:NOTE
        Uses IP address for most endpoints.
        Uses device_id for device binding endpoints.
        """
        if endpoint_type == "bind":
            # For device binding, try to get device_id from request
            device_id = request.headers.get("X-Device-ID")
            if device_id:
                return f"device:{device_id}"

        # Default to IP address
        # Handle both real IP and proxy forwarding
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            ip = forwarded_for.split(",")[0].strip()
        else:
            ip = request.client.host if request.client else "unknown"
        return f"ip:{ip}"

    def _clean_old_records(self, key: str, endpoint_name: str) -> None:
        """Clean up expired rate limit records.

        @MX:NOTE
        Removes records that are outside their time window.
        Also removes blocked records if block time has expired.
        """
        if key not in self._limits:
            return

        record = self._limits[key][endpoint_name]
        config = self._configs.get(endpoint_name, self._configs["default"])
        now = time.time()

        # Reset if window expired
        if now - record.window_start > config["window_seconds"]:
            del self._limits[key][endpoint_name]

        # Clear block if expired
        if record.blocked_until and now > record.blocked_until:
            record.blocked_until = None
            record.count = 0

    def is_allowed(
        self, request: Request, endpoint_type: str = "default"
    ) -> tuple[bool, int | None]:
        """Check if a request is allowed under rate limits.

        Args:
            request: FastAPI request object
            endpoint_type: Type of endpoint for limit configuration

        Returns:
            Tuple of (is_allowed, retry_after_seconds)
            retry_after_seconds is None if allowed, or seconds until limit resets
        """
        key = self._get_key(request, endpoint_type)
        endpoint_name = endpoint_type

        # Clean old records
        self._clean_old_records(key, endpoint_name)

        if key not in self._limits:
            self._limits[key][endpoint_name] = RateLimitRecord(
                count=0, window_start=time.time()
            )

        record = self._limits[key][endpoint_name]
        config = self._configs.get(endpoint_type, self._configs["default"])
        now = time.time()

        # Check if currently blocked
        if record.blocked_until:
            if now < record.blocked_until:
                return False, int(record.blocked_until - now)
            else:
                # Block expired, reset
                record.blocked_until = None
                record.count = 0

        # Check if window expired
        if now - record.window_start > config["window_seconds"]:
            record.count = 0
            record.window_start = now

        # Check if limit exceeded
        if record.count >= config["max_requests"]:
            # Block for the remainder of the window
            record.blocked_until = record.window_start + config["window_seconds"]
            return False, int(record.blocked_until - now)

        # Increment counter
        record.count += 1
        return True, None

    def reset(self, key: str | None = None) -> None:
        """Reset rate limit for a specific key or all keys.

        @MX:NOTE
        Used for testing or manual intervention.
        If key is None, clears all rate limit data.
        """
        if key is None:
            self._limits.clear()
        elif key in self._limits:
            self._limits[key].clear()


# Global rate limiter instance
_rate_limiter = InMemoryRateLimiter()


def check_rate_limit(endpoint_type: EndpointType = "default"):
    """FastAPI dependency for rate limiting.

    @MX:NOTE
    Applies rate limiting based on endpoint_type configuration.
    Returns 429 Too Many Requests with retry-after header when limited.

    Usage:
        @app.post("/login")
        async def login(
            ...,
            _rate_limit: None = Depends(check_rate_limit("login"))
        ): ...
    """

    async def _check(request: Request) -> None:
        """Check rate limit and raise exception if exceeded."""
        allowed, retry_after = _rate_limiter.is_allowed(request, endpoint_type)

        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please try again later.",
                headers={
                    "Retry-After": str(retry_after) if retry_after else "3600"
                },
            )

    return _check


def get_rate_limit_status(request: Request, endpoint_type: str = "default") -> dict:
    """Get current rate limit status for a request.

    Returns a dict with current usage information.
    """
    key = _rate_limiter._get_key(request, endpoint_type)
    endpoint_name = endpoint_type

    if key not in _rate_limiter._limits:
        return {"limit": 0, "remaining": 0, "reset": 0}

    record = _rate_limiter._limits[key][endpoint_name]
    config = _rate_limiter._configs.get(endpoint_type, _rate_limiter._configs["default"])

    return {
        "limit": config["max_requests"],
        "remaining": max(0, config["max_requests"] - record.count),
        "reset": int(record.window_start + config["window_seconds"]),
    }
