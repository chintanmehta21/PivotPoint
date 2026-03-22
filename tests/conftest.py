"""Shared test fixtures."""
import pytest
from datetime import date, datetime
from decimal import Decimal

from quant.models.contracts import OptionsContract, GreeksSnapshot, PositionLeg, MultiLegPosition
from quant.models.market import MarketSnapshot, OptionsChain
from quant.models.signals import SignalPayload
from quant.utils.types import Direction, TimeFrame, SignalType, Side, OptionType, Underlying


@pytest.fixture
def sample_contract() -> OptionsContract:
    return OptionsContract(
        symbol="NIFTY23MAR23100CE",
        expiry=date(2026, 3, 31),
        strike=Decimal("23100"),
        option_type=OptionType.CE,
        premium=Decimal("150"),
        lot_size=65,
    )


@pytest.fixture
def sample_greeks() -> GreeksSnapshot:
    return GreeksSnapshot(delta=0.5, gamma=0.02, vega=1.5, theta=-0.8, iv=22.0)


@pytest.fixture
def sample_position(sample_contract: OptionsContract) -> MultiLegPosition:
    return MultiLegPosition(
        legs=[
            PositionLeg(contract=sample_contract, quantity=1, side=Side.BUY),
        ]
    )


@pytest.fixture
def sample_market() -> MarketSnapshot:
    return MarketSnapshot(
        underlying=Underlying.NIFTY,
        price=23100.0,
        timestamp=datetime(2026, 3, 22, 10, 0, 0),
        vix_level=22.09,
    )


@pytest.fixture
def sample_chain(sample_contract: OptionsContract) -> OptionsChain:
    return OptionsChain(
        underlying=Underlying.NIFTY,
        expiry=date(2026, 3, 31),
        contracts=[sample_contract],
    )


@pytest.fixture
def sample_signal(sample_position: MultiLegPosition, sample_greeks: GreeksSnapshot) -> SignalPayload:
    return SignalPayload(
        timestamp=datetime(2026, 3, 22, 10, 0, 0),
        strategy_name="Test Strategy",
        strategy_id="TEST1",
        underlying=Underlying.NIFTY,
        timeframe=TimeFrame.WEEKLY,
        direction=Direction.BULLISH,
        position=sample_position,
        max_profit=Decimal("15000"),
        max_loss=Decimal("5000"),
        risk_reward_ratio=3.0,
        confidence_score=75.0,
        greeks=sample_greeks,
        signal_type=SignalType.ENTRY,
        notes="Test signal",
    )
