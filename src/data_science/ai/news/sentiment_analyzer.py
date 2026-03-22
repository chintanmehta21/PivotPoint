"""News sentiment analysis interface.

FUTURE: Implement NLP/LLM-based sentiment analysis for:
- Market-moving news detection
- Geopolitical risk assessment
- Earnings surprise prediction
- Sector rotation signals
"""
from __future__ import annotations
from typing import Protocol
from pydantic import BaseModel


class SentimentResult(BaseModel):
    """Result of sentiment analysis."""
    score: float  # -1.0 (bearish) to 1.0 (bullish)
    confidence: float  # 0.0 to 1.0
    category: str  # e.g., "geopolitical", "earnings", "macro"
    summary: str = ""


class NewsSentimentAnalyzer(Protocol):
    """Protocol for news sentiment analysis.

    # FUTURE: NLP/LLM integration for news-driven signals.
    """

    def analyze(self, headlines: list[str]) -> SentimentResult:
        """Analyze news headlines for market sentiment."""
        ...
