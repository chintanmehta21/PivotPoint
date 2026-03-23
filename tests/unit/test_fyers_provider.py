"""Tests for FyersProvider orchestrator."""
from __future__ import annotations

import asyncio
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch, call

import pytest

from quant.models.contracts import GreeksSnapshot, OptionsContract
from quant.models.market import MarketSnapshot, OptionsChain
from quant.utils.types import Underlying, OptionType


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_auth_mock(secrets_path: str = "secrets/fyers.json") -> MagicMock:
    auth = MagicMock()
    auth.get_valid_token.return_value = "test_token_123"
    auth._creds = {"app_id": "TESTAPP-100"}
    return auth


def _make_client_mock() -> MagicMock:
    client = MagicMock()
    client.get_quotes = AsyncMock(return_value={"s": "ok", "d": []})
    client.get_history = AsyncMock(return_value={"candles": []})
    client.get_funds = AsyncMock(return_value={"s": "ok", "fund_limit": []})
    client.get_positions = AsyncMock(return_value={"s": "ok", "netPositions": []})
    return client


def _make_ws_mock() -> MagicMock:
    ws = MagicMock()
    ws.price_cache = {}
    ws.connect = MagicMock()
    ws.subscribe = MagicMock()
    ws.disconnect = MagicMock()
    ws.is_connected.return_value = True
    return ws


def _make_cache_mock() -> MagicMock:
    cache = MagicMock()
    cache.update = AsyncMock()
    cache.get_candles = MagicMock(return_value=MagicMock())  # returns DataFrame-like
    return cache


# ---------------------------------------------------------------------------
# TestProtocolConformance
# ---------------------------------------------------------------------------

class TestProtocolConformance:
    """Verify FyersProvider exposes all methods required by MarketDataProvider."""

    def test_has_initialize(self):
        from quant.data.fyers.provider import FyersProvider
        assert hasattr(FyersProvider, "initialize")
        assert asyncio.iscoroutinefunction(FyersProvider.initialize)

    def test_has_shutdown(self):
        from quant.data.fyers.provider import FyersProvider
        assert hasattr(FyersProvider, "shutdown")
        assert asyncio.iscoroutinefunction(FyersProvider.shutdown)

    def test_has_get_options_chain(self):
        from quant.data.fyers.provider import FyersProvider
        assert hasattr(FyersProvider, "get_options_chain")
        assert asyncio.iscoroutinefunction(FyersProvider.get_options_chain)

    def test_has_get_market_snapshot(self):
        from quant.data.fyers.provider import FyersProvider
        assert hasattr(FyersProvider, "get_market_snapshot")
        assert asyncio.iscoroutinefunction(FyersProvider.get_market_snapshot)

    def test_has_get_funds(self):
        from quant.data.fyers.provider import FyersProvider
        assert hasattr(FyersProvider, "get_funds")
        assert asyncio.iscoroutinefunction(FyersProvider.get_funds)

    def test_has_get_positions(self):
        from quant.data.fyers.provider import FyersProvider
        assert hasattr(FyersProvider, "get_positions")
        assert asyncio.iscoroutinefunction(FyersProvider.get_positions)

    def test_has_get_candles(self):
        from quant.data.fyers.provider import FyersProvider
        assert hasattr(FyersProvider, "get_candles")
        assert asyncio.iscoroutinefunction(FyersProvider.get_candles)

    def test_satisfies_protocol(self):
        """FyersProvider must be structurally compatible with MarketDataProvider."""
        from quant.data.fyers.provider import FyersProvider
        from quant.data.provider import MarketDataProvider
        # Runtime_checkable not set on Protocol, but we can verify via isinstance
        # after instantiation in other tests. Here just check method presence.
        required = [
            "initialize", "shutdown", "get_options_chain",
            "get_market_snapshot", "get_funds", "get_positions", "get_candles",
        ]
        for method in required:
            assert hasattr(FyersProvider, method), f"Missing method: {method}"


