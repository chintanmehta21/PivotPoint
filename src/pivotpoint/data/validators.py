"""Business logic validation for market data."""
from datetime import date
from decimal import Decimal
from pivotpoint.models.contracts import OptionsContract
from pivotpoint.utils.exceptions import ContractExpiredError, IlliquidStrikeError

def validate_contract_not_expired(contract: OptionsContract) -> None:
    """Raise ContractExpiredError if contract has expired."""
    if contract.expiry < date.today():
        raise ContractExpiredError(contract.symbol, contract.expiry)

def validate_strike_reasonable(contract: OptionsContract, spot_price: float, max_deviation: float = 0.3) -> None:
    """Raise IlliquidStrikeError if strike is too far from spot."""
    deviation = abs(float(contract.strike) - spot_price) / spot_price
    if deviation > max_deviation:
        raise IlliquidStrikeError(contract.symbol, contract.strike)
