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


from quant.models.daily_report import (
    DailyReport,
    MarketMacros,
    ReportStatus,
    ReportType,
    VirtualPortfolio,
    PortfolioTier,
)


@pytest.fixture
def sample_market_macros() -> MarketMacros:
    return MarketMacros(
        nifty_price=Decimal("22450.30"),
        nifty_change_pct=1.2,
        banknifty_price=Decimal("48120.50"),
        banknifty_change_pct=-0.4,
        india_vix=14.8,
        vix_change=-0.6,
        nifty_pcr_oi=1.12,
        nifty_max_pain=Decimal("22500"),
        banknifty_max_pain=Decimal("48000"),
        nifty_iv_percentile=42.0,
        banknifty_iv_percentile=38.0,
        fii_net_cash=Decimal("-1240"),
        dii_net_cash=Decimal("890"),
    )


@pytest.fixture
def sample_virtual_portfolio() -> VirtualPortfolio:
    return VirtualPortfolio(
        tier=PortfolioTier.CONSERVATIVE,
        threshold=85,
        active_positions=3,
        total_trades=28,
        realized_pnl=Decimal("42300"),
        unrealized_pnl=Decimal("8100"),
        total_pnl=Decimal("50400"),
        win_rate=0.68,
        best_strategy="BQ1",
        worst_strategy="BrM2",
    )


@pytest.fixture
def sample_daily_report(sample_market_macros) -> DailyReport:
    return DailyReport(
        report_type=ReportType.EVENING,
        report_status=ReportStatus.SUCCESS,
        date=date(2026, 3, 24),
        timestamp=datetime(2026, 3, 24, 16, 0, 0),
        market_macros=sample_market_macros,
    )
