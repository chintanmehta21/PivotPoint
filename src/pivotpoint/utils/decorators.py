"""Shared decorators for timing and error handling."""
import functools
import time
from typing import Any, Callable
import structlog

logger = structlog.get_logger()

def timed(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator to log function execution time."""
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            elapsed_ms = (time.perf_counter() - start) * 1000
            logger.debug("Function completed", function=func.__name__, duration_ms=round(elapsed_ms, 2))
            return result
        except Exception:
            elapsed_ms = (time.perf_counter() - start) * 1000
            logger.error("Function failed", function=func.__name__, duration_ms=round(elapsed_ms, 2))
            raise
    return wrapper
