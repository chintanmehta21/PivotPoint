"""Parametrized tests for all 14 strategies."""
import pytest
from pivotpoint.strategies.registry import StrategyRegistry
from pivotpoint.strategies.base_strategy import BaseStrategy
from pivotpoint.utils.types import Direction, TimeFrame

registry = StrategyRegistry()
ALL_STRATEGIES = list(registry.all().values())


@pytest.mark.parametrize("strategy", ALL_STRATEGIES, ids=[s.strategy_id for s in ALL_STRATEGIES])
def test_strategy_has_required_attributes(strategy):
    assert isinstance(strategy.name, str) and len(strategy.name) > 0
    assert isinstance(strategy.strategy_id, str) and len(strategy.strategy_id) > 0
    assert strategy.direction in Direction
    assert strategy.timeframe in TimeFrame
    assert isinstance(strategy.description, str)


@pytest.mark.parametrize("strategy", ALL_STRATEGIES, ids=[s.strategy_id for s in ALL_STRATEGIES])
def test_strategy_inherits_base(strategy):
    assert isinstance(strategy, BaseStrategy)


@pytest.mark.parametrize("strategy", ALL_STRATEGIES, ids=[s.strategy_id for s in ALL_STRATEGIES])
def test_strategy_repr(strategy):
    r = repr(strategy)
    assert "PivotPoint" in r or strategy.name in r


def test_registry_count():
    assert registry.count == 14


def test_registry_bullish_count():
    assert len(registry.by_direction(Direction.BULLISH)) == 6


def test_registry_bearish_count():
    assert len(registry.by_direction(Direction.BEARISH)) == 8


def test_registry_get_by_id():
    s = registry.get("BrQ1")
    assert s.name == "Skip-Strike Bearish Put Butterfly"


def test_registry_get_missing_raises():
    with pytest.raises(KeyError):
        registry.get("NONEXISTENT")
