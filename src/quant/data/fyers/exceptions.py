"""Fyers-specific exception hierarchy."""
from quant.utils.exceptions import PivotPointError


class FyersError(PivotPointError):
    """Base exception for all Fyers-related errors."""
    pass


class FyersAuthError(FyersError):
    """Raised when a Fyers authentication step fails."""

    def __init__(self, step: int, reason: str) -> None:
        self.step = step
        self.reason = reason
        super().__init__(f"Step {step} failed: {reason}")


class FyersRateLimitError(FyersError):
    """Raised when a Fyers API rate limit is exceeded."""

    def __init__(self, limit_type: str, limit: int) -> None:
        self.limit_type = limit_type
        self.limit = limit
        super().__init__(f"Rate limit exceeded: {limit_type} (limit={limit})")


class FyersAPIError(FyersError):
    """Raised on non-2xx responses from the Fyers REST API."""

    def __init__(self, status_code: int, endpoint: str, message: str = "") -> None:
        self.status_code = status_code
        self.endpoint = endpoint
        super().__init__(f"API error {status_code} on {endpoint}: {message}")


class FyersWebSocketError(FyersError):
    """Raised on Fyers WebSocket connection or message errors."""
    pass


class FyersDataError(FyersError):
    """Raised when Fyers returns malformed or unexpected data."""
    pass
