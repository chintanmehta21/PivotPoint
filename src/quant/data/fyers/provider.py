"""FyersProvider: orchestrator implementing the MarketDataProvider Protocol.

Composes FyersAuth, FyersClient, FyersWebSocket, CandleCache, and the
Greeks engine into a single coherent interface.

Design decisions
----------------
- ``__init__`` creates FyersAuth and CandleCache only — no network I/O.
- ``initialize()`` performs all network operations: token fetch, FyersClient
  construction, cache update, WebSocket connect + subscribe.
- ``get_market_snapshot()`` prefers the live WebSocket price cache; falls
  back to REST when the WebSocket is not connected.
- ``get_options_chain()`` builds symbols, batch-fetches quotes, computes IV
  and Greeks vectorially, and returns (OptionsChain, dict[str, GreeksSnapshot]).
"""
from __future__ import annotations

import logging
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from quant.config.settings import settings
from quant.data.fyers.auth import FyersAuth
from quant.data.fyers.cache import CandleCache
from quant.data.fyers.client import FyersClient
from quant.data.fyers.greeks import compute_greeks, compute_iv
from quant.data.fyers.symbols import (
    INDEX_SYMBOLS,
    VIX_SYMBOL,
    build_chain_symbols,
)
from quant.data.fyers.ws import FyersWebSocket
from quant.models.contracts import GreeksSnapshot, OptionsContract
from quant.models.market import MarketSnapshot, OptionsChain
from quant.utils.types import OptionType, Underlying

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# FyersProvider
# ---------------------------------------------------------------------------