# ---------------------------------------------------------------------------
# TestFyersProviderInit
# ---------------------------------------------------------------------------

class TestFyersProviderInit:
    """Verify constructor creates FyersAuth and CandleCache — no network I/O."""

    def test_creates_auth(self, tmp_path):
        """Constructor must create a FyersAuth instance with the secrets path."""
        from quant.data.fyers.provider import FyersProvider

        secrets_file = tmp_path / "fyers.json"
        secrets_file.write_text('{"dummy": true}')

        with (
            patch("quant.data.fyers.provider.FyersAuth") as MockAuth,
            patch("quant.data.fyers.provider.CandleCache") as MockCache,
        ):
            provider = FyersProvider(
                secrets_path=str(secrets_file),
                cache_dir=str(tmp_path / "candles"),
            )
            MockAuth.assert_called_once_with(str(secrets_file))
            MockCache.assert_called_once()

    def test_client_and_ws_not_created_at_init(self, tmp_path):
        """Client and WS must NOT be created in __init__ (lazy init)."""
        from quant.data.fyers.provider import FyersProvider

        secrets_file = tmp_path / "fyers.json"
        secrets_file.write_text('{"dummy": true}')

        with (
            patch("quant.data.fyers.provider.FyersAuth"),
            patch("quant.data.fyers.provider.CandleCache"),
            patch("quant.data.fyers.provider.FyersClient") as MockClient,
            patch("quant.data.fyers.provider.FyersWebSocket") as MockWS,
        ):
            provider = FyersProvider(
                secrets_path=str(secrets_file),
                cache_dir=str(tmp_path / "candles"),
            )
            MockClient.assert_not_called()
            MockWS.assert_not_called()


# ---------------------------------------------------------------------------
# TestGetMarketSnapshot
# ---------------------------------------------------------------------------

class TestGetMarketSnapshot:
    """Verify get_market_snapshot reads from ws.price_cache correctly."""

    @pytest.mark.asyncio
    async def test_returns_market_snapshot_from_ws_cache(self, tmp_path):
        """Should read spot price and VIX from the WebSocket price cache."""
        from quant.data.fyers.provider import FyersProvider

        secrets_file = tmp_path / "fyers.json"
        secrets_file.write_text('{"dummy": true}')

        with (
            patch("quant.data.fyers.provider.FyersAuth"),
            patch("quant.data.fyers.provider.CandleCache"),
        ):
            provider = FyersProvider(
                secrets_path=str(secrets_file),
                cache_dir=str(tmp_path / "candles"),
            )

        ws = _make_ws_mock()
        ws.price_cache = {
            "NSE:NIFTY50-INDEX": {"ltp": 24500.0},
            "NSE:INDIAVIX-INDEX": {"ltp": 16.5},
        }
        ws.is_connected.return_value = True
        provider._ws = ws

        snapshot = await provider.get_market_snapshot(Underlying.NIFTY)

        assert isinstance(snapshot, MarketSnapshot)
        assert snapshot.underlying == Underlying.NIFTY
        assert snapshot.price == 24500.0
        assert snapshot.vix_level == 16.5

    @pytest.mark.asyncio
    async def test_uses_rest_fallback_when_ws_not_connected(self, tmp_path):
        """Should fall back to REST quotes when WS is not connected."""
        from quant.data.fyers.provider import FyersProvider

        secrets_file = tmp_path / "fyers.json"
        secrets_file.write_text('{"dummy": true}')

        with (
            patch("quant.data.fyers.provider.FyersAuth"),
            patch("quant.data.fyers.provider.CandleCache"),
        ):
            provider = FyersProvider(
                secrets_path=str(secrets_file),
                cache_dir=str(tmp_path / "candles"),
            )

        ws = _make_ws_mock()
        ws.is_connected.return_value = False
        ws.price_cache = {}
        provider._ws = ws

        client = _make_client_mock()
        client.get_quotes = AsyncMock(return_value={
            "s": "ok",
            "d": [
                {"n": "NSE:NIFTY50-INDEX", "v": {"lp": 24300.0}},
                {"n": "NSE:INDIAVIX-INDEX", "v": {"lp": 15.0}},
            ],
        })
        provider._client = client

        snapshot = await provider.get_market_snapshot(Underlying.NIFTY)

        assert isinstance(snapshot, MarketSnapshot)
        assert snapshot.price == 24300.0
        assert snapshot.vix_level == 15.0

    @pytest.mark.asyncio
    async def test_banknifty_snapshot(self, tmp_path):
        """Should return BANKNIFTY snapshot correctly."""
        from quant.data.fyers.provider import FyersProvider

        secrets_file = tmp_path / "fyers.json"
        secrets_file.write_text('{"dummy": true}')

        with (
            patch("quant.data.fyers.provider.FyersAuth"),
            patch("quant.data.fyers.provider.CandleCache"),
        ):
            provider = FyersProvider(
                secrets_path=str(secrets_file),
                cache_dir=str(tmp_path / "candles"),
            )

        ws = _make_ws_mock()
        ws.price_cache = {
            "NSE:NIFTYBANK-INDEX": {"ltp": 52000.0},
            "NSE:INDIAVIX-INDEX": {"ltp": 14.2},
        }
        ws.is_connected.return_value = True
        provider._ws = ws

        snapshot = await provider.get_market_snapshot(Underlying.BANKNIFTY)

        assert snapshot.underlying == Underlying.BANKNIFTY
        assert snapshot.price == 52000.0
        assert snapshot.vix_level == 14.2


