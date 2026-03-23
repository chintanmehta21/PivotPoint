# Fyers Auth & Data Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement Fyers API v3 integration — headless auth, REST client, WebSocket streaming, vectorized Greeks engine, and parquet candle cache — fulfilling the `MarketDataProvider` Protocol.

**Architecture:** Layered provider in `src/quant/data/fyers/` with 9 focused modules: exceptions, symbols, auth, client, greeks, cache, websocket, provider orchestrator, and `__init__` re-exports. Each layer is independently testable. The provider composes all pieces and satisfies the Protocol.

**Tech Stack:** Python 3.11+, fyers-apiv3, NumPy (vectorized Greeks via stdlib `math.erf`, no scipy), pandas + pyarrow (candle cache), pytest + pytest-asyncio (testing), freezegun (time-dependent TOTP tests)

**Spec:** `docs/superpowers/specs/2026-03-22-fyers-auth-design.md`

---

## File Map

### New Files (Create)

| File | Responsibility |
|---|---|
| `src/quant/data/fyers/__init__.py` | Re-exports `FyersProvider` |
| `src/quant/data/fyers/exceptions.py` | `FyersError` hierarchy extending `PivotPointError` |
| `src/quant/data/fyers/symbols.py` | Fyers option symbol format build/parse |
| `src/quant/data/fyers/auth.py` | Headless TOTP login, token lifecycle |
| `src/quant/data/fyers/client.py` | Async REST wrapper with rate limiting |
| `src/quant/data/fyers/greeks.py` | Vectorized Black-Scholes IV + Greeks |
| `src/quant/data/fyers/cache.py` | Parquet-based incremental candle cache |
| `src/quant/data/fyers/ws.py` | WebSocket manager with reconnection |
| `src/quant/data/fyers/provider.py` | `FyersProvider` orchestrator |
| `tests/unit/test_fyers_exceptions.py` | Exception hierarchy tests |
| `tests/unit/test_fyers_symbols.py` | Symbol format tests |
| `tests/unit/test_fyers_auth.py` | Auth flow tests (mocked HTTP) |
| `tests/unit/test_fyers_client.py` | Client tests (mocked SDK) |
| `tests/unit/test_fyers_greeks.py` | Greeks engine numerical tests |
| `tests/unit/test_fyers_cache.py` | Candle cache tests (tmp dir) |
| `tests/unit/test_fyers_ws.py` | WebSocket manager tests (mocked SDK) |
| `tests/unit/test_fyers_provider.py` | Provider orchestration tests |

### Modified Files

| File | Change |
|---|---|
| `pyproject.toml` | Add `pyarrow` dependency |
| `.gitignore` | Add `data/candles/` |
| `src/quant/config/settings.py` | Replace `FyersSettings` credentials with operational config (incl. lot sizes) |
| `src/quant/data/provider.py` | Extend `MarketDataProvider` Protocol with new methods |
| `src/quant/utils/exceptions.py` | Re-export Fyers exceptions |

---

## Task 1: Add `pyarrow` Dependency

**Files:**
- Modify: `pyproject.toml:10-25`

- [ ] **Step 1: Add pyarrow to dependencies**

In `pyproject.toml`, add `"pyarrow>=15.0.0"` to the `dependencies` list after the `fyers-apiv3` line.

- [ ] **Step 2: Add `data/candles/` to .gitignore**

Append `data/candles/` to `.gitignore` so parquet cache files are not committed.

- [ ] **Step 3: Install**

Run: `pip install -e ".[dev]"`
Expected: All deps install including pyarrow

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml .gitignore
git commit -m "Add pyarrow dependency and gitignore candle cache"
```

---

## Task 2: Exceptions Module

**Files:**
- Create: `src/quant/data/fyers/exceptions.py`
- Create: `tests/unit/test_fyers_exceptions.py`
- Modify: `src/quant/utils/exceptions.py` (add re-exports)

- [ ] **Step 1: Write failing tests**

Create `tests/unit/test_fyers_exceptions.py`:

```python
"""Tests for Fyers exception hierarchy."""
from quant.data.fyers.exceptions import (
    FyersError,
    FyersAuthError,
    FyersRateLimitError,
    FyersAPIError,
    FyersWebSocketError,
    FyersDataError,
)
from quant.utils.exceptions import PivotPointError


def test_fyers_error_inherits_pivotpoint():
    err = FyersError("test")
    assert isinstance(err, PivotPointError)
    assert str(err) == "test"


def test_fyers_auth_error_includes_step():
    err = FyersAuthError(step=2, reason="OTP verification rejected")
    assert err.step == 2
    assert "Step 2" in str(err)
    assert "OTP verification rejected" in str(err)
    assert isinstance(err, FyersError)


def test_fyers_rate_limit_error():
    err = FyersRateLimitError(limit_type="per_second", limit=10)
    assert err.limit_type == "per_second"
    assert err.limit == 10
    assert isinstance(err, FyersError)


def test_fyers_api_error_includes_status_and_endpoint():
    err = FyersAPIError(status_code=400, endpoint="/quotes", message="Bad request")
    assert err.status_code == 400
    assert err.endpoint == "/quotes"
    assert "400" in str(err)
    assert isinstance(err, FyersError)


def test_fyers_websocket_error():
    err = FyersWebSocketError("Connection refused")
    assert isinstance(err, FyersError)


def test_fyers_data_error():
    err = FyersDataError("Missing premium for NIFTY2632724000CE")
    assert isinstance(err, FyersError)


def test_all_exceptions_importable_from_utils():
    """Verify re-exports work."""
    from quant.utils.exceptions import FyersError as FE
    assert FE is FyersError
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_fyers_exceptions.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'quant.data.fyers'`

- [ ] **Step 3: Create the fyers package and exceptions module**

Create `src/quant/data/fyers/__init__.py`:
```python
"""Fyers API v3 integration package."""
```

Create `src/quant/data/fyers/exceptions.py`:
```python
"""Fyers-specific exception hierarchy."""
from quant.utils.exceptions import PivotPointError


class FyersError(PivotPointError):
    """Base exception for all Fyers API errors."""
    pass


class FyersAuthError(FyersError):
    """Authentication flow failure."""
    def __init__(self, step: int, reason: str) -> None:
        self.step = step
        self.reason = reason
        super().__init__(f"Step {step} failed: {reason}")


class FyersRateLimitError(FyersError):
    """API rate limit exceeded."""
    def __init__(self, limit_type: str, limit: int) -> None:
        self.limit_type = limit_type
        self.limit = limit
        super().__init__(f"Rate limit exceeded: {limit_type} (limit={limit})")


class FyersAPIError(FyersError):
    """Non-200 REST API response."""
    def __init__(self, status_code: int, endpoint: str, message: str = "") -> None:
        self.status_code = status_code
        self.endpoint = endpoint
        super().__init__(f"API error {status_code} on {endpoint}: {message}")


class FyersWebSocketError(FyersError):
    """WebSocket connection or subscription failure."""
    pass


class FyersDataError(FyersError):
    """Missing or malformed market data."""
    pass
```

- [ ] **Step 4: Add re-exports to utils/exceptions.py**

Append to `src/quant/utils/exceptions.py`:
```python
# Fyers exceptions (re-exported for convenience)
from quant.data.fyers.exceptions import (  # noqa: F401
    FyersError,
    FyersAuthError,
    FyersRateLimitError,
    FyersAPIError,
    FyersWebSocketError,
    FyersDataError,
)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/unit/test_fyers_exceptions.py -v`
Expected: All 7 tests PASS

- [ ] **Step 6: Commit**

```bash
git add src/quant/data/fyers/__init__.py src/quant/data/fyers/exceptions.py src/quant/utils/exceptions.py tests/unit/test_fyers_exceptions.py
git commit -m "Add Fyers exception hierarchy extending PivotPointError"
```

---

## Task 3: Symbol Format Module

**Files:**
- Create: `src/quant/data/fyers/symbols.py`
- Create: `tests/unit/test_fyers_symbols.py`

- [ ] **Step 1: Write failing tests**

Create `tests/unit/test_fyers_symbols.py`:

```python
"""Tests for Fyers option symbol format construction and parsing."""
from datetime import date
import pytest

from quant.data.fyers.symbols import (
    build_option_symbol,
    build_chain_symbols,
    parse_option_symbol,
    MONTH_CODES,
    INDEX_SYMBOLS,
)
from quant.utils.types import Underlying


class TestMonthCodes:
    def test_jan_through_sep_are_digits(self):
        for i in range(1, 10):
            assert MONTH_CODES[i] == str(i)

    def test_oct_nov_dec_are_letters(self):
        assert MONTH_CODES[10] == "O"
        assert MONTH_CODES[11] == "N"
        assert MONTH_CODES[12] == "D"


class TestBuildOptionSymbol:
    def test_nifty_march_call(self):
        symbol = build_option_symbol(Underlying.NIFTY, date(2026, 3, 27), 24000, "CE")
        assert symbol == "NSE:NIFTY2632724000CE"

    def test_banknifty_november_put(self):
        symbol = build_option_symbol(Underlying.BANKNIFTY, date(2026, 11, 6), 52000, "PE")
        assert symbol == "NSE:BANKNIFTY26N0652000PE"

    def test_nifty_january_single_digit_day(self):
        symbol = build_option_symbol(Underlying.NIFTY, date(2026, 1, 8), 23500, "CE")
        assert symbol == "NSE:NIFTY2610823500CE"

    def test_nifty_october(self):
        symbol = build_option_symbol(Underlying.NIFTY, date(2026, 10, 15), 25000, "PE")
        assert symbol == "NSE:NIFTY26O1525000PE"

    def test_nifty_december(self):
        symbol = build_option_symbol(Underlying.NIFTY, date(2026, 12, 31), 26000, "CE")
        assert symbol == "NSE:NIFTY26D3126000CE"


