"""Options contract and position data models."""
from datetime import date
from decimal import Decimal
from pydantic import BaseModel, Field
from quant.utils.types import OptionType, Side

class OptionsContract(BaseModel):
    """A single options contract."""
    symbol: str
    expiry: date
    strike: Decimal
    option_type: OptionType
    premium: Decimal = Decimal("0")
    lot_size: int = 1

class GreeksSnapshot(BaseModel):
    """Greeks values at a point in time."""
    delta: float = 0.0
    gamma: float = 0.0
    vega: float = 0.0
    theta: float = 0.0
    iv: float = 0.0

class PositionLeg(BaseModel):
    """A single leg in a multi-leg position."""
    contract: OptionsContract
    quantity: int
    side: Side

class MultiLegPosition(BaseModel):
    """A multi-leg options position with computed properties."""
    legs: list[PositionLeg] = Field(default_factory=list)

    @property
    def net_premium(self) -> Decimal:
        """Calculate net premium (positive = credit, negative = debit)."""
        total = Decimal("0")
        for leg in self.legs:
            multiplier = 1 if leg.side == Side.SELL else -1
            total += leg.contract.premium * leg.quantity * multiplier * leg.contract.lot_size
        return total

    @property
    def is_credit(self) -> bool:
        return self.net_premium > 0

    @property
    def total_lots(self) -> int:
        return sum(leg.quantity for leg in self.legs)