# ---------------------------------------------------------------------------
# TestGetOptionsChain
# ---------------------------------------------------------------------------

class TestGetOptionsChain:
    """Verify get_options_chain builds an OptionsChain with Greeks."""

    @pytest.mark.asyncio
    async def test_returns_options_chain_and_greeks(self, tmp_path):
        """Should return (OptionsChain, dict[str, GreeksSnapshot]) from quotes."""
        from quant.data.fyers.provider import FyersProvider

        secrets_file = tmp_path / "fyers.json"
        secrets_file.write_text('{"dummy": true}')

        with (
            patch("quant.data.fyers.provider.FyersAuth"),
            patch("quant.data.fyers.provider.CandleCache"),
        ):
            provider = FyersProvider(
                secrets_path=str(secrets_file),
                cache_dir=str(tmp_path / "candles"),
            )

        # Provide spot price via WS
        ws = _make_ws_mock()
        ws.price_cache = {
            "NSE:NIFTY50-INDEX": {"ltp": 24000.0},
            "NSE:INDIAVIX-INDEX": {"ltp": 16.0},
        }
        ws.is_connected.return_value = True
        provider._ws = ws

        # Two option symbols: one CE, one PE
        expiry = date(2026, 3, 27)
        ce_sym = "NSE:NIFTY2632724000CE"
        pe_sym = "NSE:NIFTY2632724000PE"

        client = _make_client_mock()
        client.get_quotes = AsyncMock(return_value={
            "s": "ok",
            "d": [
                {"n": ce_sym, "v": {"lp": 120.0}},
                {"n": pe_sym, "v": {"lp": 95.0}},
            ],
        })
        provider._client = client

        chain, greeks_map = await provider.get_options_chain(Underlying.NIFTY, expiry)

        assert isinstance(chain, OptionsChain)
        assert chain.underlying == Underlying.NIFTY
        assert chain.expiry == expiry
        # Should have at least our 2 contracts
        assert len(chain.contracts) >= 2
        symbols_in_chain = {c.symbol for c in chain.contracts}
        assert ce_sym in symbols_in_chain
        assert pe_sym in symbols_in_chain

        # Each symbol should have a GreeksSnapshot
        assert ce_sym in greeks_map
        assert pe_sym in greeks_map
        assert isinstance(greeks_map[ce_sym], GreeksSnapshot)
        assert isinstance(greeks_map[pe_sym], GreeksSnapshot)

    @pytest.mark.asyncio
    async def test_greeks_iv_nonzero_for_meaningful_premium(self, tmp_path):
        """IV should be > 0 for options with meaningful premiums."""
        from quant.data.fyers.provider import FyersProvider

        secrets_file = tmp_path / "fyers.json"
        secrets_file.write_text('{"dummy": true}')

        with (
            patch("quant.data.fyers.provider.FyersAuth"),
            patch("quant.data.fyers.provider.CandleCache"),
        ):
            provider = FyersProvider(
                secrets_path=str(secrets_file),
                cache_dir=str(tmp_path / "candles"),
            )

        ws = _make_ws_mock()
        ws.price_cache = {
            "NSE:NIFTY50-INDEX": {"ltp": 24000.0},
            "NSE:INDIAVIX-INDEX": {"ltp": 16.0},
        }
        ws.is_connected.return_value = True
        provider._ws = ws

        expiry = date(2026, 3, 27)
        ce_sym = "NSE:NIFTY2632724000CE"
        pe_sym = "NSE:NIFTY2632724000PE"

        client = _make_client_mock()
        client.get_quotes = AsyncMock(return_value={
            "s": "ok",
            "d": [
                {"n": ce_sym, "v": {"lp": 120.0}},
                {"n": pe_sym, "v": {"lp": 95.0}},
            ],
        })
        provider._client = client

        _, greeks_map = await provider.get_options_chain(Underlying.NIFTY, expiry)

        assert greeks_map[ce_sym].iv > 0.0
        assert greeks_map[pe_sym].iv > 0.0