class TestBuildChainSymbols:
    def test_nifty_chain_size(self):
        """ATM 24000 ± 500 at 50pt intervals = 21 strikes × 2 types = 42 symbols."""
        symbols = build_chain_symbols(Underlying.NIFTY, date(2026, 3, 27), 24000)
        assert len(symbols) == 42

    def test_banknifty_chain_size(self):
        """ATM 52000 ± 500 at 100pt intervals = 11 strikes × 2 types = 22 symbols."""
        symbols = build_chain_symbols(Underlying.BANKNIFTY, date(2026, 3, 27), 52000)
        assert len(symbols) == 22

    def test_chain_contains_atm(self):
        symbols = build_chain_symbols(Underlying.NIFTY, date(2026, 3, 27), 24000)
        assert "NSE:NIFTY2632724000CE" in symbols
        assert "NSE:NIFTY2632724000PE" in symbols

    def test_chain_contains_otm(self):
        symbols = build_chain_symbols(Underlying.NIFTY, date(2026, 3, 27), 24000)
        assert "NSE:NIFTY2632724500CE" in symbols
        assert "NSE:NIFTY2632723500PE" in symbols

    def test_custom_range_and_interval(self):
        symbols = build_chain_symbols(
            Underlying.NIFTY, date(2026, 3, 27), 24000,
            strike_range=200, strike_interval=100
        )
        # ±200 at 100pt = 5 strikes × 2 = 10
        assert len(symbols) == 10


class TestParseOptionSymbol:
    def test_roundtrip_nifty(self):
        original = "NSE:NIFTY2632724000CE"
        underlying, expiry, strike, opt_type = parse_option_symbol(original)
        assert underlying == Underlying.NIFTY
        assert expiry == date(2026, 3, 27)
        assert strike == 24000
        assert opt_type == "CE"

    def test_roundtrip_banknifty(self):
        original = "NSE:BANKNIFTY26N0652000PE"
        underlying, expiry, strike, opt_type = parse_option_symbol(original)
        assert underlying == Underlying.BANKNIFTY
        assert expiry == date(2026, 11, 6)
        assert strike == 52000
        assert opt_type == "PE"

    def test_build_then_parse_roundtrip(self):
        for month in range(1, 13):
            d = date(2026, month, 15)
            sym = build_option_symbol(Underlying.NIFTY, d, 24000, "CE")
            u, exp, s, t = parse_option_symbol(sym)
            assert u == Underlying.NIFTY
            assert exp == d
            assert s == 24000
            assert t == "CE"


class TestIndexSymbols:
    def test_nifty_index(self):
        assert INDEX_SYMBOLS[Underlying.NIFTY] == "NSE:NIFTY50-INDEX"

    def test_banknifty_index(self):
        assert INDEX_SYMBOLS[Underlying.BANKNIFTY] == "NSE:NIFTYBANK-INDEX"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_fyers_symbols.py -v`
Expected: FAIL — `ImportError`

- [ ] **Step 3: Implement symbols.py**

Create `src/quant/data/fyers/symbols.py`:

```python
"""Fyers option symbol format construction and parsing."""
from __future__ import annotations

import re
from datetime import date

from quant.utils.types import Underlying

# Month codes: 1-9 for Jan-Sep, O/N/D for Oct/Nov/Dec
MONTH_CODES: dict[int, str] = {
    1: "1", 2: "2", 3: "3", 4: "4", 5: "5",
    6: "6", 7: "7", 8: "8", 9: "9",
    10: "O", 11: "N", 12: "D",
}

_MONTH_CODE_REVERSE: dict[str, int] = {v: k for k, v in MONTH_CODES.items()}

# Underlying name in Fyers symbols
_UNDERLYING_NAMES: dict[Underlying, str] = {
    Underlying.NIFTY: "NIFTY",
    Underlying.BANKNIFTY: "BANKNIFTY",
}
_NAME_TO_UNDERLYING: dict[str, Underlying] = {v: k for k, v in _UNDERLYING_NAMES.items()}

# Index spot symbols (not options)
INDEX_SYMBOLS: dict[Underlying, str] = {
    Underlying.NIFTY: "NSE:NIFTY50-INDEX",
    Underlying.BANKNIFTY: "NSE:NIFTYBANK-INDEX",
}

VIX_SYMBOL = "NSE:INDIAVIX-INDEX"

# Default strike ranges from FyersSettings
_DEFAULT_RANGES: dict[Underlying, tuple[int, int]] = {
    Underlying.NIFTY: (500, 50),       # (range, interval)
    Underlying.BANKNIFTY: (500, 100),
}


def build_option_symbol(
    underlying: Underlying,
    expiry: date,
    strike: int,
    option_type: str,
) -> str:
    """Build a Fyers option symbol string.

    Format: NSE:{UNDERLYING}{YY}{M}{DD}{STRIKE}{CE|PE}
    """
    name = _UNDERLYING_NAMES[underlying]
    yy = f"{expiry.year % 100}"
    m = MONTH_CODES[expiry.month]
    dd = f"{expiry.day:02d}"
    return f"NSE:{name}{yy}{m}{dd}{strike}{option_type}"


def build_chain_symbols(
    underlying: Underlying,
    expiry: date,
    atm_strike: int,
    strike_range: int | None = None,
    strike_interval: int | None = None,
) -> list[str]:
    """Generate all option symbols for a chain around ATM.

    Returns CE + PE symbols for strikes from (ATM - range) to (ATM + range)
    at the given interval.
    """
    default_range, default_interval = _DEFAULT_RANGES[underlying]
    sr = strike_range if strike_range is not None else default_range
    si = strike_interval if strike_interval is not None else default_interval

    symbols: list[str] = []
    low = atm_strike - sr
    high = atm_strike + sr
    strike = low
    while strike <= high:
        symbols.append(build_option_symbol(underlying, expiry, strike, "CE"))
        symbols.append(build_option_symbol(underlying, expiry, strike, "PE"))
        strike += si
    return symbols


# Regex for parsing: NSE:{NAME}{YY}{M}{DD}{STRIKE}{TYPE}
_PARSE_RE = re.compile(
    r"^NSE:(?P<name>NIFTY|BANKNIFTY)"
    r"(?P<yy>\d{2})(?P<m>[1-9OND])(?P<dd>\d{2})"
    r"(?P<strike>\d+)(?P<type>CE|PE)$"
)


def parse_option_symbol(symbol: str) -> tuple[Underlying, date, int, str]:
    """Parse a Fyers option symbol into components.

    Returns: (underlying, expiry, strike, option_type)
    """
    match = _PARSE_RE.match(symbol)
    if not match:
        raise ValueError(f"Invalid Fyers option symbol: {symbol}")

    name = match.group("name")
    yy = int(match.group("yy"))
    m_code = match.group("m")
    dd = int(match.group("dd"))
    strike = int(match.group("strike"))
    opt_type = match.group("type")

    year = 2000 + yy
    month = _MONTH_CODE_REVERSE[m_code]
    expiry = date(year, month, dd)

    return _NAME_TO_UNDERLYING[name], expiry, strike, opt_type
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_fyers_symbols.py -v`
Expected: All 14 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/quant/data/fyers/symbols.py tests/unit/test_fyers_symbols.py
git commit -m "Add Fyers option symbol format builder and parser"
```

---

## Task 4: Update Settings

**Files:**
- Modify: `src/quant/config/settings.py:23-29`
- Create: `tests/unit/test_fyers_settings.py`

- [ ] **Step 1: Write failing test**

Create `tests/unit/test_fyers_settings.py`:

```python
"""Tests for updated FyersSettings."""
from quant.config.settings import FyersSettings


def test_fyers_settings_defaults():
    s = FyersSettings()
    assert s.secrets_path == "secrets/fyers"
    assert s.ws_max_symbols == 200
    assert s.quotes_batch_size == 50
    assert s.rate_limit_per_sec == 10
    assert s.rate_limit_per_min == 200
    assert s.risk_free_rate == 0.065
    assert s.cache_dir == "data/candles"
    assert s.strike_range_nifty == 500
    assert s.strike_interval_nifty == 50
    assert s.strike_range_banknifty == 500
    assert s.strike_interval_banknifty == 100
    assert s.lot_size_nifty == 75
    assert s.lot_size_banknifty == 15
    assert s.ws_reconnect_max_delay == 30


def test_fyers_settings_no_longer_has_credentials():
    s = FyersSettings()
    assert not hasattr(s, "app_id")
    assert not hasattr(s, "secret_key")
    assert not hasattr(s, "redirect_url")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_fyers_settings.py -v`
Expected: FAIL — `secrets_path` not found on old FyersSettings

- [ ] **Step 3: Replace FyersSettings in settings.py**

Replace the `FyersSettings` class in `src/quant/config/settings.py` (lines 23-29) with:

```python
class FyersSettings(BaseModel):
    """Fyers API operational configuration."""
    secrets_path: str = "secrets/fyers"
    ws_reconnect_max_delay: int = 30
    ws_max_symbols: int = 200
    quotes_batch_size: int = 50
    rate_limit_per_sec: int = 10
    rate_limit_per_min: int = 200
    risk_free_rate: float = 0.065
    cache_dir: str = "data/candles"
    strike_range_nifty: int = 500
    strike_interval_nifty: int = 50
    strike_range_banknifty: int = 500
    strike_interval_banknifty: int = 100
    lot_size_nifty: int = 75
    lot_size_banknifty: int = 15
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/unit/test_fyers_settings.py tests/unit/test_config.py -v`
Expected: All PASS (including existing config tests)

- [ ] **Step 5: Commit**

