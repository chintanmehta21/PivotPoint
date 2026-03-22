# Fyers Authentication & Data Pipeline Design

**Date:** 2026-03-22
**Status:** Approved
**Scope:** `src/quant/data/fyers/` — authentication, market data fetching, WebSocket streaming, Greeks computation, and historical candle caching

---

## 1. Problem Statement

PivotPoint has 14 options strategies (6 bullish, 8 bearish) with complete signal generation logic, but no live data feed. The `MarketDataProvider` Protocol in `src/quant/data/provider.py` defines the core interface — this design implements it against Fyers API v3 and extends the Protocol with additional methods for lifecycle, account data, and historical candles.

### Data Requirements (derived from codebase analysis)

| Category | Data Points | Frequency | Consumers |
|---|---|---|---|
| Spot | NIFTY, BANKNIFTY price | Real-time (WebSocket) | All 14 strategies — strike selection, entry/exit |
| VIX | India VIX level | Real-time (WebSocket) | All strategies — regime gates (VIX 12-18 checks) |
| Options Chain | All strikes + premiums per expiry | Real-time (batch + WS) | Multi-leg position construction |
| Greeks | Delta, Gamma, Vega, Theta, IV per contract | Computed locally | Position Greeks aggregation, risk tracking |
| IV Surface | Skew, term structure | Derived from chain | Diagonal calendars, broken wings, skew harvest |
| Historical | OHLCV daily/weekly candles | Daily batch | SuperTrend indicator, support/resistance |
| Account | Balance, positions, holdings | On-demand | Position sizing (2% risk), max 3 pos/underlying |

### Fyers API v3 Rate Limits

- **Per second:** 10 requests
- **Per minute:** 200 requests
- **Per day:** 100,000 requests

---

## 2. Architecture

### Module Structure

```
src/quant/data/fyers/
  __init__.py          ← exports FyersProvider
  auth.py              ← headless TOTP login, token lifecycle
  client.py            ← thin REST wrapper (quotes, history, depth)
  ws.py                ← WebSocket manager (connect, subscribe, reconnect)
  provider.py          ← implements MarketDataProvider, orchestrates above
  greeks.py            ← vectorized Black-Scholes (IV + all Greeks)
  cache.py             ← parquet-based historical candle cache
  symbols.py           ← Fyers option symbol format construction/parsing
  exceptions.py        ← FyersError hierarchy (extends PivotPointError)
```

### Data Flow

```
secrets/fyers (credentials JSON)
       │
       ▼
   FyersAuth ──token──▶ FyersClient ──REST──▶ Fyers API
       │                     │
       │                     ├── quotes() ──▶ batch premiums
       │                     ├── history() ──▶ OHLCV candles
       │                     ├── funds()   ──▶ capital
       │                     └── positions()──▶ open trades
       │
       ├──token──▶ FyersWebSocket ──stream──▶ spot, VIX, option LTPs
       │
       ▼
   FyersProvider (orchestrator)
       ├── greeks.py (NumPy vectorized BS) ◀── premiums from chain
       ├── cache.py (parquet files) ◀── candles from client
       └── implements MarketDataProvider Protocol
              │
              ▼
       Strategies, Execution, Risk modules
```

---

## 3. Credentials Management

### File: `secrets/fyers` (JSON)

```json
{
  "app_id": "XXXX-100",
  "secret_key": "...",
  "redirect_uri": "https://trade.fyers.in/api-login/redirect-uri/abc123",
  "fyers_id": "XX01234",
  "pin": "1234",
  "totp_key": "BASE32SECRET..."
}
```

- All Fyers credentials in a single file
- `secrets/` is gitignored
- Current `FyersSettings` fields (`app_id`, `secret_key`, `redirect_url`) move here
- `FyersSettings` in `settings.py` retains only operational config (rate limits, cache paths, etc.)

---

## 4. Module Designs

### 4.1 Authentication (`auth.py`)

**Class: `FyersAuth`**

```python
class FyersAuth:
    def __init__(self, secrets_path: Path)
    def authenticate(self) -> str        # full 5-step headless login
    def get_valid_token(self) -> str      # cached token or re-auth
```

**Headless TOTP Login Flow (5 steps):**

