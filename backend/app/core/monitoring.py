"""Performance metrics collection and monitoring utilities.

@MX:NOTE: Performance monitoring infrastructure
"""

import contextvars
import logging
import time
from typing import Any, Callable
from functools import wraps

# Context variables for request tracking
request_start_time: contextvars.ContextVar[float] = contextvars.ContextVar(
    "request_start_time", default=0.0
)
request_id: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="")

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Collect and aggregate performance metrics.

    @MX:NOTE: Simple in-memory metrics collector
    For production, use Prometheus or similar metrics system.
    """

    def __init__(self) -> None:
        """Initialize metrics collector."""
        self.request_count: dict[str, int] = {}
        self.request_latency: dict[str, list[float]] = {}
        self.slow_requests: list[dict[str, Any]] = []
        self.max_slow_requests = 1000

    def record_request(
        self,
        method: str,
        path: str,
        status_code: int,
        latency: float,
    ) -> None:
        """Record request metrics.

        Args:
            method: HTTP method
            path: Request path
            status_code: HTTP status code
            latency: Request latency in seconds
        """
        key = f"{method} {path}"

        # Count requests
        self.request_count[key] = self.request_count.get(key, 0) + 1

        # Track latency
        if key not in self.request_latency:
            self.request_latency[key] = []
        self.request_latency[key].append(latency)

        # Keep only last 100 latency measurements per endpoint
        if len(self.request_latency[key]) > 100:
            self.request_latency[key] = self.request_latency[key][-100:]

        # Track slow requests (>1s)
        if latency > 1.0:
            slow_request = {
                "method": method,
                "path": path,
                "status_code": status_code,
                "latency": latency,
                "timestamp": time.time(),
            }
            self.slow_requests.append(slow_request)

            # Keep only recent slow requests
            if len(self.slow_requests) > self.max_slow_requests:
                self.slow_requests = self.slow_requests[-self.max_slow_requests :]

    def get_metrics(self) -> dict[str, Any]:
        """Get aggregated metrics.

        Returns:
            Dictionary with aggregated metrics
        """
        metrics = {
            "request_count": self.request_count.copy(),
            "avg_latency": {},
            "p95_latency": {},
            "p99_latency": {},
            "slow_request_count": len(self.slow_requests),
        }

        # Calculate latency percentiles
        for key, latencies in self.request_latency.items():
            if latencies:
                sorted_latencies = sorted(latencies)
                metrics["avg_latency"][key] = sum(latencies) / len(latencies)
                metrics["p95_latency"][key] = sorted_latencies[
                    int(len(sorted_latencies) * 0.95)
                ]
                metrics["p99_latency"][key] = sorted_latencies[
                    int(len(sorted_latencies) * 0.99)
                ]

        return metrics

    def reset(self) -> None:
        """Reset all metrics."""
        self.request_count.clear()
        self.request_latency.clear()
        self.slow_requests.clear()


# Global metrics collector instance
metrics = MetricsCollector()


def track_performance(func_name: str | None = None) -> Callable:
    """Decorator to track function performance.

    @MX:ANCHOR: Performance tracking decorator
    @MX:REASON: High fan-in utility for monitoring critical functions

    Args:
        func_name: Custom function name for metrics (defaults to actual function name)

    Returns:
        Decorated function with performance tracking

    Example:
        @code-block:: python

        @track_performance()
        async def expensive_operation(data: dict) -> Result:
            return await process(data)
    """

    def decorator(func: Callable) -> Callable:
        name = func_name or func.__name__

        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            start = time.time()
            try:
                result = await func(*args, **kwargs)
                latency = time.time() - start

                # Log performance
                logger.info(
                    f"Function {name} executed",
                    extra={
                        "function": name,
                        "latency": f"{latency:.3f}s",
                        "status": "success",
                    },
                )

                # Track slow functions (>100ms)
                if latency > 0.1:
                    logger.warning(
                        f"Slow function detected: {name}",
                        extra={
                            "function": name,
                            "latency": f"{latency:.3f}s",
                        },
                    )

                return result

            except Exception as e:
                latency = time.time() - start
                logger.error(
                    f"Function {name} failed",
                    extra={
                        "function": name,
                        "latency": f"{latency:.3f}s",
                        "status": "error",
                        "error": str(e),
                    },
                )
                raise

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            start = time.time()
            try:
                result = func(*args, **kwargs)
                latency = time.time() - start

                logger.info(
                    f"Function {name} executed",
                    extra={
                        "function": name,
                        "latency": f"{latency:.3f}s",
                        "status": "success",
                    },
                )

                if latency > 0.1:
                    logger.warning(
                        f"Slow function detected: {name}",
                        extra={
                            "function": name,
                            "latency": f"{latency:.3f}s",
                        },
                    )

                return result

            except Exception as e:
                latency = time.time() - start
                logger.error(
                    f"Function {name} failed",
                    extra={
                        "function": name,
                        "latency": f"{latency:.3f}s",
                        "status": "error",
                        "error": str(e),
                    },
                )
                raise

        # Return appropriate wrapper based on function type
        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def log_slow_query(
    threshold: float = 0.5,
) -> Callable:
    """Decorator to log slow database queries.

    @MX:NOTE: Database query performance monitoring

    Args:
        threshold: Threshold in seconds for logging slow queries

    Returns:
        Decorated function with slow query logging

    Example:
        @code-block:: python

        @log_slow_query(threshold=1.0)
        async def get_user_tasks(user_id: str) -> list[Task]:
            return await db.query(Task).filter(Task.user_id == user_id).all()
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            start = time.time()
            result = await func(*args, **kwargs)
            latency = time.time() - start

            if latency > threshold:
                logger.warning(
                    "Slow database query detected",
                    extra={
                        "function": func.__name__,
                        "latency": f"{latency:.3f}s",
                        "threshold": f"{threshold}s",
                    },
                )

            return result

        return wrapper

    return decorator


class RequestTimer:
    """Context manager for timing request processing.

    @MX:NOTE: Request timing utility

    Example:
        @code-block:: python

        async with RequestTimer(request) as timer:
            result = await process_request(request)
    """

    def __init__(self, request: Any) -> None:
        """Initialize request timer.

        Args:
            request: FastAPI request object
        """
        self.request = request
        self.start_time: float = 0.0
        self.end_time: float = 0.0

    def __enter__(self) -> "RequestTimer":
        """Start timing."""
        self.start_time = time.time()
        request_start_time.set(self.start_time)
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Stop timing and record metrics."""
        self.end_time = time.time()
        latency = self.end_time - self.start_time

        # Record metrics
        metrics.record_request(
            method=self.request.method,
            path=self.request.url.path,
            status_code=getattr(self.request.state, "status_code", 200),
            latency=latency,
        )

    @property
    def elapsed(self) -> float:
        """Get elapsed time in seconds."""
        return time.time() - self.start_time
