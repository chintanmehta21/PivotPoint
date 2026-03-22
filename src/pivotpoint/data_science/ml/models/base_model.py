"""Base model interface for ML integration.

FUTURE: Implement concrete models for:
- Signal prediction (entry/exit timing)
- Volatility forecasting
- Regime classification (trending/mean-reverting/volatile)
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    import pandas as pd


class ModelInterface(Protocol):
    """Protocol for ML model implementations.

    # FUTURE: ML model integration point.
    # Implement this protocol to create predictive models
    # that enhance strategy signal generation.
    """

    def predict(self, features: pd.DataFrame) -> dict[str, float]:
        """Generate predictions from features."""
        ...

    def train(self, data: pd.DataFrame) -> None:
        """Train the model on historical data."""
        ...

    def evaluate(self, data: pd.DataFrame) -> dict[str, float]:
        """Evaluate model performance on test data."""
        ...

    def save(self, path: str) -> None:
        """Save model to disk."""
        ...

    def load(self, path: str) -> None:
        """Load model from disk."""
        ...