1. **Send OTP:** `POST https://api-t2.fyers.in/vagator/v2/send_login_otp_v2`
   - Payload: `{"fy_id": base64(fyers_id), "app_id": "2"}`
   - Returns: `request_key`

2. **Verify OTP with TOTP:** `POST https://api-t2.fyers.in/vagator/v2/verify_otp`
   - Payload: `{"request_key": ..., "otp": totp(totp_key)}`
   - TOTP generated inline: HMAC-SHA1, RFC 6238, 30s step, 6 digits
   - Returns: new `request_key`

3. **Verify PIN:** `POST https://api-t2.fyers.in/vagator/v2/verify_pin_v2`
   - Payload: `{"request_key": ..., "identity_type": "pin", "identifier": base64(pin)}`
   - Returns: `access_token` (intermediate, for auth code request)

4. **Get Auth Code:** `POST https://api.fyers.in/api/v2/token`
   - Bearer auth with step 3 token
   - Payload: `{"fyers_id": ..., "app_id": ..., "redirect_uri": ..., "appType": "100", ...}`
   - Returns: 308 redirect with `auth_code` in URL query params

5. **Exchange for Access Token:** `SessionModel.set_token(auth_code)` → `generate_token()`
   - Returns: final `access_token` for all API calls

**Token Lifecycle:**
- On startup: `get_valid_token()` checks cached token via `get_profile()`
- If valid: reuse (skip re-auth)
- If expired/invalid: run full `authenticate()` flow
- Mid-session 401: re-authenticate and retry the failed operation
- Token stored in-memory only (ephemeral, expires daily at market close)

**TOTP Implementation (inline, no external dependency):**
```python
def totp(key: str, time_step: int = 30, digits: int = 6) -> str:
    key = key.rstrip("=")  # strip existing padding before re-padding
    key_bytes = base64.b32decode(key.upper() + "=" * ((8 - len(key)) % 8))
    counter = struct.pack(">Q", int(time.time() / time_step))
    mac = hmac.new(key_bytes, counter, "sha1").digest()
    offset = mac[-1] & 0x0F
    binary = struct.unpack(">L", mac[offset:offset + 4])[0] & 0x7FFFFFFF
    return str(binary)[-digits:].zfill(digits)
```

**Errors:** `FyersAuthError(PivotPointError)` with step identification (e.g., "Step 2 failed: OTP verification rejected").

---

### 4.2 REST Client (`client.py`)

**Class: `FyersClient`**

Thin wrapper around `fyersModel.FyersModel`. No business logic.

**Async bridging:** The Fyers SDK is synchronous (uses `requests` internally). All client methods are `async def` and wrap synchronous SDK calls with `await asyncio.to_thread(self._model.<method>, ...)` to avoid blocking the event loop.

```python
class FyersClient:
    def __init__(self, auth: FyersAuth)
    async def get_quotes(self, symbols: list[str]) -> list[dict]
    async def get_history(self, symbol: str, resolution: str, from_ts: int, to_ts: int) -> list[dict]
    async def get_market_depth(self, symbol: str) -> dict
    async def get_profile(self) -> dict
    async def get_funds(self) -> dict
    async def get_positions(self) -> list[dict]
    async def get_holdings(self) -> list[dict]
```

**Rate Limit Handling:**
- Internal sliding-window counters: calls in last 1s and last 60s
- Pre-call check: if approaching limit (>8/sec or >180/min), `await asyncio.sleep()` until safe
- On 429 response: raise `FyersRateLimitError`

**Batch Optimization for `get_quotes()`:**
- Fyers accepts comma-separated symbols in a single call
- Auto-chunk into batches of 50 symbols
- Full NIFTY chain (200 symbols) = 4 API calls instead of 200

**Token Refresh:**
- On expired/401 response: call `auth.get_valid_token()` (triggers re-auth)
- Re-initialize `FyersModel` with fresh token
- Retry the failed call once

---

### 4.3 WebSocket Manager (`ws.py`)

**Class: `FyersWebSocket`**

```python
class FyersWebSocket:
    def __init__(self, auth: FyersAuth, on_price_update: Callback, on_disconnect: Callback)
    def connect(self)
    def subscribe(self, symbols: list[str])
    def unsubscribe(self, symbols: list[str])
    def is_connected(self) -> bool
```

