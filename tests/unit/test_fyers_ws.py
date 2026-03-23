"""Tests for Fyers WebSocket manager."""
from datetime import datetime
from unittest.mock import MagicMock, patch
import pytest
from quant.data.fyers.ws import FyersWebSocket

@pytest.fixture
def mock_auth():
    auth = MagicMock()
    auth.get_valid_token.return_value = "test_token"
    auth._credentials = {"app_id": "TEST-100"}
    return auth

class TestFyersWebSocketInit:
    def test_initializes_state(self, mock_auth):
        ws = FyersWebSocket(mock_auth, on_price_update=MagicMock(), on_disconnect=MagicMock())
        assert ws.subscribed_symbols == set()
        assert ws.price_cache == {}
        assert not ws.is_connected()

class TestSubscribe:
    def test_tracks_subscribed_symbols(self, mock_auth):
        ws = FyersWebSocket(mock_auth, on_price_update=MagicMock(), on_disconnect=MagicMock())
        ws._connected = True
        ws._socket = MagicMock()
        ws.subscribe(["NSE:NIFTY50-INDEX", "NSE:NIFTYBANK-INDEX"])
        assert "NSE:NIFTY50-INDEX" in ws.subscribed_symbols

    def test_unsubscribe_removes_symbols(self, mock_auth):
        ws = FyersWebSocket(mock_auth, on_price_update=MagicMock(), on_disconnect=MagicMock())
        ws._connected = True
        ws._socket = MagicMock()
        ws.subscribe(["NSE:NIFTY50-INDEX", "NSE:NIFTYBANK-INDEX"])
        ws.unsubscribe(["NSE:NIFTY50-INDEX"])
        assert "NSE:NIFTY50-INDEX" not in ws.subscribed_symbols
        assert "NSE:NIFTYBANK-INDEX" in ws.subscribed_symbols

    def test_rejects_over_200_symbols(self, mock_auth):
        ws = FyersWebSocket(mock_auth, on_price_update=MagicMock(), on_disconnect=MagicMock())
        ws._connected = True
        ws._socket = MagicMock()
        with pytest.raises(ValueError, match="200"):
            ws.subscribe([f"NSE:SYM{i}" for i in range(201)])

class TestPriceCache:
    def test_on_message_updates_cache(self, mock_auth):
        callback = MagicMock()
        ws = FyersWebSocket(mock_auth, on_price_update=callback, on_disconnect=MagicMock())
        ws._handle_message({"symbol": "NSE:NIFTY50-INDEX", "ltp": 24000})
        assert ws.price_cache["NSE:NIFTY50-INDEX"]["ltp"] == 24000
        callback.assert_called_once()

    def test_tracks_last_update_time(self, mock_auth):
        ws = FyersWebSocket(mock_auth, on_price_update=MagicMock(), on_disconnect=MagicMock())
        ws._handle_message({"symbol": "NSE:NIFTY50-INDEX", "ltp": 24000})
        assert isinstance(ws.last_update["NSE:NIFTY50-INDEX"], datetime)