# ---------------------------------------------------------------------------
# TestInitialize
# ---------------------------------------------------------------------------

class TestInitialize:
    """Verify initialize() wires up all components correctly."""

    @pytest.mark.asyncio
    async def test_initialize_calls_all_components(self, tmp_path):
        """initialize() should: get token, create client+ws, update cache 5 times,
        connect WS, subscribe to indices+VIX.
        """
        from quant.data.fyers.provider import FyersProvider

        secrets_file = tmp_path / "fyers.json"
        secrets_file.write_text('{"dummy": true}')

        mock_auth = _make_auth_mock()
        mock_cache = _make_cache_mock()
        mock_client = _make_client_mock()
        mock_ws = _make_ws_mock()

        with (
            patch("quant.data.fyers.provider.FyersAuth", return_value=mock_auth),
            patch("quant.data.fyers.provider.CandleCache", return_value=mock_cache),
            patch("quant.data.fyers.provider.FyersClient", return_value=mock_client),
            patch("quant.data.fyers.provider.FyersWebSocket", return_value=mock_ws),
        ):
            provider = FyersProvider(
                secrets_path=str(secrets_file),
                cache_dir=str(tmp_path / "candles"),
            )
            await provider.initialize()

        # Auth token obtained
        mock_auth.get_valid_token.assert_called()

        # Cache updated 5 times: NIFTY/D, NIFTY/W, BANKNIFTY/D, BANKNIFTY/W, VIX/D
        assert mock_cache.update.call_count == 5

        # WS connected
        mock_ws.connect.assert_called_once()

        # WS subscribed (at least indices + VIX)
        mock_ws.subscribe.assert_called()
        subscribe_calls_args = [
            arg
            for c in mock_ws.subscribe.call_args_list
            for arg in (c.args[0] if c.args else c.kwargs.get("symbols", []))
        ]
        assert "NSE:NIFTY50-INDEX" in subscribe_calls_args
        assert "NSE:NIFTYBANK-INDEX" in subscribe_calls_args
        assert "NSE:INDIAVIX-INDEX" in subscribe_calls_args

    @pytest.mark.asyncio
    async def test_initialize_cache_update_symbols(self, tmp_path):
        """Cache update calls must cover NIFTY, BANKNIFTY (D+W) and VIX (D)."""
        from quant.data.fyers.provider import FyersProvider

        secrets_file = tmp_path / "fyers.json"
        secrets_file.write_text('{"dummy": true}')

        mock_auth = _make_auth_mock()
        mock_cache = _make_cache_mock()
        mock_client = _make_client_mock()
        mock_ws = _make_ws_mock()

        with (
            patch("quant.data.fyers.provider.FyersAuth", return_value=mock_auth),
            patch("quant.data.fyers.provider.CandleCache", return_value=mock_cache),
            patch("quant.data.fyers.provider.FyersClient", return_value=mock_client),
            patch("quant.data.fyers.provider.FyersWebSocket", return_value=mock_ws),
        ):
            provider = FyersProvider(
                secrets_path=str(secrets_file),
                cache_dir=str(tmp_path / "candles"),
            )
            await provider.initialize()

        # Collect all (symbol, resolution) combos from update calls
        update_calls = [
            (c.args[0] if c.args else c.kwargs["symbol"],
             c.args[1] if len(c.args) > 1 else c.kwargs["resolution"])
            for c in mock_cache.update.call_args_list
        ]
        symbols_called = {sym for sym, _ in update_calls}
        resolutions_per_sym = {}
        for sym, res in update_calls:
            resolutions_per_sym.setdefault(sym, set()).add(res)

        # NIFTY and BANKNIFTY should have both D and W
        assert "NSE:NIFTY50-INDEX" in symbols_called
        assert "NSE:NIFTYBANK-INDEX" in symbols_called
        assert "NSE:INDIAVIX-INDEX" in symbols_called
        assert "D" in resolutions_per_sym.get("NSE:NIFTY50-INDEX", set())
        assert "W" in resolutions_per_sym.get("NSE:NIFTY50-INDEX", set())
        assert "D" in resolutions_per_sym.get("NSE:NIFTYBANK-INDEX", set())
        assert "W" in resolutions_per_sym.get("NSE:NIFTYBANK-INDEX", set())
        assert "D" in resolutions_per_sym.get("NSE:INDIAVIX-INDEX", set())