```bash
git add src/quant/config/settings.py tests/unit/test_fyers_settings.py
git commit -m "Update FyersSettings: credentials to secrets, add operational config"
```

---

## Task 5: Authentication Module

**Files:**
- Create: `src/quant/data/fyers/auth.py`
- Create: `tests/unit/test_fyers_auth.py`

- [ ] **Step 1: Write failing tests**

Create `tests/unit/test_fyers_auth.py`:

```python
"""Tests for Fyers headless TOTP authentication."""
import json
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from freezegun import freeze_time

from quant.data.fyers.auth import FyersAuth, generate_totp
from quant.data.fyers.exceptions import FyersAuthError


@pytest.fixture
def secrets_file(tmp_path):
    creds = {
        "app_id": "TEST123-100",
        "secret_key": "testsecret",
        "redirect_uri": "https://trade.fyers.in/api-login/redirect-uri/abc123",
        "fyers_id": "AB01234",
        "pin": "1234",
        "totp_key": "JBSWY3DPEHPK3PXP",  # standard test vector
    }
    path = tmp_path / "fyers"
    path.write_text(json.dumps(creds))
    return path


class TestGenerateTotp:
    @freeze_time("2026-01-01 00:00:00")
    def test_generates_6_digit_string(self):
        otp = generate_totp("JBSWY3DPEHPK3PXP")
        assert len(otp) == 6
        assert otp.isdigit()

    @freeze_time("2026-01-01 00:00:00")
    def test_deterministic_for_same_time(self):
        otp1 = generate_totp("JBSWY3DPEHPK3PXP")
        otp2 = generate_totp("JBSWY3DPEHPK3PXP")
        assert otp1 == otp2

    @freeze_time("2026-01-01 00:00:00")
    def test_different_keys_give_different_otps(self):
        otp1 = generate_totp("JBSWY3DPEHPK3PXP")
        otp2 = generate_totp("GEZDGNBVGY3TQOJQ")
        assert otp1 != otp2

    def test_handles_key_with_existing_padding(self):
        """Key already has = padding — should not crash."""
        otp = generate_totp("JBSWY3DPEHPK3PXP====")
        assert len(otp) == 6
        assert otp.isdigit()


class TestFyersAuthInit:
    def test_loads_credentials(self, secrets_file):
        auth = FyersAuth(secrets_file)
        assert auth._credentials["app_id"] == "TEST123-100"
        assert auth._credentials["fyers_id"] == "AB01234"

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            FyersAuth(tmp_path / "nonexistent")

    def test_invalid_json_raises(self, tmp_path):
        bad = tmp_path / "fyers"
        bad.write_text("not json")
        with pytest.raises(json.JSONDecodeError):
            FyersAuth(bad)


class TestFyersAuthAuthenticate:
    @patch("quant.data.fyers.auth.requests.Session")
    @patch("quant.data.fyers.auth.fyersModel.SessionModel")
    def test_successful_5_step_flow(self, mock_session_model_cls, mock_session_cls, secrets_file):
        """Mock the entire 5-step auth flow and verify calls."""
        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session

        # Step 1: send_login_otp_v2
        resp1 = MagicMock()
        resp1.json.return_value = {"request_key": "rk1"}
        # Step 2: verify_otp
        resp2 = MagicMock()
        resp2.status_code = 200
        resp2.json.return_value = {"request_key": "rk2"}
        # Step 3: verify_pin_v2
        resp3 = MagicMock()
        resp3.status_code = 200
        resp3.json.return_value = {"data": {"access_token": "intermediate_token"}}
        # Step 4: token endpoint
        resp4 = MagicMock()
        resp4.status_code = 308
        resp4.json.return_value = {"Url": "https://example.com?auth_code=AUTHCODE123&state=ok"}

        mock_session.post.side_effect = [resp1, resp2, resp3, resp4]

        # Step 5: SDK token exchange
        mock_sdk_session = MagicMock()
        mock_session_model_cls.return_value = mock_sdk_session
        mock_sdk_session.generate_token.return_value = {"access_token": "final_access_token_xyz"}

        auth = FyersAuth(secrets_file)
        token = auth.authenticate()

        assert token == "final_access_token_xyz"
        assert mock_session.post.call_count == 4
        mock_sdk_session.set_token.assert_called_once_with("AUTHCODE123")

    @patch("quant.data.fyers.auth.requests.Session")
    def test_step2_failure_raises_auth_error(self, mock_session_cls, secrets_file):
        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session

        resp1 = MagicMock()
        resp1.json.return_value = {"request_key": "rk1"}
        resp2 = MagicMock()
        resp2.status_code = 400
        resp2.json.return_value = {"message": "Invalid OTP"}
        resp2.text = "Invalid OTP"

        mock_session.post.side_effect = [resp1, resp2]

        auth = FyersAuth(secrets_file)
        with pytest.raises(FyersAuthError) as exc_info:
            auth.authenticate()
        assert exc_info.value.step == 2


class TestGetValidToken:
    @patch("quant.data.fyers.auth.requests.Session")
    @patch("quant.data.fyers.auth.fyersModel")
    def test_returns_cached_token_if_valid(self, mock_fyers, mock_sess_cls, secrets_file):
        auth = FyersAuth(secrets_file)
        auth._cached_token = "cached_token"

        mock_model = MagicMock()
        mock_fyers.FyersModel.return_value = mock_model
        mock_model.get_profile.return_value = {"s": "ok", "message": ""}

        token = auth.get_valid_token()
        assert token == "cached_token"

    @patch.object(FyersAuth, "authenticate", return_value="new_token")
    @patch("quant.data.fyers.auth.fyersModel")
    def test_reauthenticates_if_expired(self, mock_fyers, mock_auth, secrets_file):
        auth = FyersAuth(secrets_file)
        auth._cached_token = "old_token"

        mock_model = MagicMock()
        mock_fyers.FyersModel.return_value = mock_model
        mock_model.get_profile.return_value = {"s": "error", "message": "expired"}

        token = auth.get_valid_token()
        assert token == "new_token"
        mock_auth.assert_called_once()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_fyers_auth.py -v`
Expected: FAIL — `ImportError`

- [ ] **Step 3: Implement auth.py**

Create `src/quant/data/fyers/auth.py`:

```python
"""Headless TOTP authentication for Fyers API v3."""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import struct
import time
from pathlib import Path
from urllib.parse import urlparse, parse_qs

import requests
from fyers_apiv3 import fyersModel

from quant.data.fyers.exceptions import FyersAuthError


def generate_totp(key: str, time_step: int = 30, digits: int = 6) -> str:
    """Generate a TOTP code (RFC 6238) from a base32 secret key."""
    key = key.rstrip("=")
    key_bytes = base64.b32decode(key.upper() + "=" * ((8 - len(key)) % 8))
    counter = struct.pack(">Q", int(time.time() / time_step))
    mac = hmac.new(key_bytes, counter, hashlib.sha1).digest()
    offset = mac[-1] & 0x0F
    binary = struct.unpack(">L", mac[offset:offset + 4])[0] & 0x7FFFFFFF
    return str(binary)[-digits:].zfill(digits)


class FyersAuth:
    """Manages Fyers API authentication with headless TOTP login."""

    def __init__(self, secrets_path: Path) -> None:
        with open(secrets_path) as f:
            self._credentials: dict[str, str] = json.load(f)
        self._cached_token: str | None = None

    def authenticate(self) -> str:
        """Run the full 5-step headless login flow. Returns access_token."""
        creds = self._credentials
        s = requests.Session()
        s.headers.update({
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        })

        # Step 1: Send OTP
        fy_id_b64 = base64.b64encode(creds["fyers_id"].encode()).decode()
        data1 = json.dumps({"fy_id": fy_id_b64, "app_id": "2"})
        r1 = s.post("https://api-t2.fyers.in/vagator/v2/send_login_otp_v2", data=data1)
        request_key = r1.json().get("request_key")
        if not request_key:
            raise FyersAuthError(step=1, reason=f"No request_key: {r1.text}")

        # Step 2: Verify OTP with TOTP
        otp = generate_totp(creds["totp_key"])
        data2 = json.dumps({"request_key": request_key, "otp": otp})
        r2 = s.post("https://api-t2.fyers.in/vagator/v2/verify_otp", data=data2)
        if r2.status_code != 200:
            raise FyersAuthError(step=2, reason=f"OTP verification failed: {r2.text}")
        request_key = r2.json()["request_key"]

        # Step 3: Verify PIN
        pin_b64 = base64.b64encode(str(creds["pin"]).encode()).decode()
        data3 = json.dumps({
            "request_key": request_key,
            "identity_type": "pin",
            "identifier": pin_b64,
        })
        r3 = s.post("https://api-t2.fyers.in/vagator/v2/verify_pin_v2", data=data3)
        if r3.status_code != 200:
            raise FyersAuthError(step=3, reason=f"PIN verification failed: {r3.text}")
        intermediate_token = r3.json()["data"]["access_token"]

        # Step 4: Get auth code
        app_id_prefix = creds["app_id"][:-4]  # strip "-100"
        data4 = json.dumps({
            "fyers_id": creds["fyers_id"],
            "app_id": app_id_prefix,
            "redirect_uri": creds["redirect_uri"],
            "appType": "100",
            "code_challenge": "",
            "state": "abcdefg",
            "scope": "",
            "nonce": "",
            "response_type": "code",
            "create_cookie": True,
        })
        r4 = s.post(
            "https://api.fyers.in/api/v2/token",
            headers={
                "authorization": f"Bearer {intermediate_token}",
                "content-type": "application/json; charset=UTF-8",
            },
            data=data4,
        )
        if r4.status_code != 308:
            raise FyersAuthError(step=4, reason=f"Expected 308, got {r4.status_code}: {r4.text}")
        parsed = urlparse(r4.json()["Url"])
        auth_code = parse_qs(parsed.query)["auth_code"][0]

        # Step 5: Exchange auth code for access token via SDK
        session = fyersModel.SessionModel(
            client_id=creds["app_id"],
            secret_key=creds["secret_key"],
            redirect_uri=creds["redirect_uri"],
            response_type="code",
            grant_type="authorization_code",
        )
        session.set_token(auth_code)
        response = session.generate_token()
        token = response["access_token"]

        self._cached_token = token
        return token

    def get_valid_token(self) -> str:
        """Return a valid access token, re-authenticating if needed."""
        if self._cached_token:
            try:
                fyers = fyersModel.FyersModel(
                    client_id=self._credentials["app_id"],
                    token=self._cached_token,
                    is_async=False,
                    log_path="",
                )
                resp = fyers.get_profile()
                if resp.get("s") == "ok" and "error" not in resp.get("message", "").lower():
                    return self._cached_token
            except (ConnectionError, KeyError, TypeError):
                pass  # token invalid or network unreachable — re-authenticate

        return self.authenticate()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_fyers_auth.py -v`
