"""Tests for virtual portfolio tracker."""
from datetime import date
from decimal import Decimal

import pytest

from quant.models.daily_report import PortfolioTier, VirtualPortfolio
from quant.report.portfolio_tracker import PortfolioTracker
from quant.utils.types import Direction


class TestPortfolioTracker:
    def test_three_tiers_returned(self):
        tracker = PortfolioTracker()
        portfolios = tracker.get_snapshots()
        assert len(portfolios) == 3
        tiers = {p.tier for p in portfolios}
        assert tiers == {PortfolioTier.CONSERVATIVE, PortfolioTier.MODERATE, PortfolioTier.AGGRESSIVE}

    def test_thresholds_match(self):
        tracker = PortfolioTracker()
        for p in tracker.get_snapshots():
            if p.tier == PortfolioTier.CONSERVATIVE:
                assert p.threshold == 85
            elif p.tier == PortfolioTier.MODERATE:
                assert p.threshold == 75
            elif p.tier == PortfolioTier.AGGRESSIVE:
                assert p.threshold == 0

    def test_initial_state_is_empty(self):
        tracker = PortfolioTracker()
        for p in tracker.get_snapshots():
            assert p.active_positions == 0
            assert p.total_trades == 0
            assert p.total_pnl == Decimal("0")

    def test_open_trade_above_threshold(self):
        tracker = PortfolioTracker()
        tracker.process_entry("BQ1", Direction.BULLISH, 90.0, Decimal("150.00"), date(2026, 3, 24))
        for p in tracker.get_snapshots():
            assert p.active_positions == 1
            assert p.total_trades == 1

    def test_open_trade_below_conservative_threshold(self):
        tracker = PortfolioTracker()
        tracker.process_entry("BW1", Direction.BULLISH, 80.0, Decimal("100.00"), date(2026, 3, 24))
        snapshots = {p.tier: p for p in tracker.get_snapshots()}
        assert snapshots[PortfolioTier.CONSERVATIVE].active_positions == 0
        assert snapshots[PortfolioTier.MODERATE].active_positions == 1
        assert snapshots[PortfolioTier.AGGRESSIVE].active_positions == 1

    def test_close_trade_realizes_pnl(self):
        tracker = PortfolioTracker()
        tracker.process_entry("BQ1", Direction.BULLISH, 90.0, Decimal("100.00"), date(2026, 3, 24))
        tracker.process_exit("BQ1", Decimal("130.00"), date(2026, 3, 25))
        for p in tracker.get_snapshots():
            assert p.active_positions == 0
            assert p.realized_pnl == Decimal("30.00")
            assert p.win_rate == 1.0

    def test_win_rate_calculation(self):
        tracker = PortfolioTracker()
        tracker.process_entry("S1", Direction.BULLISH, 90.0, Decimal("100"), date(2026, 3, 24))
        tracker.process_exit("S1", Decimal("120"), date(2026, 3, 25))
        tracker.process_entry("S2", Direction.BULLISH, 90.0, Decimal("100"), date(2026, 3, 25))
        tracker.process_exit("S2", Decimal("80"), date(2026, 3, 26))
        snapshots = {p.tier: p for p in tracker.get_snapshots()}
        assert snapshots[PortfolioTier.CONSERVATIVE].win_rate == 0.5

    def test_bearish_pnl_direction(self):
        tracker = PortfolioTracker()
        tracker.process_entry("S1", Direction.BEARISH, 90.0, Decimal("100"), date(2026, 3, 24))
        tracker.process_exit("S1", Decimal("80"), date(2026, 3, 25))
        snapshots = {p.tier: p for p in tracker.get_snapshots()}
        assert snapshots[PortfolioTier.CONSERVATIVE].realized_pnl == Decimal("20")