# ---------------------------------------------------------------------------
# TestShutdown
# ---------------------------------------------------------------------------

class TestShutdown:
    """Verify shutdown disconnects the WebSocket."""

    @pytest.mark.asyncio
    async def test_shutdown_disconnects_ws(self, tmp_path):
        """shutdown() should call ws.disconnect()."""
        from quant.data.fyers.provider import FyersProvider

        secrets_file = tmp_path / "fyers.json"
        secrets_file.write_text('{"dummy": true}')

        with (
            patch("quant.data.fyers.provider.FyersAuth"),
            patch("quant.data.fyers.provider.CandleCache"),
        ):
            provider = FyersProvider(
                secrets_path=str(secrets_file),
                cache_dir=str(tmp_path / "candles"),
            )

        ws = _make_ws_mock()
        provider._ws = ws

        await provider.shutdown()

        ws.disconnect.assert_called_once()

    @pytest.mark.asyncio
    async def test_shutdown_safe_without_ws(self, tmp_path):
        """shutdown() must not raise if WS was never initialized."""
        from quant.data.fyers.provider import FyersProvider

        secrets_file = tmp_path / "fyers.json"
        secrets_file.write_text('{"dummy": true}')

        with (
            patch("quant.data.fyers.provider.FyersAuth"),
            patch("quant.data.fyers.provider.CandleCache"),
        ):
            provider = FyersProvider(
                secrets_path=str(secrets_file),
                cache_dir=str(tmp_path / "candles"),
            )

        # _ws is None — should not raise
        await provider.shutdown()


# ---------------------------------------------------------------------------
# TestGetFunds
# ---------------------------------------------------------------------------