Expected: All 9 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/quant/data/fyers/auth.py tests/unit/test_fyers_auth.py
git commit -m "Add headless TOTP auth with 5-step login flow and token lifecycle"
```

---

## Task 6: Greeks Engine

**Files:**
- Create: `src/quant/data/fyers/greeks.py`
- Create: `tests/unit/test_fyers_greeks.py`

- [ ] **Step 1: Write failing tests**

Create `tests/unit/test_fyers_greeks.py`:

```python
"""Tests for vectorized Black-Scholes Greeks engine."""
import numpy as np
import pytest

from quant.data.fyers.greeks import black_scholes_price, compute_iv, compute_greeks


class TestBlackScholesPrice:
    def test_atm_call_price_reasonable(self):
        """ATM call with 30d expiry, 20% IV should be ~2-4% of spot."""
        prices = black_scholes_price(
            spots=np.array([24000.0]),
            strikes=np.array([24000.0]),
            T=np.array([30 / 365]),
            ivs=np.array([0.20]),
            r=0.065,
            option_types=np.array([1]),  # 1=call
        )
        assert 300 < prices[0] < 1000  # ~1.5-4% of spot

    def test_deep_itm_call_near_intrinsic(self):
        prices = black_scholes_price(
            spots=np.array([24000.0]),
            strikes=np.array([22000.0]),
            T=np.array([30 / 365]),
            ivs=np.array([0.20]),
            r=0.065,
            option_types=np.array([1]),
        )
        assert prices[0] > 2000  # at least intrinsic

    def test_deep_otm_put_near_zero(self):
        prices = black_scholes_price(
            spots=np.array([24000.0]),
            strikes=np.array([22000.0]),
            T=np.array([5 / 365]),
            ivs=np.array([0.15]),
            r=0.065,
            option_types=np.array([-1]),  # -1=put
        )
        assert prices[0] < 10

    def test_vectorized_multiple_contracts(self):
        spots = np.full(5, 24000.0)
        strikes = np.array([23500, 23750, 24000, 24250, 24500], dtype=float)
        T = np.full(5, 30 / 365)
        ivs = np.full(5, 0.18)
        types = np.ones(5)
        prices = black_scholes_price(spots, strikes, T, ivs, 0.065, types)
        assert len(prices) == 5
        # lower strikes should have higher call prices
        assert prices[0] > prices[-1]

    def test_put_call_parity(self):
        """C - P ≈ S - K*exp(-rT) for same strike."""
        S, K, T_val, iv, r = 24000.0, 24000.0, 30 / 365, 0.20, 0.065
        call = black_scholes_price(
            np.array([S]), np.array([K]), np.array([T_val]),
            np.array([iv]), r, np.array([1]),
        )[0]
        put = black_scholes_price(
            np.array([S]), np.array([K]), np.array([T_val]),
            np.array([iv]), r, np.array([-1]),
        )[0]
        parity = S - K * np.exp(-r * T_val)
        assert abs((call - put) - parity) < 1.0  # within ₹1


class TestComputeIV:
    def test_recovers_known_iv(self):
        """Price with known IV, then recover it."""
        spot, strike, T_val, known_iv, r = 24000.0, 24000.0, 30 / 365, 0.20, 0.065
        price = black_scholes_price(
            np.array([spot]), np.array([strike]), np.array([T_val]),
            np.array([known_iv]), r, np.array([1]),
        )
        recovered = compute_iv(
            premiums=price,
            spots=np.array([spot]),
            strikes=np.array([strike]),
            T=np.array([T_val]),
            option_types=np.array([1]),
            r=r,
        )
        assert abs(recovered[0] - known_iv) < 1e-4

    def test_deep_otm_near_zero_premium_returns_zero_iv(self):
        iv = compute_iv(
            premiums=np.array([0.01]),
            spots=np.array([24000.0]),
            strikes=np.array([28000.0]),
            T=np.array([5 / 365]),
            option_types=np.array([1]),
            r=0.065,
        )
        assert iv[0] == 0.0

    def test_vectorized_iv_recovery(self):
        n = 20
        spots = np.full(n, 24000.0)
        strikes = np.linspace(23000, 25000, n)
        T = np.full(n, 30 / 365)
        known_ivs = np.full(n, 0.18)
        types = np.ones(n)
        prices = black_scholes_price(spots, strikes, T, known_ivs, 0.065, types)
        recovered = compute_iv(prices, spots, strikes, T, types, 0.065)
        np.testing.assert_allclose(recovered, known_ivs, atol=1e-4)


class TestComputeGreeks:
    def test_atm_call_delta_near_0_5(self):
        greeks = compute_greeks(
            spots=np.array([24000.0]),
            strikes=np.array([24000.0]),
            T=np.array([30 / 365]),
            ivs=np.array([0.20]),
            option_types=np.array([1]),
            r=0.065,
        )
        assert 0.45 < greeks["delta"][0] < 0.65

    def test_atm_put_delta_near_neg_0_5(self):
        greeks = compute_greeks(
            spots=np.array([24000.0]),
            strikes=np.array([24000.0]),
            T=np.array([30 / 365]),
            ivs=np.array([0.20]),
            option_types=np.array([-1]),
            r=0.065,
        )
        assert -0.65 < greeks["delta"][0] < -0.45

    def test_gamma_positive(self):
        greeks = compute_greeks(
            spots=np.array([24000.0]),
            strikes=np.array([24000.0]),
            T=np.array([30 / 365]),
            ivs=np.array([0.20]),
            option_types=np.array([1]),
            r=0.065,
        )
        assert greeks["gamma"][0] > 0

    def test_vega_positive(self):
        greeks = compute_greeks(
            spots=np.array([24000.0]),
            strikes=np.array([24000.0]),
            T=np.array([30 / 365]),
            ivs=np.array([0.20]),
            option_types=np.array([1]),
            r=0.065,
        )
        assert greeks["vega"][0] > 0

    def test_theta_negative_for_long(self):
        greeks = compute_greeks(
            spots=np.array([24000.0]),
            strikes=np.array([24000.0]),
            T=np.array([30 / 365]),
            ivs=np.array([0.20]),
            option_types=np.array([1]),
            r=0.065,
        )
        assert greeks["theta"][0] < 0

    def test_returns_all_four_greeks(self):
        greeks = compute_greeks(
            spots=np.array([24000.0]),
            strikes=np.array([24000.0]),
            T=np.array([30 / 365]),
            ivs=np.array([0.20]),
            option_types=np.array([1]),
            r=0.065,
        )
        assert set(greeks.keys()) == {"delta", "gamma", "vega", "theta"}

    def test_vectorized_20_contracts(self):
        n = 20
        greeks = compute_greeks(
            spots=np.full(n, 24000.0),
            strikes=np.linspace(23000, 25000, n),
            T=np.full(n, 30 / 365),
            ivs=np.full(n, 0.18),
            option_types=np.ones(n),
            r=0.065,
        )
        assert all(len(v) == n for v in greeks.values())
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_fyers_greeks.py -v`
Expected: FAIL — `ImportError`

- [ ] **Step 3: Implement greeks.py**

Create `src/quant/data/fyers/greeks.py`:

```python
"""Vectorized Black-Scholes Greeks engine using NumPy (no scipy dependency)."""
from __future__ import annotations

import numpy as np
from math import pi, sqrt as _sqrt

# Normal distribution functions using NumPy + stdlib erf (no scipy needed)
_INV_SQRT_2PI = 1.0 / _sqrt(2.0 * pi)


def _norm_cdf(x: np.ndarray) -> np.ndarray:
    """Standard normal CDF via error function."""
    return 0.5 * (1.0 + np.vectorize(np.erf)(x / _sqrt(2.0)))


def _norm_pdf(x: np.ndarray) -> np.ndarray:
    """Standard normal PDF."""
    return _INV_SQRT_2PI * np.exp(-0.5 * x * x)


def black_scholes_price(
    spots: np.ndarray,
    strikes: np.ndarray,
    T: np.ndarray,
    ivs: np.ndarray,
    r: float,
    option_types: np.ndarray,
) -> np.ndarray:
    """Compute Black-Scholes prices. option_types: 1=call, -1=put."""
    d1 = (np.log(spots / strikes) + (r + 0.5 * ivs**2) * T) / (ivs * np.sqrt(T))
    d2 = d1 - ivs * np.sqrt(T)

    call_price = spots * _norm_cdf(d1) - strikes * np.exp(-r * T) * _norm_cdf(d2)
    put_price = strikes * np.exp(-r * T) * _norm_cdf(-d2) - spots * _norm_cdf(-d1)

    return np.where(option_types == 1, call_price, put_price)


