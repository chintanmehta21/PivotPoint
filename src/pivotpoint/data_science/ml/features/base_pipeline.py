"""Base feature pipeline interface for ML integration.

FUTURE: Implement concrete pipelines for IV surface features,
Greeks-based features, and market microstructure features.
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    import pandas as pd
    from pivotpoint.models.market import MarketSnapshot, OptionsChain


class FeaturePipeline(Protocol):
    """Protocol for feature engineering pipelines.

    # FUTURE: ML feature engineering integration point.
    # Implement this protocol to create feature extractors
    # that feed into ML models for signal generation.
    """

    def extract(self, market: MarketSnapshot, chain: OptionsChain) -> pd.DataFrame:
        """Extract raw features from market data."""
        ...

    def transform(self, features: pd.DataFrame) -> pd.DataFrame:
        """Transform raw features into model-ready format."""
        ...
