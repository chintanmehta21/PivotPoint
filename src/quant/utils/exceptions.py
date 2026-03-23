"""Custom exception hierarchy for the trading system."""
from datetime import date
from decimal import Decimal

class PivotPointError(Exception):
    """Base exception for all system errors."""
    pass

class ContractExpiredError(PivotPointError):
    def __init__(self, symbol: str, expiry: date) -> None:
        self.symbol = symbol
        self.expiry = expiry
        super().__init__(f"Contract expired: {symbol} @ {expiry}")

class MissingGreeksError(PivotPointError):
    def __init__(self, symbol: str) -> None:
        self.symbol = symbol
        super().__init__(f"Greeks data unavailable for: {symbol}")

class IlliquidStrikeError(PivotPointError):
    def __init__(self, symbol: str, strike: Decimal) -> None:
        self.symbol = symbol
        self.strike = strike
        super().__init__(f"Illiquid strike: {symbol} @ {strike}")

class MarketClosedError(PivotPointError):
    def __init__(self, market: str = "NSE") -> None:
        self.market = market
        super().__init__(f"Market closed: {market}")

class InsufficientDataError(PivotPointError):
    def __init__(self, data_type: str, detail: str = "") -> None:
        self.data_type = data_type
        self.detail = detail
        super().__init__(f"Insufficient {data_type} data: {detail}")

class ConfigurationError(PivotPointError):
    def __init__(self, field: str, reason: str = "") -> None:
        self.field = field
        self.reason = reason
        super().__init__(f"Configuration error for '{field}': {reason}")

class SignalValidationError(PivotPointError):
    def __init__(self, strategy_id: str, reason: str) -> None:
        self.strategy_id = strategy_id
        self.reason = reason
        super().__init__(f"Signal validation failed for {strategy_id}: {reason}")

class StrategyEvaluationError(PivotPointError):
    def __init__(self, strategy_id: str, reason: str) -> None:
        self.strategy_id = strategy_id
        self.reason = reason
        super().__init__(f"Strategy evaluation failed for {strategy_id}: {reason}")


# Fyers exceptions (re-exported for convenience via lazy import to avoid circular deps)
_FYERS_EXCEPTION_NAMES = (
    "FyersError", "FyersAuthError", "FyersRateLimitError",
    "FyersAPIError", "FyersWebSocketError", "FyersDataError",
)


def __getattr__(name: str):  # noqa: N807
    if name in _FYERS_EXCEPTION_NAMES:
        import importlib
        mod = importlib.import_module("quant.data.fyers.exceptions")
        return getattr(mod, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