def compute_iv(
    premiums: np.ndarray,
    spots: np.ndarray,
    strikes: np.ndarray,
    T: np.ndarray,
    option_types: np.ndarray,
    r: float = 0.065,
    tol: float = 1e-6,
    max_iter: int = 50,
) -> np.ndarray:
    """Newton-Raphson IV solver, vectorized across entire chain."""
    # Filter out near-zero premiums (deep OTM)
    near_zero = premiums < 0.05
    iv = np.full_like(premiums, 0.20)  # initial guess 20%
    iv[near_zero] = 0.0

    mask = ~near_zero  # only solve for non-trivial premiums
    if not mask.any():
        return iv

    iv_m = iv[mask]
    for _ in range(max_iter):
        prices = black_scholes_price(spots[mask], strikes[mask], T[mask], iv_m, r, option_types[mask])
        diff = prices - premiums[mask]

        # Vega for Newton step
        d1 = (np.log(spots[mask] / strikes[mask]) + (r + 0.5 * iv_m**2) * T[mask]) / (iv_m * np.sqrt(T[mask]))
        vega = spots[mask] * _norm_pdf(d1) * np.sqrt(T[mask])

        # Avoid division by zero
        vega = np.maximum(vega, 1e-10)
        iv_m = iv_m - diff / vega
        iv_m = np.clip(iv_m, 0.001, 5.0)  # bound IV to reasonable range

        if np.all(np.abs(diff) < tol):
            break

    iv[mask] = iv_m
    # Zero out any that didn't converge to reasonable values
    iv[iv < 0.001] = 0.0
    return iv


def compute_greeks(
    spots: np.ndarray,
    strikes: np.ndarray,
    T: np.ndarray,
    ivs: np.ndarray,
    option_types: np.ndarray,
    r: float = 0.065,
) -> dict[str, np.ndarray]:
    """Compute delta, gamma, vega, theta for European options. Vectorized."""
    sqrt_T = np.sqrt(T)
    d1 = (np.log(spots / strikes) + (r + 0.5 * ivs**2) * T) / (ivs * sqrt_T)
    d2 = d1 - ivs * sqrt_T

    nd1 = _norm_pdf(d1)
    Nd1 = _norm_cdf(d1)
    Nd2 = _norm_cdf(d2)

    # Delta
    delta = np.where(option_types == 1, Nd1, Nd1 - 1)

    # Gamma (same for calls and puts)
    gamma = nd1 / (spots * ivs * sqrt_T)

    # Vega (per 1% IV move = divide by 100)
    vega = spots * nd1 * sqrt_T / 100

    # Theta (per day = divide by 365)
    theta_common = -(spots * nd1 * ivs) / (2 * sqrt_T)
    call_theta = theta_common - r * strikes * np.exp(-r * T) * Nd2
    put_theta = theta_common + r * strikes * np.exp(-r * T) * _norm_cdf(-d2)
    theta = np.where(option_types == 1, call_theta, put_theta) / 365

    return {"delta": delta, "gamma": gamma, "vega": vega, "theta": theta}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_fyers_greeks.py -v`
Expected: All 13 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/quant/data/fyers/greeks.py tests/unit/test_fyers_greeks.py
git commit -m "Add vectorized Black-Scholes Greeks engine with IV solver (NumPy only)"
```

---

## Task 7: REST Client

**Files:**
- Create: `src/quant/data/fyers/client.py`
- Create: `tests/unit/test_fyers_client.py`

- [ ] **Step 1: Write failing tests**

Create `tests/unit/test_fyers_client.py`:

```python
"""Tests for Fyers REST client wrapper."""
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock

import pytest
import pytest_asyncio

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
            mock_model.quotes.return_value = {
                "s": "ok",
                "d": [{"n": "NSE:NIFTY50-INDEX", "v": {"lp": 24000}}],
            }
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

            # 120 / 50 = 3 batches
            assert mock_model.quotes.call_count == 3


class TestGetHistory:
    @pytest.mark.asyncio
    async def test_returns_candle_data(self, mock_auth):
        with patch("quant.data.fyers.client.fyersModel") as mock_fm:
            mock_model = MagicMock()
            mock_fm.FyersModel.return_value = mock_model
            mock_model.history.return_value = {
                "s": "ok",
                "candles": [[1700000000, 24000, 24100, 23900, 24050, 1000000]],
            }
            client = FyersClient(mock_auth)
            result = await client.get_history("NSE:NIFTY50-INDEX", "1D", 1700000000, 1700100000)
            assert result["s"] == "ok"
            assert len(result["candles"]) == 1


class TestRateLimiting:
    @pytest.mark.asyncio
    async def test_tracks_call_count(self, mock_auth):
        with patch("quant.data.fyers.client.fyersModel") as mock_fm:
            mock_model = MagicMock()
            mock_fm.FyersModel.return_value = mock_model
            mock_model.get_profile.return_value = {"s": "ok"}

            client = FyersClient(mock_auth)
            await client.get_profile()
            assert client._call_count_sec >= 1


class TestTokenRefresh:
    @pytest.mark.asyncio
    async def test_refreshes_on_expired_token(self, mock_auth):
        with patch("quant.data.fyers.client.fyersModel") as mock_fm:
            mock_model = MagicMock()
            mock_fm.FyersModel.return_value = mock_model

            # First call returns expired, second returns ok
            mock_model.get_profile.side_effect = [
                {"s": "error", "message": "expired"},
                {"s": "ok", "data": {"name": "Test"}},
            ]
            mock_auth.get_valid_token.return_value = "new_token"

            client = FyersClient(mock_auth)
            result = await client.get_profile()
            assert result["s"] == "ok"
            assert mock_auth.get_valid_token.call_count >= 2  # initial + refresh
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_fyers_client.py -v`
Expected: FAIL — `ImportError`

- [ ] **Step 3: Implement client.py**

Create `src/quant/data/fyers/client.py`:

```python
"""Async REST client wrapper for Fyers API v3."""
from __future__ import annotations

import asyncio
import time
from collections import deque

from fyers_apiv3 import fyersModel

from quant.data.fyers.auth import FyersAuth
from quant.data.fyers.exceptions import FyersAPIError, FyersRateLimitError

_BATCH_SIZE = 50


class FyersClient:
    """Thin async wrapper around fyersModel.FyersModel with rate limiting."""

    def __init__(self, auth: FyersAuth, batch_size: int = _BATCH_SIZE) -> None:
        self._auth = auth
        self._batch_size = batch_size
        self._token = auth.get_valid_token()
        self._model = self._build_model(self._token)
        self._call_timestamps: deque[float] = deque()
        self._call_count_sec = 0

    def _build_model(self, token: str) -> fyersModel.FyersModel:
        return fyersModel.FyersModel(
            client_id=self._auth._credentials["app_id"],
            token=token,
            is_async=False,
            log_path="",
        )

    async def _throttle(self) -> None:
        """Enforce rate limits: 10/sec, 200/min."""
        now = time.monotonic()
        # Prune old timestamps
        while self._call_timestamps and self._call_timestamps[0] < now - 60:
            self._call_timestamps.popleft()

        # Check per-minute
        if len(self._call_timestamps) >= 180:
            wait = 60 - (now - self._call_timestamps[0])
            if wait > 0:
                await asyncio.sleep(wait)

        # Check per-second
        recent = sum(1 for t in self._call_timestamps if t > now - 1)
        if recent >= 8:
            await asyncio.sleep(1.0 - (now - self._call_timestamps[-1]))

        self._call_timestamps.append(time.monotonic())
        self._call_count_sec = sum(1 for t in self._call_timestamps if t > time.monotonic() - 1)

    async def _call(self, method: str, *args, **kwargs) -> dict:
        """Execute a Fyers SDK call with throttling and token refresh."""
        await self._throttle()
        fn = getattr(self._model, method)
        result = await asyncio.to_thread(fn, *args, **kwargs)

        # Check for expired token
        if isinstance(result, dict) and result.get("s") == "error":
            msg = result.get("message", "").lower()
            if "expired" in msg or "invalid token" in msg:
                self._token = self._auth.get_valid_token()
                self._model = self._build_model(self._token)
                await self._throttle()
                fn = getattr(self._model, method)
                result = await asyncio.to_thread(fn, *args, **kwargs)

        return result

    async def get_quotes(self, symbols: list[str]) -> dict:
        """Batch quotes for multiple symbols (auto-chunks at batch_size)."""
        all_data: list[dict] = []
        for i in range(0, len(symbols), self._batch_size):
            batch = symbols[i:i + self._batch_size]
            data = {"symbols": ",".join(batch)}
            result = await self._call("quotes", data=data)
            if result.get("d"):
                all_data.extend(result["d"])
        return {"s": "ok", "d": all_data}

    async def get_history(self, symbol: str, resolution: str, from_ts: int, to_ts: int) -> dict:
        data = {
            "symbol": symbol,
            "resolution": resolution,
            "date_format": "0",
            "range_from": str(from_ts),
            "range_to": str(to_ts),
            "cont_flag": "1",
        }
        return await self._call("history", data=data)

    async def get_market_depth(self, symbol: str) -> dict:
        return await self._call("depth", data={"symbol": symbol, "ohlcv_flag": "1"})

    async def get_profile(self) -> dict:
        return await self._call("get_profile")

    async def get_funds(self) -> dict:
        return await self._call("funds")

    async def get_positions(self) -> dict:
        return await self._call("positions")

    async def get_holdings(self) -> dict:
        return await self._call("holdings")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_fyers_client.py -v`
