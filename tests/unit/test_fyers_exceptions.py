"""Tests for Fyers exception hierarchy."""
import pytest

from quant.data.fyers.exceptions import (
    FyersError,
    FyersAuthError,
    FyersRateLimitError,
    FyersAPIError,
    FyersWebSocketError,
    FyersDataError,
)
from quant.utils.exceptions import PivotPointError


class TestFyersErrorInheritance:
    def test_fyers_error_inherits_pivotpoint(self):
        err = FyersError("test")
        assert isinstance(err, PivotPointError)

    def test_fyers_websocket_error(self):
        err = FyersWebSocketError("ws failed")
        assert isinstance(err, FyersError)

    def test_fyers_data_error(self):
        err = FyersDataError("data missing")
        assert isinstance(err, FyersError)


class TestFyersAuthError:
    def test_fyers_auth_error_includes_step(self):
        err = FyersAuthError(step=2, reason="OTP verification rejected")
        assert err.step == 2
        assert "Step 2" in str(err)

    def test_fyers_auth_error_includes_reason(self):
        err = FyersAuthError(step=1, reason="Invalid credentials")
        assert err.reason == "Invalid credentials"
        assert isinstance(err, FyersError)


class TestFyersRateLimitError:
    def test_fyers_rate_limit_error(self):
        err = FyersRateLimitError(limit_type="per_second", limit=10)
        assert err.limit_type == "per_second"
        assert err.limit == 10
        assert isinstance(err, FyersError)


class TestFyersAPIError:
    def test_fyers_api_error_includes_status_and_endpoint(self):
        err = FyersAPIError(status_code=400, endpoint="/quotes", message="Bad request")
        assert err.status_code == 400
        assert err.endpoint == "/quotes"
        assert "400" in str(err)
        assert isinstance(err, FyersError)


class TestReExports:
    def test_all_exceptions_importable_from_utils(self):
        from quant.utils.exceptions import (  # noqa: F401
            FyersError,
            FyersAuthError,
            FyersRateLimitError,
            FyersAPIError,
            FyersWebSocketError,
            FyersDataError,
        )
        # All imports succeeded
        assert FyersError is not None
        assert FyersAuthError is not None
        assert FyersRateLimitError is not None
        assert FyersAPIError is not None
        assert FyersWebSocketError is not None
        assert FyersDataError is not None
