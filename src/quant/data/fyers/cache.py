"""Parquet-based incremental candle cache for Fyers market data."""
from __future__ import annotations

import time
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any, Protocol

import pandas as pd

# ---------------------------------------------------------------------------
# Typing: minimal protocol so the real FyersClient is never imported here
# ---------------------------------------------------------------------------

class _HistoryClient(Protocol):
    async def get_history(
        self,
        symbol: str,
        resolution: str,
        from_ts: int,
        to_ts: int,
    ) -> dict[str, Any]: ...


# ---------------------------------------------------------------------------
# Resolution mapping
# ---------------------------------------------------------------------------

_RESOLUTION_MAP: dict[str, str] = {
    "D": "1D",
    "W": "1W",
    "1": "1",
    "5": "5",
    "15": "15",
    "30": "30",
    "60": "60",
}

_COLUMNS = ["timestamp", "open", "high", "low", "close", "volume"]


def _clean_symbol(symbol: str) -> str:
    """Strip exchange prefix and instrument-type suffixes for use as filename stem."""
    return (
        symbol
        .replace("NSE:", "")
        .replace("-INDEX", "")
        .replace("-EQ", "")
        .replace("-", "")
    )


def _ts_to_date(ts: int) -> date:
    return datetime.fromtimestamp(ts, tz=UTC).date()


def _candles_to_df(candles: list[list[Any]]) -> pd.DataFrame:
    df = pd.DataFrame(candles, columns=_COLUMNS)
    df["date"] = df["timestamp"].apply(_ts_to_date)
    return df


# ---------------------------------------------------------------------------
# CandleCache
# ---------------------------------------------------------------------------

class CandleCache:
    """Manages a local parquet store of OHLCV candle data.

    Each (symbol, resolution) pair is stored as a single parquet file named
    ``<clean_symbol>_<resolution>.parquet`` inside *cache_dir*.
    """

    def __init__(self, cache_dir: Path) -> None:
        self._dir = Path(cache_dir)
        self._dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _path(self, symbol: str, resolution: str) -> Path:
        clean = _clean_symbol(symbol)
        return self._dir / f"{clean}_{resolution}.parquet"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_candles(
        self,
        symbol: str,
        resolution: str,
        start: date,
        end: date,
    ) -> pd.DataFrame:
        """Return cached candles for *symbol* in [start, end] (inclusive).

        Returns an empty DataFrame when no cache file exists.
        """
        path = self._path(symbol, resolution)
        if not path.exists():
            return pd.DataFrame(columns=_COLUMNS + ["date"])

        df = pd.read_parquet(path)

        # Normalise the 'date' column to python date objects for comparison
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"]).dt.date

        mask = (df["date"] >= start) & (df["date"] <= end)
        return df.loc[mask].reset_index(drop=True)

    async def backfill(
        self,
        symbol: str,
        resolution: str,
        days: int,
        client: _HistoryClient,
    ) -> None:
        """Fetch *days* worth of history and persist to parquet (overwrites)."""
        fyers_res = _RESOLUTION_MAP.get(resolution, resolution)
        now = int(time.time())
        from_ts = now - days * 86_400
        to_ts = now

        data = await client.get_history(
            symbol=symbol,
            resolution=fyers_res,
            from_ts=from_ts,
            to_ts=to_ts,
        )

        candles: list[list[Any]] = data.get("candles", [])
        df = _candles_to_df(candles)
        df.to_parquet(self._path(symbol, resolution), index=False)

    async def update(
        self,
        symbol: str,
        resolution: str,
        client: _HistoryClient,
    ) -> None:
        """Fetch candles newer than the last cached timestamp and append them."""
        path = self._path(symbol, resolution)
        fyers_res = _RESOLUTION_MAP.get(resolution, resolution)

        if path.exists():
            existing = pd.read_parquet(path)
            last_ts = int(existing["timestamp"].max())
        else:
            existing = pd.DataFrame(columns=_COLUMNS + ["date"])
            last_ts = 0

        now = int(time.time())
        from_ts = last_ts + 1
        to_ts = now

        data = await client.get_history(
            symbol=symbol,
            resolution=fyers_res,
            from_ts=from_ts,
            to_ts=to_ts,
        )

        candles: list[list[Any]] = data.get("candles", [])
        if not candles:
            return

        new_df = _candles_to_df(candles)
        combined = pd.concat([existing, new_df], ignore_index=True)
        combined = combined.drop_duplicates(subset=["timestamp"]).sort_values("timestamp")
        combined.to_parquet(path, index=False)