**Implementation:**
- Uses `fyers_apiv3.FyersWebsocket.data_ws.FyersDataSocket`
- `litemode=False` — need full OHLCV, not just LTP
- `reconnect=True` — SDK-level reconnection enabled
- Max 200 symbols per connection (Fyers limit)

**Thread-to-asyncio bridging:** The Fyers WebSocket SDK uses internal threading for callbacks. The `on_price_update` callback bridges data into the asyncio event loop via `loop.call_soon_threadsafe()` to safely update the price cache and notify consumers.

**Reconnection Strategy:**
- Exponential backoff: 1s → 2s → 4s → 8s → 16s → 30s (cap)
- On disconnect: fire `on_disconnect` callback → strategies pause signal generation
- On reconnect: automatically re-subscribe to all tracked symbols
- No REST fallback — keep it simple, pause until WebSocket recovers

**Internal State:**
- `subscribed_symbols: set[str]` — current subscriptions
- `last_update: dict[str, datetime]` — per-symbol staleness tracking
- `price_cache: dict[str, dict]` — latest SymbolUpdate data per symbol

**Subscription Management:**
- Subscribe to underlying spots: `NSE:NIFTY50-INDEX`, `NSE:NIFTYBANK-INDEX`
- Subscribe to VIX: `NSE:INDIAVIX-INDEX`
- Subscribe to active option symbols (up to ~197 remaining slots)
- Rotate subscriptions when expiry rolls or chain needs refreshing

---

### 4.4 Greeks Engine (`greeks.py`)

**Pure functions, NumPy vectorized. No class.**

```python
def compute_iv(
    premiums: np.ndarray, spots: np.ndarray, strikes: np.ndarray,
    T: np.ndarray, option_types: np.ndarray, r: float = 0.065
) -> np.ndarray

def compute_greeks(
    spots: np.ndarray, strikes: np.ndarray, T: np.ndarray,
    ivs: np.ndarray, option_types: np.ndarray, r: float = 0.065
) -> dict[str, np.ndarray]  # {"delta", "gamma", "vega", "theta"}

def black_scholes_price(
    spots: np.ndarray, strikes: np.ndarray, T: np.ndarray,
    ivs: np.ndarray, r: float, option_types: np.ndarray
) -> np.ndarray
```

**IV Solver:**
- Newton-Raphson method, vectorized across entire chain
- Convergence tolerance: 1e-6
- Max iterations: 50
- Edge cases: deep ITM → intrinsic value floor; deep OTM (premium < 0.05) → IV = 0; near-expiry (T < 1 day) → use last known IV

**Performance:**
- Full NIFTY chain (200 contracts): <5ms
- All inputs/outputs are NumPy arrays
- Risk-free rate: 6.5% (RBI repo rate), configurable via `FyersSettings.risk_free_rate`

**Greeks formulas (European options, Black-Scholes):**
- Delta: N(d1) for calls, N(d1) - 1 for puts
- Gamma: n(d1) / (S × σ × √T)
- Vega: S × n(d1) × √T
- Theta: standard BS theta with dividend yield = 0

---

### 4.5 Candle Cache (`cache.py`)

**Class: `CandleCache`**

```python
class CandleCache:
    def __init__(self, cache_dir: Path = Path("data/candles"))
    def get_candles(self, symbol: str, resolution: str, from_date: date, to_date: date) -> pd.DataFrame  # sync: local parquet read
    async def update(self, symbol: str, resolution: str, client: FyersClient)    # async: fetches from API
    async def backfill(self, symbol: str, resolution: str, days_back: int, client: FyersClient)  # async: fetches from API
```

Note: `get_candles()` is intentionally synchronous — it reads from local parquet files only (no network I/O). `update()` and `backfill()` are async because they call `FyersClient` which uses `asyncio.to_thread()`.

**Storage:**
- One parquet file per `{symbol}_{resolution}.parquet`
- Examples: `NIFTY50_D.parquet`, `NIFTYBANK_W.parquet`, `INDIAVIX_D.parquet`
- Cache directory: `data/candles/` (configurable via `FyersSettings.cache_dir`)

**Incremental Updates:**
- On startup: check last cached date per file
- Fetch only the delta (new candles since last cached date)
- Append to existing parquet file
- First run: full backfill — 52 weeks weekly, 260 trading days daily (~1 year)