Expected: All 6 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/quant/data/fyers/client.py tests/unit/test_fyers_client.py
git commit -m "Add async Fyers REST client with rate limiting and batch quotes"
```

---

## Task 8: Candle Cache

**Files:**
- Create: `src/quant/data/fyers/cache.py`
- Create: `tests/unit/test_fyers_cache.py`

- [ ] **Step 1: Write failing tests**

Create `tests/unit/test_fyers_cache.py`:

```python
"""Tests for parquet-based candle cache."""
from datetime import date
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pandas as pd
import pytest
import pytest_asyncio

from quant.data.fyers.cache import CandleCache


@pytest.fixture
def cache(tmp_path):
    return CandleCache(cache_dir=tmp_path)


@pytest.fixture
def sample_candles():
    """Fyers history() response format: [timestamp, open, high, low, close, volume]."""
    return {
        "s": "ok",
        "candles": [
            [1711324800, 24000, 24100, 23900, 24050, 1000000],  # 2024-03-25
            [1711411200, 24050, 24200, 24000, 24150, 900000],   # 2024-03-26
        ],
    }


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
        # Write some test data
        df = pd.DataFrame({
            "timestamp": [1711324800, 1711411200],
            "open": [24000, 24050],
            "high": [24100, 24200],
            "low": [23900, 24000],
            "close": [24050, 24150],
            "volume": [1000000, 900000],
        })
        df["date"] = pd.to_datetime(df["timestamp"], unit="s").dt.date
        path = tmp_path / "NIFTY50_D.parquet"
        df.to_parquet(path, index=False)

        result = cache.get_candles("NIFTY50", "D", date(2024, 3, 25), date(2024, 3, 26))
        assert len(result) == 2
        assert "close" in result.columns


class TestBackfill:
    @pytest.mark.asyncio
    async def test_writes_parquet_file(self, cache, tmp_path, sample_candles):
        mock_client = AsyncMock()
        mock_client.get_history.return_value = sample_candles

        await cache.backfill("NIFTY50", "D", 365, mock_client)

        path = tmp_path / "NIFTY50_D.parquet"
        assert path.exists()
        df = pd.read_parquet(path)
        assert len(df) == 2


class TestUpdate:
    @pytest.mark.asyncio
    async def test_appends_new_candles(self, cache, tmp_path, sample_candles):
        # Pre-populate with one candle
        df = pd.DataFrame({
            "timestamp": [1711324800],
            "open": [24000], "high": [24100], "low": [23900],
            "close": [24050], "volume": [1000000],
            "date": [date(2024, 3, 25)],
        })
        path = tmp_path / "NIFTY50_D.parquet"
        df.to_parquet(path, index=False)

        mock_client = AsyncMock()
        mock_client.get_history.return_value = {
            "s": "ok",
            "candles": [[1711411200, 24050, 24200, 24000, 24150, 900000]],
        }

        await cache.update("NIFTY50", "D", mock_client)

        updated = pd.read_parquet(path)
        assert len(updated) == 2

    @pytest.mark.asyncio
    async def test_noop_when_no_new_data(self, cache, tmp_path):
        df = pd.DataFrame({
            "timestamp": [1711324800],
            "open": [24000], "high": [24100], "low": [23900],
            "close": [24050], "volume": [1000000],
            "date": [date(2024, 3, 25)],
        })
        path = tmp_path / "NIFTY50_D.parquet"
        df.to_parquet(path, index=False)

        mock_client = AsyncMock()
        mock_client.get_history.return_value = {"s": "ok", "candles": []}

        await cache.update("NIFTY50", "D", mock_client)
        assert len(pd.read_parquet(path)) == 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_fyers_cache.py -v`
Expected: FAIL — `ImportError`

- [ ] **Step 3: Implement cache.py**

Create `src/quant/data/fyers/cache.py`:

```python
"""Parquet-based incremental candle cache."""
from __future__ import annotations

import time
from datetime import date
from pathlib import Path

import pandas as pd

from quant.data.fyers.client import FyersClient

# Resolution mapping to Fyers format
_RESOLUTION_MAP = {"D": "1D", "W": "1W"}


class CandleCache:
    """Local parquet cache for historical OHLCV candle data."""

    def __init__(self, cache_dir: Path = Path("data/candles")) -> None:
        self._dir = Path(cache_dir)
        self._dir.mkdir(parents=True, exist_ok=True)

    def _path(self, symbol: str, resolution: str) -> Path:
        # NSE:NIFTY50-INDEX → NIFTY50, NSE:NIFTYBANK-INDEX → NIFTYBANK
        clean = symbol.replace("NSE:", "").replace("-INDEX", "").replace("-EQ", "").replace("-", "")
        return self._dir / f"{clean}_{resolution}.parquet"

    def get_candles(
        self,
        symbol: str,
        resolution: str,
        from_date: date,
        to_date: date,
    ) -> pd.DataFrame:
        """Read candles from local cache. Sync — no network I/O."""
        path = self._path(symbol, resolution)
        if not path.exists():
            return pd.DataFrame()

        df = pd.read_parquet(path)
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"]).dt.date
            mask = (df["date"] >= from_date) & (df["date"] <= to_date)
            return df[mask].reset_index(drop=True)
        return df

    async def backfill(
        self,
        symbol: str,
        resolution: str,
        days_back: int,
        client: FyersClient,
    ) -> None:
        """Full historical fetch and cache write."""
        fyers_res = _RESOLUTION_MAP.get(resolution, resolution)
        to_ts = int(time.time())
        from_ts = to_ts - (days_back * 86400)

        result = await client.get_history(symbol, fyers_res, from_ts, to_ts)
        candles = result.get("candles", [])
        if not candles:
            return

        df = pd.DataFrame(candles, columns=["timestamp", "open", "high", "low", "close", "volume"])
        df["date"] = pd.to_datetime(df["timestamp"], unit="s").dt.date
        df.to_parquet(self._path(symbol, resolution), index=False)

    async def update(
        self,
        symbol: str,
        resolution: str,
        client: FyersClient,
    ) -> None:
        """Incremental update — fetch only new candles since last cached date."""
        path = self._path(symbol, resolution)
        if not path.exists():
            await self.backfill(symbol, resolution, 365, client)
            return

        existing = pd.read_parquet(path)
        if existing.empty:
            await self.backfill(symbol, resolution, 365, client)
            return

        last_ts = int(existing["timestamp"].max())
        from_ts = last_ts + 1
        to_ts = int(time.time())

        fyers_res = _RESOLUTION_MAP.get(resolution, resolution)
        result = await client.get_history(symbol, fyers_res, from_ts, to_ts)
        candles = result.get("candles", [])
        if not candles:
            return

        new_df = pd.DataFrame(candles, columns=["timestamp", "open", "high", "low", "close", "volume"])
        new_df["date"] = pd.to_datetime(new_df["timestamp"], unit="s").dt.date
        combined = pd.concat([existing, new_df], ignore_index=True)
        combined.drop_duplicates(subset=["timestamp"], inplace=True)
        combined.sort_values("timestamp", inplace=True)
        combined.to_parquet(path, index=False)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_fyers_cache.py -v`
Expected: All 6 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/quant/data/fyers/cache.py tests/unit/test_fyers_cache.py
git commit -m "Add parquet-based incremental candle cache"
```

---

## Task 9: WebSocket Manager

**Files:**
- Create: `src/quant/data/fyers/ws.py`
- Create: `tests/unit/test_fyers_ws.py`

- [ ] **Step 1: Write failing tests**

Create `tests/unit/test_fyers_ws.py`:

```python
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
        assert "NSE:NIFTYBANK-INDEX" in ws.subscribed_symbols

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
        symbols = [f"NSE:SYM{i}" for i in range(201)]
        with pytest.raises(ValueError, match="200"):
            ws.subscribe(symbols)


class TestPriceCache:
    def test_on_message_updates_cache(self, mock_auth):
        callback = MagicMock()
        ws = FyersWebSocket(mock_auth, on_price_update=callback, on_disconnect=MagicMock())
        msg = {"symbol": "NSE:NIFTY50-INDEX", "ltp": 24000, "open_price": 23900}
        ws._handle_message(msg)
        assert ws.price_cache["NSE:NIFTY50-INDEX"]["ltp"] == 24000
        callback.assert_called_once_with(msg)

    def test_tracks_last_update_time(self, mock_auth):
        ws = FyersWebSocket(mock_auth, on_price_update=MagicMock(), on_disconnect=MagicMock())
        ws._handle_message({"symbol": "NSE:NIFTY50-INDEX", "ltp": 24000})
        assert "NSE:NIFTY50-INDEX" in ws.last_update
        assert isinstance(ws.last_update["NSE:NIFTY50-INDEX"], datetime)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_fyers_ws.py -v`
Expected: FAIL — `ImportError`

- [ ] **Step 3: Implement ws.py**

Create `src/quant/data/fyers/ws.py`:

```python
"""WebSocket manager for real-time Fyers market data."""
from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Callable

from fyers_apiv3.FyersWebsocket import data_ws

from quant.data.fyers.auth import FyersAuth
from quant.data.fyers.exceptions import FyersWebSocketError

_MAX_SYMBOLS = 200


class FyersWebSocket:
    """Manages a Fyers data WebSocket connection with auto-reconnect."""

    def __init__(
        self,
        auth: FyersAuth,
        on_price_update: Callable[[dict], None],
        on_disconnect: Callable[[], None],
    ) -> None:
        self._auth = auth
        self._on_price_update = on_price_update
        self._on_disconnect = on_disconnect
        self._socket: data_ws.FyersDataSocket | None = None
        self._connected = False
        self._loop: asyncio.AbstractEventLoop | None = None

        self.subscribed_symbols: set[str] = set()
        self.price_cache: dict[str, dict] = {}
        self.last_update: dict[str, datetime] = {}

    def is_connected(self) -> bool:
        return self._connected

    def connect(self) -> None:
        """Establish WebSocket connection."""
        try:
            self._loop = asyncio.get_running_loop()
        except RuntimeError:
            self._loop = None

        token = self._auth.get_valid_token()
        access_token = f"{self._auth._credentials['app_id']}:{token}"

        self._socket = data_ws.FyersDataSocket(
            access_token=access_token,
            log_path="",
            litemode=False,
            write_to_file=False,
            reconnect=True,
            on_connect=self._on_connect,
            on_close=self._on_close,
            on_error=self._on_error,
            on_message=self._on_message,
        )
        self._socket.connect()

    def _on_connect(self) -> None:
        self._connected = True
        # Re-subscribe on reconnect
        if self.subscribed_symbols:
            self._socket.subscribe(list(self.subscribed_symbols))

    def _on_close(self) -> None:
        self._connected = False
        if self._loop:
            self._loop.call_soon_threadsafe(self._on_disconnect)
        else:
            self._on_disconnect()

    def _on_error(self, error: str) -> None:
        self._connected = False

    def _handle_message(self, msg: dict) -> None:
        """Process incoming price update."""
        symbol = msg.get("symbol")
        if symbol:
            self.price_cache[symbol] = msg
            self.last_update[symbol] = datetime.now()
        self._on_price_update(msg)

    def _on_message(self, msg: dict) -> None:
        """WebSocket callback — runs on SDK's thread."""
        if self._loop:
            self._loop.call_soon_threadsafe(self._handle_message, msg)
        else:
            self._handle_message(msg)

    def subscribe(self, symbols: list[str]) -> None:
        """Subscribe to SymbolUpdate for given symbols."""
        total = len(self.subscribed_symbols | set(symbols))
        if total > _MAX_SYMBOLS:
            raise ValueError(f"Cannot subscribe to more than {_MAX_SYMBOLS} symbols (requested {total})")
        self.subscribed_symbols.update(symbols)
        if self._connected and self._socket:
            self._socket.subscribe(symbols)

    def unsubscribe(self, symbols: list[str]) -> None:
        """Unsubscribe from given symbols."""
        self.subscribed_symbols -= set(symbols)
        if self._connected and self._socket:
            self._socket.unsubscribe(symbols)

    def disconnect(self) -> None:
        """Close WebSocket connection."""
        if self._socket:
            self._socket.close_connection()
        self._connected = False
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_fyers_ws.py -v`
Expected: All 6 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/quant/data/fyers/ws.py tests/unit/test_fyers_ws.py
git commit -m "Add Fyers WebSocket manager with auto-reconnect and price cache"
```

---

## Task 10: Update MarketDataProvider Protocol

**Files:**
- Modify: `src/quant/data/provider.py`

- [ ] **Step 1: Update the Protocol**

Replace `src/quant/data/provider.py` with:

```python
"""Market data provider interface (Protocol)."""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Protocol

import pandas as pd

from quant.models.contracts import GreeksSnapshot
from quant.models.market import MarketSnapshot, OptionsChain
from quant.utils.types import Underlying


class MarketDataProvider(Protocol):
    """Protocol for market data providers. Primary implementation: Fyers API."""

    async def initialize(self) -> None:
        """Initialize the provider (auth, cache update, websocket connect)."""
        ...

    async def shutdown(self) -> None:
        """Clean shutdown (disconnect websocket, flush cache)."""
        ...

    async def get_options_chain(
        self, underlying: Underlying, expiry: date
    ) -> tuple[OptionsChain, dict[str, GreeksSnapshot]]:
        """Get options chain with Greeks for an underlying at a specific expiry."""
        ...

    async def get_market_snapshot(self, underlying: Underlying) -> MarketSnapshot:
        """Get current market state for an underlying."""
        ...

    async def get_funds(self) -> Decimal:
        """Get available trading capital."""
        ...

    async def get_positions(self) -> list[dict]:
        """Get current open positions."""
        ...

    async def get_candles(
        self, symbol: str, resolution: str, periods: int
    ) -> pd.DataFrame:
        """Get historical OHLCV candles from local cache."""
        ...
```

- [ ] **Step 2: Run existing tests to verify nothing breaks**

Run: `pytest tests/ -v`
Expected: All existing tests PASS

- [ ] **Step 3: Commit**

```bash
git add src/quant/data/provider.py
git commit -m "Extend MarketDataProvider Protocol with lifecycle, account, candle methods"
```

---

## Task 11: Provider Orchestrator

**Files:**
- Create: `src/quant/data/fyers/provider.py`
- Create: `tests/unit/test_fyers_provider.py`
- Modify: `src/quant/data/fyers/__init__.py`

- [ ] **Step 1: Write failing tests**

Create `tests/unit/test_fyers_provider.py`:

```python
"""Tests for FyersProvider orchestrator."""
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
import json

import numpy as np
import pytest
import pytest_asyncio

from quant.data.fyers.provider import FyersProvider
from quant.utils.types import Underlying


@pytest.fixture
def secrets_file(tmp_path):
    creds = {
        "app_id": "TEST123-100",
        "secret_key": "testsecret",
        "redirect_uri": "https://trade.fyers.in/api-login/redirect-uri/abc123",
        "fyers_id": "AB01234",
        "pin": "1234",
        "totp_key": "JBSWY3DPEHPK3PXP",
    }
    path = tmp_path / "fyers"
    path.write_text(json.dumps(creds))
    return path


class TestProtocolConformance:
    def test_fyers_provider_satisfies_protocol(self):
        """Verify FyersProvider has all MarketDataProvider methods."""
        from quant.data.provider import MarketDataProvider
        import inspect
        protocol_methods = {
            name for name, _ in inspect.getmembers(MarketDataProvider, predicate=inspect.isfunction)
            if not name.startswith("_")
        }
        provider_methods = {
            name for name, _ in inspect.getmembers(FyersProvider, predicate=inspect.isfunction)
            if not name.startswith("_")
        }
        assert protocol_methods.issubset(provider_methods), (
            f"Missing: {protocol_methods - provider_methods}"
        )


class TestFyersProviderInit:
    def test_creates_auth(self, secrets_file, tmp_path):
        with patch("quant.data.fyers.provider.FyersAuth") as mock_auth_cls, \
             patch("quant.data.fyers.provider.FyersClient") as mock_client_cls, \
             patch("quant.data.fyers.provider.FyersWebSocket") as mock_ws_cls, \
             patch("quant.data.fyers.provider.CandleCache") as mock_cache_cls:
            mock_auth_cls.return_value = MagicMock()
            provider = FyersProvider(secrets_path=secrets_file, cache_dir=tmp_path)
            mock_auth_cls.assert_called_once()


class TestGetMarketSnapshot:
    @pytest.mark.asyncio
    async def test_returns_snapshot_from_ws_cache(self, secrets_file, tmp_path):
        with patch("quant.data.fyers.provider.FyersAuth") as mock_auth_cls, \
             patch("quant.data.fyers.provider.FyersClient") as mock_client_cls, \
             patch("quant.data.fyers.provider.FyersWebSocket") as mock_ws_cls, \
             patch("quant.data.fyers.provider.CandleCache") as mock_cache_cls:
            mock_auth = MagicMock()
            mock_auth_cls.return_value = mock_auth

            provider = FyersProvider(secrets_path=secrets_file, cache_dir=tmp_path)
            provider._ws.price_cache = {
                "NSE:NIFTY50-INDEX": {"ltp": 24000.0},
                "NSE:INDIAVIX-INDEX": {"ltp": 15.5},
            }
            provider._ws._connected = True

            snapshot = await provider.get_market_snapshot(Underlying.NIFTY)
            assert snapshot.underlying == Underlying.NIFTY
            assert snapshot.price == 24000.0
            assert snapshot.vix_level == 15.5


class TestGetOptionsChain:
    @pytest.mark.asyncio
    async def test_returns_chain_and_greeks(self, secrets_file, tmp_path):
        with patch("quant.data.fyers.provider.FyersAuth") as mock_auth_cls, \
             patch("quant.data.fyers.provider.FyersClient") as mock_client_cls, \
             patch("quant.data.fyers.provider.FyersWebSocket") as mock_ws_cls, \
             patch("quant.data.fyers.provider.CandleCache") as mock_cache_cls:
            mock_auth = MagicMock()
            mock_auth_cls.return_value = mock_auth

            mock_client = AsyncMock()
            mock_client_cls.return_value = mock_client

            # Simulate quotes for 2 symbols (1 CE, 1 PE at same strike)
            mock_client.get_quotes.return_value = {
                "s": "ok",
                "d": [
                    {"n": "NSE:NIFTY2632724000CE", "v": {"lp": 350.0}},
                    {"n": "NSE:NIFTY2632724000PE", "v": {"lp": 280.0}},
                ],
            }

            provider = FyersProvider(secrets_path=secrets_file, cache_dir=tmp_path)
            # Set spot price for ATM calculation
            provider._ws.price_cache = {"NSE:NIFTY50-INDEX": {"ltp": 24000.0}}
            provider._ws._connected = True

            chain, greeks_map = await provider.get_options_chain(
                Underlying.NIFTY, date(2026, 3, 27)
            )

            assert chain.underlying == Underlying.NIFTY
            assert len(chain.contracts) > 0
            assert len(greeks_map) > 0


