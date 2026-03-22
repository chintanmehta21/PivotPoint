"""Fixed fractional position sizing."""
from decimal import Decimal

import structlog

logger = structlog.get_logger()

# Lot sizes for Indian market indices
LOT_SIZES: dict[str, int] = {
    "NIFTY": 65,
    "BANKNIFTY": 30,
}


class PositionSizer:
    """Calculate position size based on fixed fractional method."""

    def __init__(self, risk_per_trade_pct: float = 2.0) -> None:
        self.risk_per_trade_pct = risk_per_trade_pct

    def calculate_lots(
        self,
        capital: Decimal,
        max_loss_per_lot: Decimal,
        underlying: str = "NIFTY",
    ) -> int:
        """Calculate number of lots based on risk budget.

        Args:
            capital: Total trading capital.
            max_loss_per_lot: Maximum loss per single lot for the strategy.
            underlying: Index name for lot size lookup.

        Returns:
            Number of lots (minimum 1, capped by risk).
        """
        if max_loss_per_lot <= 0:
            return 1

        risk_budget = capital * Decimal(str(self.risk_per_trade_pct)) / Decimal("100")
        lots = int(risk_budget / max_loss_per_lot)
        lot_size = LOT_SIZES.get(underlying, 1)

        result = max(1, lots)
        logger.debug(
            "Position sized",
            capital=str(capital),
            risk_budget=str(risk_budget),
            lots=result,
            lot_size=lot_size,
        )
        return result
