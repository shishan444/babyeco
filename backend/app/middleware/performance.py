"""Performance monitoring middleware for tracking request latency."""

import time
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class PerformanceMiddleware(BaseHTTPMiddleware):
    """Middleware to track request latency and log slow requests.

    @MX:ANCHOR: Request performance tracking
    @MX:REASON: Fan-in >= 3 (applied to all routes)

    Tracks latency for all HTTP requests and logs requests that exceed
    the slow_request_threshold (default: 1 second). This helps identify
    performance bottlenecks in the application.
    """

    def __init__(
        self,
        app: ASGIApp,
        slow_request_threshold: float = 1.0,
    ) -> None:
        """Initialize performance middleware.

        Args:
            app: ASGI application
            slow_request_threshold: Threshold in seconds for logging slow requests
        """
        super().__init__(app)
        self.slow_request_threshold = slow_request_threshold

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and track latency.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware or route handler

        Returns:
            HTTP response with performance headers added
        """
        start_time = time.time()

        # Process request
        response = await call_next(request)

        # Calculate latency
        process_time = time.time() - start_time

        # Add performance header to response
        response.headers["X-Process-Time"] = str(process_time)

        # Log slow requests
        if process_time > self.slow_request_threshold:
            logger.warning(
                "Slow request detected",
                extra={
                    "method": request.method,
                    "url": str(request.url),
                    "status": response.status_code,
                    "process_time": f"{process_time:.3f}s",
                    "threshold": f"{self.slow_request_threshold}s",
                },
            )

        # Log all requests in development
        if process_time > 0.1:  # Only log requests taking more than 100ms
            logger.info(
                "Request processed",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status": response.status_code,
                    "process_time": f"{process_time:.3f}s",
                },
            )

        return response
