# Fyers Data Pipeline — First Run Log

**Date:** 2026-03-23
**Branch:** master
**Python:** 3.11.9 (Windows 11)

---

## 1. Module Import Check

All 9 modules import cleanly with no errors:

| Module | Status |
|---|---|
| `quant.data.fyers` | OK |
| `quant.data.fyers.exceptions` | OK |
| `quant.data.fyers.symbols` | OK |
| `quant.data.fyers.auth` | OK |
| `quant.data.fyers.client` | OK |
| `quant.data.fyers.greeks` | OK |
| `quant.data.fyers.cache` | OK |
| `quant.data.fyers.ws` | OK |
| `quant.data.fyers.provider` | OK |

`FyersProvider` is correctly exported from `quant.data.fyers.__init__`.

---

## 2. Protocol Conformance

`FyersProvider` implements all 7 `MarketDataProvider` Protocol methods:
- `initialize`, `shutdown`, `get_options_chain`, `get_market_snapshot`, `get_funds`, `get_positions`, `get_candles`

**Status: PASS**

---

## 3. Exception Hierarchy

All Fyers exceptions properly inherit from `PivotPointError`:
- `FyersError(PivotPointError)` — base
- `FyersAuthError(FyersError)` — includes `step` and `reason`
- `FyersRateLimitError(FyersError)` — includes `limit_type` and `limit`
- `FyersAPIError(FyersError)` — includes `status_code` and `endpoint`
- `FyersWebSocketError(FyersError)`
- `FyersDataError(FyersError)`

Re-exports via `quant.utils.exceptions` work (lazy `__getattr__` to avoid circular imports).

**Status: PASS**

---

## 4. Settings

`FyersSettings` operational config loaded with correct defaults:

| Setting | Value |
|---|---|
| `secrets_path` | `secrets/fyers` |
| `rate_limit_per_sec` | 10 |
| `rate_limit_per_min` | 200 |
| `lot_size_nifty` | 75 |
| `lot_size_banknifty` | 15 |
| `risk_free_rate` | 0.065 |
| `cache_dir` | `data/candles` |
| `strike_range_nifty` | 500 |
| `strike_interval_nifty` | 50 |
| `strike_range_banknifty` | 500 |
| `strike_interval_banknifty` | 100 |
| `ws_max_symbols` | 200 |
| `ws_reconnect_max_delay` | 30 |

Credential fields (`app_id`, `secret_key`, `redirect_url`) no longer exist on `FyersSettings`.

**Status: PASS**

---

## 5. Symbol Format Validation

| Test | Result |
|---|---|
| NIFTY 24000 CE Mar 27 | `NSE:NIFTY2632724000CE` |
| BANKNIFTY 52000 PE Mar 27 | `NSE:BANKNIFTY2632752000PE` |
| Roundtrip parse | NIFTY 2026-03-27 24000 CE |
| NIFTY chain size (ATM 24000 +/-500 @50) | 42 symbols |
| BANKNIFTY chain size (ATM 52000 +/-500 @100) | 22 symbols |
| All 12 month code roundtrips | PASS |
| INDEX_SYMBOLS | NIFTY -> NSE:NIFTY50-INDEX, BANKNIFTY -> NSE:NIFTYBANK-INDEX |
| VIX_SYMBOL | NSE:INDIAVIX-INDEX |

**Status: PASS**

---

## 6. Greeks Engine Numerical Validation

### Black-Scholes Pricing

| Metric | Value |
|---|---|
| ATM Call (S=24000, K=24000, T=30d, IV=20%) | Rs 613.77 |
| ATM Put (same params) | Rs 485.89 |
| Put-Call Parity error | Rs 0.000000 (perfect) |

### IV Solver (Newton-Raphson)

| Metric | Value |
|---|---|
| Input IV | 0.200000 |
| Recovered IV | 0.200000 |
| Recovery error | 0.00000000 |

### Greeks (ATM Call, 30d, 20% IV)

| Greek | Value | Expected Range |
|---|---|---|
| Delta | 0.5485 | 0.45 - 0.65 |
| Gamma | 0.000288 | > 0 |
| Vega | 27.2466 | > 0 |
| Theta | -11.3171 | < 0 |

### Vectorized Performance

| Metric | Value |
|---|---|
| Contracts | 200 (100 CE + 100 PE) |
| Total time (price + IV + Greeks) | 1.7ms |
| Max IV recovery error | 0.00000097 |

**Status: PASS**

### Bug Found and Fixed

**Issue:** `greeks.py` used `math.sqrt(T)` (`_sqrt`) in `_d1_d2()`, `compute_iv()`, and `compute_greeks()`. This fails when `T` is a NumPy array (which it is when processing a full chain). Unit tests passed because they happened to use scalar-compatible array shapes.

**Fix:** Replaced all `_sqrt(T)` with `np.sqrt(T)` in 3 locations. Commit `3e3fe1e`.

**Root cause:** The subagent implementing greeks used `from math import sqrt as _sqrt` for constants but also used it for the dynamic `T` parameter. The unit tests didn't catch this because `pytest` tests used arrays that were coincidentally 0-dimensional or the helper function `_d1_d2` was called with already-computed scalar values internally.

**Lesson:** Integration tests with realistic array shapes would have caught this. The unit tests were correct but didn't exercise the full vectorized path with multi-element `T` arrays.

---

## 7. TOTP Generation

| Metric | Value |
|---|---|
| Output | 443861 |
| Length | 6 digits |
| Deterministic | Yes (same key + time = same OTP) |
| Padded key handling | Works |