class FyersProvider:
    """Orchestrator that composes all Fyers layer modules.

    Parameters
    ----------
    secrets_path:
        Path to the JSON credentials file (passed to FyersAuth).
    cache_dir:
        Directory for the CandleCache parquet files.
    risk_free_rate:
        Risk-free interest rate used in IV / Greeks computation (decimal).
        Defaults to the value from FyersSettings.
    """

    def __init__(
        self,
        secrets_path: str | Path,
        cache_dir: str | Path | None = None,
        risk_free_rate: float | None = None,
    ) -> None:
        self._secrets_path = str(secrets_path)
        self._cache_dir = Path(
            cache_dir if cache_dir is not None else settings.fyers.cache_dir
        )
        self._risk_free_rate: float = (
            risk_free_rate
            if risk_free_rate is not None
            else settings.fyers.risk_free_rate
        )

        # Eagerly created — no network I/O.
        self._auth = FyersAuth(self._secrets_path)
        self._cache = CandleCache(self._cache_dir)

        # Lazily created in initialize().
        self._client: FyersClient | None = None
        self._ws: FyersWebSocket | None = None

    # ------------------------------------------------------------------
    # MarketDataProvider Protocol
    # ------------------------------------------------------------------

    async def initialize(self) -> None:
        """Authenticate, populate cache, connect WebSocket.

        Steps
        -----
        1. Obtain a valid access token (re-authenticates if stale).
        2. Build FyersClient and FyersWebSocket.
        3. Update CandleCache for NIFTY (D, W), BANKNIFTY (D, W), VIX (D).
        4. Connect the WebSocket.
        5. Subscribe to NIFTY index, BANKNIFTY index, and VIX.
        """
        log.info("FyersProvider.initialize() starting")

        # Step 1: token (validates existing or re-authenticates)
        self._auth.get_valid_token()

        # Step 2: build client and WS
        self._client = FyersClient(self._auth)
        self._ws = FyersWebSocket(
            self._auth,
            on_price_update=self._on_price_update,
            on_disconnect=self._on_disconnect,
        )

        # Step 3: update cache — 5 combos
        cache_combos: list[tuple[str, str]] = [
            (INDEX_SYMBOLS[Underlying.NIFTY], "D"),
            (INDEX_SYMBOLS[Underlying.NIFTY], "W"),
            (INDEX_SYMBOLS[Underlying.BANKNIFTY], "D"),
            (INDEX_SYMBOLS[Underlying.BANKNIFTY], "W"),
            (VIX_SYMBOL, "D"),
        ]
        for symbol, resolution in cache_combos:
            try:
                await self._cache.update(symbol, resolution, self._client)
            except Exception as exc:  # noqa: BLE001
                log.warning("Cache update failed for %s/%s: %s", symbol, resolution, exc)

        # Step 4: connect WebSocket
        self._ws.connect()

        # Step 5: subscribe to indices + VIX
        symbols_to_subscribe = [
            INDEX_SYMBOLS[Underlying.NIFTY],
            INDEX_SYMBOLS[Underlying.BANKNIFTY],
            VIX_SYMBOL,
        ]
        self._ws.subscribe(symbols_to_subscribe)

        log.info("FyersProvider.initialize() complete")

    async def shutdown(self) -> None:
        """Disconnect the WebSocket gracefully."""
        if self._ws is not None:
            self._ws.disconnect()
            log.info("FyersProvider.shutdown() complete")

    async def get_market_snapshot(self, underlying: Underlying) -> MarketSnapshot:
        """Return current market state for *underlying*.

        Reads from the WebSocket price cache when connected; falls back to a
        REST quotes call via FyersClient otherwise.
        """
        index_sym = INDEX_SYMBOLS[underlying]

        use_ws = (
            self._ws is not None
            and self._ws.is_connected()
            and index_sym in self._ws.price_cache
        )

        if use_ws:
            assert self._ws is not None
            spot = float(self._ws.price_cache[index_sym].get("ltp", 0.0))
            vix_data = self._ws.price_cache.get(VIX_SYMBOL, {})
            vix = float(vix_data.get("ltp", 0.0))
        else:
            # REST fallback
            assert self._client is not None, (
                "FyersProvider not initialized — call initialize() first"
            )
            resp = await self._client.get_quotes([index_sym, VIX_SYMBOL])
            quotes: dict[str, float] = {}
            for item in resp.get("d", []):
                sym = item.get("n", "")
                lp = float(item.get("v", {}).get("lp", 0.0))
                quotes[sym] = lp
            spot = quotes.get(index_sym, 0.0)
            vix = quotes.get(VIX_SYMBOL, 0.0)

        return MarketSnapshot(
            underlying=underlying,
            price=spot,
            timestamp=datetime.now(tz=UTC),
            vix_level=vix,
        )

    async def get_options_chain(
        self, underlying: Underlying, expiry: date
    ) -> tuple[OptionsChain, dict[str, GreeksSnapshot]]:
        """Return (OptionsChain, greeks_map) for *underlying* at *expiry*.

        1. Get the current spot price.
        2. Round spot to the nearest ATM strike.
        3. Build all CE/PE symbol strings for the configured range.
        4. Batch-fetch live quotes via FyersClient.
        5. Compute IV and Greeks vectorially.
        6. Build OptionsChain and GreeksSnapshot map.
        """
        assert self._client is not None, (
            "FyersProvider not initialized — call initialize() first"
        )

        # Spot price
        snapshot = await self.get_market_snapshot(underlying)
        spot = snapshot.price
        atm_strike = self._round_to_strike(spot, underlying)

        # Build symbols
        interval = self._strike_interval(underlying)
        sym_range = self._strike_range(underlying)
        symbols = build_chain_symbols(
            underlying,
            expiry,
            atm_strike,
            strike_range=sym_range,
            strike_interval=interval,
        )

        # Fetch quotes
        resp = await self._client.get_quotes(symbols)
        quote_map: dict[str, float] = {}
        for item in resp.get("d", []):
            sym = item.get("n", "")
            lp = float(item.get("v", {}).get("lp", 0.0))
            quote_map[sym] = lp

        # Only process symbols that came back from the API
        active_symbols = [s for s in symbols if s in quote_map]
        if not active_symbols:
            return (
                OptionsChain(underlying=underlying, expiry=expiry, contracts=[]),
                {},
            )

        # Compute time to expiry (in years)
        today = date.today()
        days_to_expiry = max((expiry - today).days, 1)
        T = days_to_expiry / 365.0

        # Vectorise inputs
        n = len(active_symbols)
        premiums_arr = np.array([quote_map[s] for s in active_symbols], dtype=float)
        spots_arr = np.full(n, spot, dtype=float)

        # Parse strike and type from symbol list
        from quant.data.fyers.symbols import parse_option_symbol

        strikes_list: list[int] = []
        opt_types_list: list[int] = []  # 1 = CE, -1 = PE
        parsed: list[tuple] = []
        for sym in active_symbols:
            _, _, strike, otype = parse_option_symbol(sym)
            strikes_list.append(strike)
            opt_types_list.append(1 if otype == "CE" else -1)
            parsed.append((strike, otype))

        strikes_arr = np.array(strikes_list, dtype=float)
        opt_types_arr = np.array(opt_types_list, dtype=int)

        # Compute IV
        ivs_arr = compute_iv(
            premiums=premiums_arr,
            spots=spots_arr,
            strikes=strikes_arr,
            T=T,
            option_types=opt_types_arr,
            r=self._risk_free_rate,
        )

        # Compute Greeks
        greeks_dict = compute_greeks(
            spots=spots_arr,
            strikes=strikes_arr,
            T=T,
            ivs=ivs_arr,
            option_types=opt_types_arr,
            r=self._risk_free_rate,
        )

        # Build output structures
        contracts: list[OptionsContract] = []
        greeks_map: dict[str, GreeksSnapshot] = {}
        lot_size = self._lot_size(underlying)

        for idx, sym in enumerate(active_symbols):
            strike_val, otype_str = parsed[idx]
            contract = OptionsContract(
                symbol=sym,
                expiry=expiry,
                strike=Decimal(str(strike_val)),
                option_type=OptionType.CE if otype_str == "CE" else OptionType.PE,
                premium=Decimal(str(round(float(premiums_arr[idx]), 2))),
                lot_size=lot_size,
            )
            contracts.append(contract)

            greeks_map[sym] = GreeksSnapshot(
                delta=float(greeks_dict["delta"][idx]),
                gamma=float(greeks_dict["gamma"][idx]),
                vega=float(greeks_dict["vega"][idx]),
                theta=float(greeks_dict["theta"][idx]),
                iv=float(ivs_arr[idx]),
            )

        chain = OptionsChain(
            underlying=underlying,
            expiry=expiry,
            contracts=contracts,
        )
        return chain, greeks_map

    async def get_funds(self) -> Decimal:
        """Return the available balance from the Fyers fund_limit response."""
        assert self._client is not None, (
            "FyersProvider not initialized — call initialize() first"
        )
        resp = await self._client.get_funds()
        # Fyers returns a list under "fund_limit"; id=10 is available balance.
        for entry in resp.get("fund_limit", []):
            if entry.get("id") == 10:
                return Decimal(str(entry.get("equityAmount", 0.0)))
        # Fallback: sum all equityAmount entries
        total = sum(
            float(e.get("equityAmount", 0.0))
            for e in resp.get("fund_limit", [])
        )
        return Decimal(str(total))

    async def get_positions(self) -> list[dict]:
        """Return the list of net open positions."""
        assert self._client is not None, (
            "FyersProvider not initialized — call initialize() first"
        )
        resp = await self._client.get_positions()
        return resp.get("netPositions", [])

    async def get_candles(
        self, symbol: str, resolution: str, periods: int
    ) -> pd.DataFrame:
        """Return up to *periods* recent candles from the local CandleCache."""
        from datetime import timedelta

        today = date.today()
        # Back far enough to cover the requested number of periods.
        start = today - timedelta(days=periods * 2 + 30)
        df = self._cache.get_candles(symbol, resolution, start=start, end=today)
        if len(df) > periods:
            df = df.iloc[-periods:]
        return df.reset_index(drop=True)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _round_to_strike(self, price: float, underlying: Underlying) -> int:
        """Round *price* to the nearest valid strike for *underlying*."""
        interval = self._strike_interval(underlying)
        return int(round(price / interval) * interval)

    def _strike_interval(self, underlying: Underlying) -> int:
        """Return the strike interval for *underlying* from settings."""
        if underlying == Underlying.NIFTY:
            return settings.fyers.strike_interval_nifty
        return settings.fyers.strike_interval_banknifty

    def _strike_range(self, underlying: Underlying) -> int:
        """Return the strike range for *underlying* from settings."""
        if underlying == Underlying.NIFTY:
            return settings.fyers.strike_range_nifty
        return settings.fyers.strike_range_banknifty

    def _lot_size(self, underlying: Underlying) -> int:
        """Return the lot size for *underlying* from settings."""
        if underlying == Underlying.NIFTY:
            return settings.fyers.lot_size_nifty
        return settings.fyers.lot_size_banknifty

    # ------------------------------------------------------------------
    # WebSocket callbacks
    # ------------------------------------------------------------------

    def _on_price_update(self, msg: dict[str, Any]) -> None:
        """Callback fired on every WebSocket tick (no-op; cache managed by WS)."""
        pass  # ws.price_cache is updated by FyersWebSocket internally

    def _on_disconnect(self) -> None:
        """Callback fired when the WebSocket disconnects."""
        log.warning("FyersWebSocket disconnected unexpectedly.")
