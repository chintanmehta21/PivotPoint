"""Dynamic strategy registry with importlib auto-discovery."""
from __future__ import annotations

import importlib
import pkgutil
from pathlib import Path
from typing import TYPE_CHECKING

import structlog

from quant.strategies.base_strategy import BaseStrategy
from quant.utils.types import Direction, TimeFrame

if TYPE_CHECKING:
    pass

logger = structlog.get_logger()


class StrategyRegistry:
    """Auto-discovers and registers all BaseStrategy subclasses."""

    def __init__(self) -> None:
        self._strategies: dict[str, BaseStrategy] = {}
        self._auto_discover()

    def _auto_discover(self) -> None:
        """Scan bullish/ and bearish/ subpackages for BaseStrategy subclasses."""
        strategies_dir = Path(__file__).parent
        for subpackage in ["bullish", "bearish"]:
            package_path = strategies_dir / subpackage
            if not package_path.exists():
                continue
            package_name = f"quant.strategies.{subpackage}"
            try:
                package = importlib.import_module(package_name)
            except ImportError:
                logger.warning("Failed to import strategy package", package=package_name)
                continue

            for _importer, module_name, _is_pkg in pkgutil.iter_modules([str(package_path)]):
                full_module_name = f"{package_name}.{module_name}"
                try:
                    module = importlib.import_module(full_module_name)
                except ImportError as e:
                    logger.warning("Failed to import strategy module", module=full_module_name, error=str(e))
                    continue

                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (
                        isinstance(attr, type)
                        and issubclass(attr, BaseStrategy)
                        and attr is not BaseStrategy
                        and hasattr(attr, "strategy_id")
                        and isinstance(getattr(attr, "strategy_id", None), str)
                    ):
                        try:
                            instance = attr()
                            self._strategies[instance.strategy_id] = instance
                            logger.debug("Registered strategy", strategy=instance.name, id=instance.strategy_id)
                        except Exception as e:
                            logger.warning("Failed to instantiate strategy", cls=attr_name, error=str(e))

    def get(self, strategy_id: str) -> BaseStrategy:
        """Get a strategy by ID. Raises KeyError if not found."""
        if strategy_id not in self._strategies:
            raise KeyError(f"Strategy not found: {strategy_id}")
        return self._strategies[strategy_id]

    def by_direction(self, direction: Direction) -> list[BaseStrategy]:
        """Get all strategies for a given direction."""
        return [s for s in self._strategies.values() if s.direction == direction]

    def by_timeframe(self, timeframe: TimeFrame) -> list[BaseStrategy]:
        """Get all strategies for a given timeframe."""
        return [s for s in self._strategies.values() if s.timeframe == timeframe]

    def all(self) -> dict[str, BaseStrategy]:
        """Get all registered strategies."""
        return dict(self._strategies)

    @property
    def count(self) -> int:
        """Number of registered strategies."""
        return len(self._strategies)