**Status: PASS**

---

## 8. Authentication (Live)

**Status: BLOCKED — No credentials file**

The file `secrets/fyers` does not exist. This is expected for a first run before the user has set up their Fyers API credentials.

### Required Setup Steps

1. Create app at https://myapi.fyers.in/dashboard/
2. Enable "External 2FA TOTP" at https://myaccount.fyers.in/ManageAccount
3. Create `secrets/fyers` with:
```json
{
  "app_id": "YOUR_APP_ID-100",
  "secret_key": "YOUR_SECRET_KEY",
  "redirect_uri": "https://trade.fyers.in/api-login/redirect-uri/abc123",
  "fyers_id": "YOUR_CLIENT_ID",
  "pin": "YOUR_4_DIGIT_PIN",
  "totp_key": "YOUR_BASE32_TOTP_SECRET"
}
```
4. First-time only: visit the auth URL in a browser to grant app permissions

### What Would Happen With Credentials

The auth flow would:
1. POST to `api-t2.fyers.in/vagator/v2/send_login_otp_v2` with base64-encoded fyers_id
2. POST to `api-t2.fyers.in/vagator/v2/verify_otp` with generated TOTP
3. POST to `api-t2.fyers.in/vagator/v2/verify_pin_v2` with base64-encoded PIN
4. POST to `api.fyers.in/api/v2/token` to get auth_code
5. Exchange auth_code for access_token via Fyers SDK

Token is cached in-memory and validated via `get_profile()` on subsequent calls.

---

## 9. Candle Cache

| Metric | Value |
|---|---|
| Cache directory | `data/candles/` |
| Directory created | Yes (auto on first use) |
| Format | Parquet (one file per symbol + resolution) |
| Naming | `NIFTY50_D.parquet`, `NIFTYBANK_W.parquet`, etc. |
| Symbol cleaning | Strips `NSE:`, `-INDEX`, `-EQ` |

**Status: PASS** (structure ready, data fetching requires live auth)

---

## 10. WebSocket Manager

| Metric | Value |
|---|---|
| Class importable | Yes |
| Max symbols | 200 |
| Reconnect | Enabled (SDK-level) |
| Thread bridging | `loop.call_soon_threadsafe()` |
| Price cache | Dict keyed by symbol |

**Status: PASS** (structure ready, connection requires live auth)

---

## 11. Provider Orchestrator

| Metric | Value |
|---|---|
| Protocol conformance | All 7 methods present |
| Lazy initialization | Client + WS created in `initialize()`, not constructor |
| Lot sizes from settings | NIFTY=75, BANKNIFTY=15 |
| Strike intervals from settings | NIFTY=50, BANKNIFTY=100 |

**Status: PASS** (full orchestration requires live auth)

---

## 12. Full Test Suite

```
198 passed, 1 warning in 9.35s
```

| Category | Count |
|---|---|
| Fyers exceptions | 8 |
| Fyers symbols | 41 |
| Fyers settings | 2 |
| Fyers auth | 11 |
| Fyers greeks | 15 |
| Fyers client | 5 |
| Fyers cache | 5 |
| Fyers websocket | 6 |
| Fyers provider | 23 |
| **Fyers subtotal** | **116** |
| Pre-existing tests | 82 |
| **Total** | **198** |

**Status: ALL PASS**

---

## 13. Lint Check

After auto-fix: **0 errors remaining** (ruff check).

Issues fixed:
- Import sorting (I001) in cache.py, greeks.py
- `timezone.utc` -> `datetime.UTC` (UP017) in cache.py, provider.py
- `typing.Dict` -> `dict` (UP006/UP035) in symbols.py
- `typing.Callable` -> `collections.abc.Callable` (UP035) in ws.py

---

## 14. GitHub Workflows

**Status: NOT CONFIGURED**

No `.github/workflows/` directory exists. CI/CD pipeline needs to be created separately. The test suite is fully runnable locally with `pytest tests/ -v`.

---

## Summary

| Area | Status | Notes |
|---|---|---|
| Module imports | PASS | All 9 modules clean |
| Protocol conformance | PASS | 7/7 methods |
| Exception hierarchy | PASS | Extends PivotPointError |
| Settings | PASS | 14 operational config fields |
| Symbol format | PASS | All months, both underlyings, roundtrip |
| Greeks engine | PASS | 1.7ms/200 contracts, perfect parity |
| TOTP generation | PASS | RFC 6238 compliant |
| Candle cache | PASS | Parquet structure ready |
| WebSocket manager | PASS | Structure ready |
| Provider orchestrator | PASS | Composes all modules |
| Test suite | PASS | 198/198 |
| Lint | PASS | 0 errors |
| **Live auth** | **BLOCKED** | **Needs secrets/fyers credentials** |
| **Live data fetch** | **BLOCKED** | **Needs auth first** |
| **GitHub CI** | **NOT SET UP** | **No workflows exist** |

### Bugs Found

1. **greeks.py `_sqrt(T)` bug** — `math.sqrt` cannot handle NumPy arrays. Fixed to `np.sqrt(T)`. Commit `3e3fe1e`.

### Next Steps

1. **Create `secrets/fyers`** with your Fyers API credentials
2. **Run live auth test**: `python -c "from quant.data.fyers.auth import FyersAuth; a = FyersAuth('secrets/fyers'); print(a.get_valid_token()[:20] + '...')"`
3. **Run full pipeline test**: Initialize provider, fetch market snapshot, get options chain
4. **Set up GitHub workflow** for CI (pytest + ruff + mypy)