**Symbols Cached:**
- `NSE:NIFTY50-INDEX` — daily + weekly
- `NSE:NIFTYBANK-INDEX` — daily + weekly
- `NSE:INDIAVIX-INDEX` — daily

**Resolution Mapping:**
- `"D"` → Fyers `"1D"` (daily)
- `"W"` → Fyers `"1W"` (weekly)

---

### 4.6 Provider Orchestrator (`provider.py`)

**Class: `FyersProvider` — implements `MarketDataProvider` Protocol**

```python
class FyersProvider:
    def __init__(self, secrets_path: Path = Path("secrets/fyers"))
    async def initialize(self) -> None
    async def get_market_snapshot(self, underlying: Underlying) -> MarketSnapshot
    async def get_options_chain(self, underlying: Underlying, expiry: date) -> tuple[OptionsChain, dict[str, GreeksSnapshot]]
    async def get_funds(self) -> Decimal
    async def get_positions(self) -> list[dict]
    async def get_candles(self, symbol: str, resolution: str, periods: int) -> pd.DataFrame
    async def shutdown(self) -> None
```

**Startup Sequence (`initialize()`):**
1. `auth.get_valid_token()` — authenticate with Fyers
2. `cache.update()` for all 3 indices — incremental candle refresh
3. `ws.connect()` — establish WebSocket connection
4. `ws.subscribe(["NSE:NIFTY50-INDEX", "NSE:NIFTYBANK-INDEX", "NSE:INDIAVIX-INDEX"])` — subscribe to spots + VIX
5. Provider is ready for strategy evaluation

**`get_market_snapshot()`:**
- Returns spot price + VIX from WebSocket price cache
- If WebSocket not connected: falls back to single `get_quotes()` REST call

**`get_options_chain()`:**
1. Build symbol list using Fyers symbol format (see Section 4.7)
2. Batch `client.get_quotes()` for all symbols → get premiums
3. `greeks.compute_iv()` on all premiums
4. `greeks.compute_greeks()` on all contracts
5. Build `OptionsChain` with `OptionsContract` objects (premiums populated)
6. Build parallel `dict[str, GreeksSnapshot]` keyed by contract symbol — returned as a second value
7. Optionally subscribe new option symbols to WebSocket for live updates

**Return type change:** `get_options_chain()` returns `tuple[OptionsChain, dict[str, GreeksSnapshot]]` — the chain with premiums, plus a symbol-keyed Greeks lookup. This avoids modifying the existing `OptionsContract` model (which is used broadly) while making Greeks available to strategies. The `MarketDataProvider` Protocol will be updated to reflect this return type.

**`get_candles()`:**
- Reads from `CandleCache`
- Returns last N periods of requested resolution

**`shutdown()`:**
- Disconnect WebSocket
- Flush any pending cache writes

**Market hours awareness:**
- `initialize()` succeeds regardless of market hours — auth and cache update work anytime
- WebSocket connection is deferred until market hours (9:15 AM - 3:30 PM IST) if called outside hours
- `get_market_snapshot()` outside hours returns last cached data with stale timestamp
- `get_options_chain()` outside hours uses last available premiums (stale, for analysis only)
- Raises `MarketClosedError` only if a consumer explicitly requests real-time guarantees

---

### 4.7 Symbol Format (`symbols.py`)

**Helper module for Fyers option symbol construction.**

Fyers option symbol format: `NSE:NIFTY{YY}{M}{DD}{STRIKE}{TYPE}`
- `YY`: 2-digit year (e.g., `26`)
- `M`: month code — `1`-`9` for Jan-Sep, `O` for Oct, `N` for Nov, `D` for Dec
- `DD`: 2-digit day of month
- `STRIKE`: strike price as integer (no decimals)
- `TYPE`: `CE` or `PE`

Examples:
- `NSE:NIFTY2632724000CE` → NIFTY 27-Mar-2026 24000 CE
- `NSE:BANKNIFTY26N0652000PE` → BANKNIFTY 06-Nov-2026 52000 PE

```python
def build_option_symbol(underlying: Underlying, expiry: date, strike: int, option_type: str) -> str
def build_chain_symbols(underlying: Underlying, expiry: date, atm_strike: int) -> list[str]
def parse_option_symbol(symbol: str) -> tuple[Underlying, date, int, str]
```