class TestInitialize:
    @pytest.mark.asyncio
    async def test_startup_sequence(self, secrets_file, tmp_path):
        with patch("quant.data.fyers.provider.FyersAuth") as mock_auth_cls, \
             patch("quant.data.fyers.provider.FyersClient") as mock_client_cls, \
             patch("quant.data.fyers.provider.FyersWebSocket") as mock_ws_cls, \
             patch("quant.data.fyers.provider.CandleCache") as mock_cache_cls:
            mock_auth = MagicMock()
            mock_auth.get_valid_token.return_value = "token"
            mock_auth_cls.return_value = mock_auth

            mock_cache = AsyncMock()
            mock_cache_cls.return_value = mock_cache

            mock_ws = MagicMock()
            mock_ws_cls.return_value = mock_ws

            provider = FyersProvider(secrets_path=secrets_file, cache_dir=tmp_path)
            await provider.initialize()

            mock_auth.get_valid_token.assert_called()
            assert mock_cache.update.call_count == 5  # NIFTY D+W, BANKNIFTY D+W, VIX D
            mock_ws.connect.assert_called_once()
            mock_ws.subscribe.assert_called_once()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_fyers_provider.py -v`
Expected: FAIL — `ImportError`

- [ ] **Step 3: Implement provider.py**

Create `src/quant/data/fyers/provider.py`:

```python
"""FyersProvider — MarketDataProvider implementation using Fyers API v3."""
from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import numpy as np
import pandas as pd

from quant.data.fyers.auth import FyersAuth
from quant.data.fyers.cache import CandleCache
from quant.data.fyers.client import FyersClient
from quant.data.fyers.greeks import compute_greeks, compute_iv
from quant.data.fyers.symbols import (
    INDEX_SYMBOLS,
    VIX_SYMBOL,
    build_chain_symbols,
    build_option_symbol,
    parse_option_symbol,
)
from quant.data.fyers.ws import FyersWebSocket
from quant.models.contracts import GreeksSnapshot, OptionsContract
from quant.models.market import MarketSnapshot, OptionsChain
from quant.utils.types import OptionType, Underlying


class FyersProvider:
    """Orchestrates Fyers auth, REST, WebSocket, Greeks, and cache."""

    def __init__(
        self,
        secrets_path: Path = Path("secrets/fyers"),
        cache_dir: Path = Path("data/candles"),
        risk_free_rate: float = 0.065,
    ) -> None:
        self._auth = FyersAuth(secrets_path)
        self._cache = CandleCache(cache_dir=cache_dir)
        self._risk_free_rate = risk_free_rate
        # Client and WS are created in initialize() to avoid network I/O in constructor
        self._client: FyersClient | None = None
        self._ws: FyersWebSocket | None = None

    def _on_price_update(self, msg: dict) -> None:
        pass  # WebSocket updates are stored in ws.price_cache automatically

    def _on_disconnect(self) -> None:
        pass  # Strategies check ws.is_connected() before using real-time data

    async def initialize(self) -> None:
        """Startup: authenticate, create client/WS, update cache, connect."""
        self._auth.get_valid_token()
        self._client = FyersClient(self._auth)
        self._ws = FyersWebSocket(
            self._auth,
            on_price_update=self._on_price_update,
            on_disconnect=self._on_disconnect,
        )

        # Update candle cache for all indices
        for symbol in [*INDEX_SYMBOLS.values(), VIX_SYMBOL]:
            for res in ["D", "W"] if symbol != VIX_SYMBOL else ["D"]:
                await self._cache.update(symbol, res, self._client)

        # Connect WebSocket and subscribe to spots + VIX
        self._ws.connect()
        self._ws.subscribe([*INDEX_SYMBOLS.values(), VIX_SYMBOL])

    async def shutdown(self) -> None:
        """Disconnect WebSocket."""
        self._ws.disconnect()

    async def get_market_snapshot(self, underlying: Underlying) -> MarketSnapshot:
        """Get current spot + VIX from WebSocket cache or REST fallback."""
        index_sym = INDEX_SYMBOLS[underlying]

        if self._ws.is_connected() and index_sym in self._ws.price_cache:
            spot = self._ws.price_cache[index_sym].get("ltp", 0.0)
            vix = self._ws.price_cache.get(VIX_SYMBOL, {}).get("ltp", 0.0)
        else:
            result = await self._client.get_quotes([index_sym, VIX_SYMBOL])
            data = {d["n"]: d["v"] for d in result.get("d", [])}
            spot = data.get(index_sym, {}).get("lp", 0.0)
            vix = data.get(VIX_SYMBOL, {}).get("lp", 0.0)

        return MarketSnapshot(
            underlying=underlying,
            price=float(spot),
            timestamp=datetime.now(),
            vix_level=float(vix),
        )

    async def get_options_chain(
        self, underlying: Underlying, expiry: date
    ) -> tuple[OptionsChain, dict[str, GreeksSnapshot]]:
        """Build full chain with Greeks from batch quotes + local computation."""
        # Get current spot for ATM
        snapshot = await self.get_market_snapshot(underlying)
        atm = self._round_to_strike(snapshot.price, underlying)

        # Build symbol list
        symbols = build_chain_symbols(underlying, expiry, atm)

        # Batch fetch premiums
        result = await self._client.get_quotes(symbols)
        quote_map: dict[str, float] = {}
        for d in result.get("d", []):
            quote_map[d["n"]] = d["v"].get("lp", 0.0)

        # Build contracts and compute Greeks
        contracts: list[OptionsContract] = []
        premiums_list: list[float] = []
        spots_list: list[float] = []
        strikes_list: list[float] = []
        T_list: list[float] = []
        types_list: list[int] = []
        sym_order: list[str] = []

        days_to_expiry = max((expiry - date.today()).days, 1)
        T_val = days_to_expiry / 365.0

        for sym in symbols:
            premium = quote_map.get(sym, 0.0)
            if premium <= 0:
                continue
            u, exp, strike, opt_type = parse_option_symbol(sym)
            contracts.append(OptionsContract(
                symbol=sym,
                expiry=expiry,
                strike=Decimal(str(strike)),
                option_type=OptionType.CE if opt_type == "CE" else OptionType.PE,
                premium=Decimal(str(premium)),
                lot_size=self._lot_size(underlying),
            ))
            premiums_list.append(premium)
            spots_list.append(snapshot.price)
            strikes_list.append(float(strike))
            T_list.append(T_val)
            types_list.append(1 if opt_type == "CE" else -1)
            sym_order.append(sym)

        # Vectorized Greeks computation
        greeks_map: dict[str, GreeksSnapshot] = {}
        if premiums_list:
            premiums_arr = np.array(premiums_list)
            spots_arr = np.array(spots_list)
            strikes_arr = np.array(strikes_list)
            T_arr = np.array(T_list)
            types_arr = np.array(types_list)

            ivs = compute_iv(premiums_arr, spots_arr, strikes_arr, T_arr, types_arr, self._risk_free_rate)
            greeks = compute_greeks(spots_arr, strikes_arr, T_arr, ivs, types_arr, self._risk_free_rate)

            for i, sym in enumerate(sym_order):
                greeks_map[sym] = GreeksSnapshot(
                    delta=float(greeks["delta"][i]),
                    gamma=float(greeks["gamma"][i]),
                    vega=float(greeks["vega"][i]),
                    theta=float(greeks["theta"][i]),
                    iv=float(ivs[i]) * 100,  # store as percentage
                )

        chain = OptionsChain(underlying=underlying, expiry=expiry, contracts=contracts)
        return chain, greeks_map

    async def get_funds(self) -> Decimal:
        result = await self._client.get_funds()
        # Fyers returns fund_limit list — extract available balance
        limits = result.get("fund_limit", [])
        for item in limits:
            if item.get("title") == "Total Balance":
                return Decimal(str(item.get("equityAmount", 0)))
        return Decimal("0")

    async def get_positions(self) -> list[dict]:
        result = await self._client.get_positions()
        return result.get("netPositions", [])

    async def get_candles(self, symbol: str, resolution: str, periods: int) -> pd.DataFrame:
        today = date.today()
        from_date = today - timedelta(days=periods * 2)  # buffer for weekends/holidays
        df = self._cache.get_candles(symbol, resolution, from_date, today)
        return df.tail(periods)


    def _lot_size(self, underlying: Underlying) -> int:
        from quant.config.settings import settings
        return settings.fyers.lot_size_nifty if underlying == Underlying.NIFTY else settings.fyers.lot_size_banknifty

    @staticmethod
    def _round_to_strike(price: float, underlying: Underlying) -> int:
        """Round spot price to nearest valid strike."""
        from quant.config.settings import settings
        interval = settings.fyers.strike_interval_nifty if underlying == Underlying.NIFTY else settings.fyers.strike_interval_banknifty
        return round(price / interval) * interval
```

- [ ] **Step 4: Update `__init__.py` exports**

Replace `src/quant/data/fyers/__init__.py`:

```python
"""Fyers API v3 integration package."""
from quant.data.fyers.provider import FyersProvider

__all__ = ["FyersProvider"]
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/unit/test_fyers_provider.py -v`
Expected: All 4 tests PASS

- [ ] **Step 6: Run ALL tests to verify nothing is broken**

Run: `pytest tests/ -v`
Expected: All tests PASS

- [ ] **Step 7: Commit**

```bash
git add src/quant/data/fyers/provider.py src/quant/data/fyers/__init__.py tests/unit/test_fyers_provider.py
git commit -m "Add FyersProvider orchestrator implementing MarketDataProvider Protocol"
```

---

## Task 12: Final Integration Verification

- [ ] **Step 1: Run full test suite with coverage**

Run: `pytest tests/ -v --cov=quant.data.fyers --cov-report=term-missing`
Expected: All tests PASS, coverage >85% for `quant.data.fyers`

- [ ] **Step 2: Run ruff linter**

Run: `ruff check src/quant/data/fyers/ tests/unit/test_fyers_*.py`
Expected: No errors

- [ ] **Step 3: Run mypy type check**

Run: `mypy src/quant/data/fyers/`
Expected: No errors (or only expected missing stubs for fyers_apiv3)

- [ ] **Step 4: Commit any lint/type fixes if needed**

```bash
git add -A
git commit -m "Fix lint/type issues in Fyers integration module"
```
