"""Market data models."""
from datetime import date, datetime
from pydantic import BaseModel
from pivotpoint.utils.types import Underlying
from pivotpoint.models.contracts import OptionsContract

class MarketSnapshot(BaseModel):
    """Current market state for an underlying."""
    underlying: Underlying
    price: float
    timestamp: datetime
    vix_level: float = 0.0

class OptionsChain(BaseModel):
    """Options chain for a specific underlying and expiry."""
    underlying: Underlying
    expiry: date
    contracts: list[OptionsContract]
