"""Tests for parquet-based candle cache."""
from datetime import date
from pathlib import Path
from unittest.mock import AsyncMock
import pandas as pd
import pytest
from quant.data.fyers.cache import CandleCache

@pytest.fixture
def cache(tmp_path):
    return CandleCache(cache_dir=tmp_path)

@pytest.fixture
def sample_candles():
    return {"s": "ok", "candles": [
        [1711324800, 24000, 24100, 23900, 24050, 1000000],
        [1711411200, 24050, 24200, 24000, 24150, 900000],
    ]}

class TestCandleCacheInit:
    def test_creates_cache_dir(self, tmp_path):
        cache_dir = tmp_path / "candles"
        assert not cache_dir.exists()
        CandleCache(cache_dir=cache_dir)
        assert cache_dir.exists()

class TestGetCandles:
    def test_returns_empty_df_if_no_file(self, cache):
        df = cache.get_candles("NIFTY50", "D", date(2024, 1, 1), date(2024, 12, 31))
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0

    def test_reads_cached_data(self, cache, tmp_path):
        df = pd.DataFrame({
            "timestamp": [1711324800, 1711411200],
            "open": [24000, 24050], "high": [24100, 24200],
            "low": [23900, 24000], "close": [24050, 24150],
            "volume": [1000000, 900000],
            "date": [date(2024, 3, 25), date(2024, 3, 26)],
        })
        path = tmp_path / "NIFTY50_D.parquet"
        df.to_parquet(path, index=False)
        result = cache.get_candles("NIFTY50", "D", date(2024, 3, 25), date(2024, 3, 26))
        assert len(result) == 2

class TestBackfill:
    @pytest.mark.asyncio
    async def test_writes_parquet_file(self, cache, tmp_path, sample_candles):
        mock_client = AsyncMock()
        mock_client.get_history.return_value = sample_candles
        await cache.backfill("NIFTY50", "D", 365, mock_client)
        path = tmp_path / "NIFTY50_D.parquet"
        assert path.exists()
        assert len(pd.read_parquet(path)) == 2

class TestUpdate:
    @pytest.mark.asyncio
    async def test_appends_new_candles(self, cache, tmp_path, sample_candles):
        df = pd.DataFrame({
            "timestamp": [1711324800], "open": [24000], "high": [24100],
            "low": [23900], "close": [24050], "volume": [1000000],
            "date": [date(2024, 3, 25)],
        })
        (tmp_path / "NIFTY50_D.parquet").write_bytes(df.to_parquet(index=False))
        mock_client = AsyncMock()
        mock_client.get_history.return_value = {"s": "ok", "candles": [[1711411200, 24050, 24200, 24000, 24150, 900000]]}
        await cache.update("NIFTY50", "D", mock_client)
        assert len(pd.read_parquet(tmp_path / "NIFTY50_D.parquet")) == 2