class TestGetFunds:
    """Verify get_funds parses the Fyers fund_limit response."""

    @pytest.mark.asyncio
    async def test_returns_available_balance(self, tmp_path):
        secrets_file = tmp_path / "fyers.json"
        secrets_file.write_text('{"dummy": true}')

        with (
            patch("quant.data.fyers.provider.FyersAuth"),
            patch("quant.data.fyers.provider.CandleCache"),
        ):
            from quant.data.fyers.provider import FyersProvider
            provider = FyersProvider(
                secrets_path=str(secrets_file),
                cache_dir=str(tmp_path / "candles"),
            )

        client = _make_client_mock()
        client.get_funds = AsyncMock(return_value={
            "s": "ok",
            "fund_limit": [
                {"id": 10, "title": "Available Balance", "equityAmount": 150000.0},
            ],
        })
        provider._client = client

        result = await provider.get_funds()
        assert isinstance(result, Decimal)
        assert result == Decimal("150000.0")


# ---------------------------------------------------------------------------
# TestGetPositions
# ---------------------------------------------------------------------------

class TestGetPositions:
    """Verify get_positions returns netPositions list."""

    @pytest.mark.asyncio
    async def test_returns_list_of_positions(self, tmp_path):
        secrets_file = tmp_path / "fyers.json"
        secrets_file.write_text('{"dummy": true}')

        with (
            patch("quant.data.fyers.provider.FyersAuth"),
            patch("quant.data.fyers.provider.CandleCache"),
        ):
            from quant.data.fyers.provider import FyersProvider
            provider = FyersProvider(
                secrets_path=str(secrets_file),
                cache_dir=str(tmp_path / "candles"),
            )

        pos_data = [{"symbol": "NSE:NIFTY2632724000CE", "qty": 75, "side": 1}]
        client = _make_client_mock()
        client.get_positions = AsyncMock(return_value={
            "s": "ok",
            "netPositions": pos_data,
        })
        provider._client = client

        positions = await provider.get_positions()
        assert positions == pos_data

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_positions(self, tmp_path):
        secrets_file = tmp_path / "fyers.json"
        secrets_file.write_text('{"dummy": true}')

        with (
            patch("quant.data.fyers.provider.FyersAuth"),
            patch("quant.data.fyers.provider.CandleCache"),
        ):
            from quant.data.fyers.provider import FyersProvider
            provider = FyersProvider(
                secrets_path=str(secrets_file),
                cache_dir=str(tmp_path / "candles"),
            )

        client = _make_client_mock()
        client.get_positions = AsyncMock(return_value={"s": "ok", "netPositions": []})
        provider._client = client

        positions = await provider.get_positions()
        assert positions == []


# ---------------------------------------------------------------------------
# TestGetCandles
# ---------------------------------------------------------------------------

class TestGetCandles:
    """Verify get_candles reads from CandleCache."""

    @pytest.mark.asyncio
    async def test_reads_from_cache(self, tmp_path):
        secrets_file = tmp_path / "fyers.json"
        secrets_file.write_text('{"dummy": true}')

        import pandas as pd

        mock_df = pd.DataFrame(
            {"timestamp": [1700000000], "open": [24000], "high": [24100],
             "low": [23900], "close": [24050], "volume": [10000]}
        )
        mock_cache = _make_cache_mock()
        mock_cache.get_candles.return_value = mock_df

        with (
            patch("quant.data.fyers.provider.FyersAuth"),
            patch("quant.data.fyers.provider.CandleCache", return_value=mock_cache),
        ):
            from quant.data.fyers.provider import FyersProvider
            provider = FyersProvider(
                secrets_path=str(secrets_file),
                cache_dir=str(tmp_path / "candles"),
            )

        result = await provider.get_candles("NSE:NIFTY50-INDEX", "D", 20)
        # reset_index produces a new object, so compare values not identity
        assert list(result["timestamp"]) == list(mock_df["timestamp"])
        assert list(result["close"]) == list(mock_df["close"])
        mock_cache.get_candles.assert_called_once()
