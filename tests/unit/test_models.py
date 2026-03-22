"""Tests for data models."""
from datetime import date, datetime
from decimal import Decimal

from pivotpoint.models.contracts import OptionsContract, GreeksSnapshot, PositionLeg, MultiLegPosition
from pivotpoint.models.market import MarketSnapshot, OptionsChain
from pivotpoint.models.signals import SignalPayload
from pivotpoint.utils.types import OptionType, Side, Underlying, Direction, TimeFrame, SignalType


def test_options_contract_creation():
    contract = OptionsContract(
        symbol="NIFTY23100CE",
        expiry=date(2026, 3, 31),
        strike=Decimal("23100"),
        option_type=OptionType.CE,
        premium=Decimal("150"),
        lot_size=65,
    )
    assert contract.symbol == "NIFTY23100CE"
    assert contract.option_type == OptionType.CE


def test_greeks_snapshot_defaults():
    g = GreeksSnapshot()
    assert g.delta == 0.0
    assert g.gamma == 0.0


def test_multi_leg_position_net_premium():
    buy_contract = OptionsContract(
        symbol="NIFTY23100CE", expiry=date(2026, 3, 31),
        strike=Decimal("23100"), option_type=OptionType.CE,
        premium=Decimal("100"), lot_size=65,
    )
    sell_contract = OptionsContract(
        symbol="NIFTY23300CE", expiry=date(2026, 3, 31),
        strike=Decimal("23300"), option_type=OptionType.CE,
        premium=Decimal("50"), lot_size=65,
    )
    position = MultiLegPosition(legs=[
        PositionLeg(contract=buy_contract, quantity=1, side=Side.BUY),
        PositionLeg(contract=sell_contract, quantity=1, side=Side.SELL),
    ])
    # Sell premium - Buy premium = 50*65 - 100*65 = -3250 (debit)
    assert position.net_premium == Decimal("-3250")
    assert not position.is_credit


def test_multi_leg_position_credit():
    sell_contract = OptionsContract(
        symbol="NIFTY23100CE", expiry=date(2026, 3, 31),
        strike=Decimal("23100"), option_type=OptionType.CE,
        premium=Decimal("200"), lot_size=65,
    )
    buy_contract = OptionsContract(
        symbol="NIFTY23300CE", expiry=date(2026, 3, 31),
        strike=Decimal("23300"), option_type=OptionType.CE,
        premium=Decimal("80"), lot_size=65,
    )
    position = MultiLegPosition(legs=[
        PositionLeg(contract=sell_contract, quantity=1, side=Side.SELL),
        PositionLeg(contract=buy_contract, quantity=2, side=Side.BUY),
    ])
    # Sell: 200*1*65 = 13000, Buy: 80*2*65 = 10400, Net = 2600 (credit)
    assert position.net_premium == Decimal("2600")
    assert position.is_credit


def test_signal_payload_creation(sample_signal):
    assert sample_signal.strategy_id == "TEST1"
    assert sample_signal.direction == Direction.BULLISH
    assert sample_signal.risk_reward_ratio == 3.0


def test_market_snapshot():
    snap = MarketSnapshot(
        underlying=Underlying.NIFTY, price=23100.0,
        timestamp=datetime(2026, 3, 22), vix_level=22.09,
    )
    assert snap.underlying == Underlying.NIFTY
    assert snap.vix_level == 22.09
