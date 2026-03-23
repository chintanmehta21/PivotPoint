"""Tests for Fyers REST client wrapper."""
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
import pytest
from quant.data.fyers.client import FyersClient
from quant.data.fyers.exceptions import FyersRateLimitError

@pytest.fixture
def mock_auth():
    auth = MagicMock()
    auth.get_valid_token.return_value = "test_token"
    auth._credentials = {"app_id": "TEST-100"}
    return auth

class TestFyersClientInit:
    def test_creates_fyers_model(self, mock_auth):
        with patch("quant.data.fyers.client.fyersModel") as mock_fm:
            client = FyersClient(mock_auth)
            mock_fm.FyersModel.assert_called_once()

class TestGetQuotes:
    @pytest.mark.asyncio
    async def test_single_batch(self, mock_auth):
        with patch("quant.data.fyers.client.fyersModel") as mock_fm:
            mock_model = MagicMock()
            mock_fm.FyersModel.return_value = mock_model
            mock_model.quotes.return_value = {"s": "ok", "d": [{"n": "NSE:NIFTY50-INDEX", "v": {"lp": 24000}}]}
            client = FyersClient(mock_auth)
            result = await client.get_quotes(["NSE:NIFTY50-INDEX"])
            assert result["s"] == "ok"

    @pytest.mark.asyncio
    async def test_batches_over_50_symbols(self, mock_auth):
        with patch("quant.data.fyers.client.fyersModel") as mock_fm:
            mock_model = MagicMock()
            mock_fm.FyersModel.return_value = mock_model
            mock_model.quotes.return_value = {"s": "ok", "d": []}
            client = FyersClient(mock_auth)
            symbols = [f"NSE:SYM{i}" for i in range(120)]
            result = await client.get_quotes(symbols)
            assert mock_model.quotes.call_count == 3  # 120/50 = 3

class TestGetHistory:
    @pytest.mark.asyncio
    async def test_returns_candle_data(self, mock_auth):
        with patch("quant.data.fyers.client.fyersModel") as mock_fm:
            mock_model = MagicMock()
            mock_fm.FyersModel.return_value = mock_model
            mock_model.history.return_value = {"s": "ok", "candles": [[1700000000, 24000, 24100, 23900, 24050, 1000000]]}
            client = FyersClient(mock_auth)
            result = await client.get_history("NSE:NIFTY50-INDEX", "1D", 1700000000, 1700100000)
            assert len(result["candles"]) == 1

class TestTokenRefresh:
    @pytest.mark.asyncio
    async def test_refreshes_on_expired_token(self, mock_auth):
        with patch("quant.data.fyers.client.fyersModel") as mock_fm:
            mock_model = MagicMock()
            mock_fm.FyersModel.return_value = mock_model
            mock_model.get_profile.side_effect = [
                {"s": "error", "message": "expired"},
                {"s": "ok", "data": {"name": "Test"}},
            ]
            mock_auth.get_valid_token.return_value = "new_token"
            client = FyersClient(mock_auth)
            result = await client.get_profile()
            assert result["s"] == "ok"