`build_chain_symbols()` generates all symbols for ATM ± range at the configured interval (50pt NIFTY, 100pt BANKNIFTY), both CE and PE.

Index spot symbols (not options):
- `NSE:NIFTY50-INDEX`
- `NSE:NIFTYBANK-INDEX`
- `NSE:INDIAVIX-INDEX`

---

## 5. Protocol Update

The existing `MarketDataProvider` Protocol in `src/quant/data/provider.py` will be extended:

```python
class MarketDataProvider(Protocol):
    """Protocol for market data providers."""

    async def initialize(self) -> None: ...
    async def shutdown(self) -> None: ...
    async def get_options_chain(self, underlying: Underlying, expiry: date) -> tuple[OptionsChain, dict[str, GreeksSnapshot]]: ...
    async def get_market_snapshot(self, underlying: Underlying) -> MarketSnapshot: ...
    async def get_funds(self) -> Decimal: ...
    async def get_positions(self) -> list[dict]: ...
    async def get_candles(self, symbol: str, resolution: str, periods: int) -> pd.DataFrame: ...
```

This is a breaking change to the Protocol. All consumers (strategies, execution, risk) that call `get_options_chain()` will need to unpack the tuple return. Since no implementation exists yet, this is safe.

**Downstream impact on strategies:** The orchestrator that calls `BaseStrategy.evaluate(chain)` will also need to pass the Greeks dict. Options: (a) add `greeks: dict[str, GreeksSnapshot]` parameter to `evaluate()`, or (b) have the orchestrator attach Greeks to a context object. Decision deferred to the strategy execution implementation phase — this spec covers the data provider layer only.

---

## 6. Settings Update

`FyersSettings` in `src/quant/config/settings.py` changes from credential storage to operational config:

```python
class FyersSettings(BaseModel):
    """Fyers API operational configuration."""
    secrets_path: str = "secrets/fyers"
    ws_reconnect_max_delay: int = 30        # seconds
    ws_max_symbols: int = 200
    quotes_batch_size: int = 50
    rate_limit_per_sec: int = 10
    rate_limit_per_min: int = 200
    risk_free_rate: float = 0.065           # RBI repo rate
    cache_dir: str = "data/candles"
    strike_range_nifty: int = 500           # ATM ± points
    strike_interval_nifty: int = 50
    strike_range_banknifty: int = 500
    strike_interval_banknifty: int = 100
```

---

## 7. Error Hierarchy

```
PivotPointError (existing base in quant.utils.exceptions)
└── FyersError(PivotPointError)
    ├── FyersAuthError        — login flow step failures (includes step number)
    ├── FyersRateLimitError   — 429 responses or self-throttled
    ├── FyersAPIError         — non-200 REST responses (includes status code + endpoint)
    ├── FyersWebSocketError   — connection/subscription failures
    └── FyersDataError        — missing/malformed market data
```

All exceptions defined in `src/quant/data/fyers/exceptions.py` and re-exported via `quant.utils.exceptions` for consistency with existing patterns like `ContractExpiredError`, `MarketClosedError`, etc.

---

## 8. Dependencies

**New packages required:**
- `fyers-apiv3` — Fyers SDK (REST + WebSocket)
- `pyarrow` — parquet file I/O for candle cache
- `numpy` — vectorized Greeks computation (likely already needed for data_science)
- `pandas` — DataFrame for candle data (likely already needed)

**No new dependencies for:**
- TOTP generation (stdlib: `hmac`, `struct`, `base64`, `time`)
- HTTP requests for auth flow (`requests` — bundled with fyers-apiv3)

---

## 9. API Call Budget (Typical Session)

| Phase | Calls | Detail |
|---|---|---|
| Auth | 5 | 4 login steps + 1 token exchange |
| Token validation | 1 | `get_profile()` check |
| Candle update | 5 | 3 symbols × ~2 resolutions (incremental, often 1 call each) |
| Chain snapshot | 4-8 | 200 symbols / 50 per batch = 4 calls per underlying |
| Account data | 2-3 | funds + positions + holdings |
| **Total startup** | **~20** | Well within 200/min |
| **Ongoing (WebSocket)** | **0** | All real-time data via stream |
| **Chain refresh** | **4-8/refresh** | Only when expiry rolls or manual trigger |

Daily budget usage: ~50-100 calls out of 100,000 limit.
