"""Async REST client wrapper for the Fyers API v3.

Wraps all synchronous fyers_apiv3 SDK calls with ``asyncio.to_thread`` so
they can be awaited from async callers without blocking the event loop.

Rate limiting
-------------
Two soft limits are enforced with a sliding-window counter:

* **Per-second:**  8 calls / second
* **Per-minute:** 180 calls / minute

When either limit is reached a ``FyersRateLimitError`` is raised immediately
(no silent retry/sleep) so callers can back off or queue the request.

Token refresh
-------------
If any API response contains ``"expired"`` in its ``message`` field the client
transparently calls ``auth.get_valid_token()`` to obtain a fresh token,
rebuilds the ``FyersModel``, and retries the call once.
"""
from __future__ import annotations

import asyncio
import time
from collections import deque
from typing import Any

from fyers_apiv3 import fyersModel

from quant.data.fyers.exceptions import FyersRateLimitError

# ---------------------------------------------------------------------------
# Rate-limit constants
# ---------------------------------------------------------------------------

_RATE_LIMIT_PER_SECOND = 8
_RATE_LIMIT_PER_MINUTE = 180

# Maximum number of symbols per quotes batch (Fyers API limit).
_QUOTES_BATCH_SIZE = 50


class FyersClient:
    """Async wrapper around the synchronous Fyers API v3 SDK.

    Parameters
    ----------
    auth:
        A ``FyersAuth`` instance (or any object that exposes
        ``get_valid_token() -> str`` and ``._credentials: dict``).
    """

    def __init__(self, auth: Any) -> None:
        self._auth = auth
        self._model: fyersModel.FyersModel = self._build_model()

        # Sliding-window rate-limit state: stores timestamps of recent calls.
        self._call_times: deque[float] = deque()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_model(self) -> fyersModel.FyersModel:
        """Obtain a valid token and construct a FyersModel."""
        token = self._auth.get_valid_token()
        # Resolve app_id from whichever attribute the auth object exposes.
        creds = getattr(self._auth, "_credentials", None) or getattr(self._auth, "_creds", {})
        app_id: str = creds.get("app_id", "")
        return fyersModel.FyersModel(
            client_id=app_id,
            token=token,
            is_async=False,
            log_path="",
        )

    def _throttle(self) -> None:
        """Enforce sliding-window rate limits.

        Raises ``FyersRateLimitError`` if either the per-second or per-minute
        limit would be exceeded by the *current* call.
        """
        now = time.monotonic()

        # Prune entries older than 60 seconds.
        while self._call_times and now - self._call_times[0] > 60.0:
            self._call_times.popleft()

        # Count calls in the last second.
        calls_last_second = sum(1 for t in self._call_times if now - t <= 1.0)

        if calls_last_second >= _RATE_LIMIT_PER_SECOND:
            raise FyersRateLimitError(limit_type="per_second", limit=_RATE_LIMIT_PER_SECOND)

        if len(self._call_times) >= _RATE_LIMIT_PER_MINUTE:
            raise FyersRateLimitError(limit_type="per_minute", limit=_RATE_LIMIT_PER_MINUTE)

        self._call_times.append(now)

    def _is_expired_response(self, response: dict[str, Any]) -> bool:
        """Return True if the API response indicates token expiry."""
        msg: str = response.get("message", "") or ""
        return "expired" in msg.lower()

    def _refresh_model(self) -> None:
        """Re-authenticate and rebuild the FyersModel in-place."""
        self._model = self._build_model()

    async def _call(self, fn_name: str, *args: Any, **kwargs: Any) -> dict[str, Any]:
        """Call a named SDK method, refreshing the token once on expiry.

        Parameters
        ----------
        fn_name:
            Name of the method on ``self._model`` to invoke (e.g. ``"quotes"``).
        *args, **kwargs:
            Forwarded to the SDK method.
        """
        self._throttle()

        def _invoke() -> dict[str, Any]:
            return getattr(self._model, fn_name)(*args, **kwargs)

        result: dict[str, Any] = await asyncio.to_thread(_invoke)

        if self._is_expired_response(result):
            # Refresh token and retry once.
            self._refresh_model()
            self._throttle()
            result = await asyncio.to_thread(_invoke)

        return result

    # ------------------------------------------------------------------
    # Public API methods
    # ------------------------------------------------------------------

    async def get_quotes(self, symbols: list[str]) -> dict[str, Any]:
        """Fetch live quotes for *symbols*, auto-batching at 50 per request.

        Parameters
        ----------
        symbols:
            List of Fyers symbol strings, e.g. ``["NSE:NIFTY50-INDEX"]``.

        Returns
        -------
        dict
            Merged response with ``"s"`` from the last batch and ``"d"``
            aggregated across all batches.
        """
        all_data: list[Any] = []
        last_response: dict[str, Any] = {"s": "ok", "d": []}

        for i in range(0, len(symbols), _QUOTES_BATCH_SIZE):
            batch = symbols[i : i + _QUOTES_BATCH_SIZE]
            payload = {"symbols": ",".join(batch)}
            response = await self._call("quotes", data=payload)
            last_response = response
            if isinstance(response.get("d"), list):
                all_data.extend(response["d"])

        last_response["d"] = all_data
        return last_response

    async def get_history(
        self,
        symbol: str,
        resolution: str,
        from_ts: int,
        to_ts: int,
    ) -> dict[str, Any]:
        """Fetch OHLCV candle history for *symbol*.

        Parameters
        ----------
        symbol:
            Fyers symbol string, e.g. ``"NSE:NIFTY50-INDEX"``.
        resolution:
            Candle resolution, e.g. ``"1"`` (1 min), ``"D"`` (daily).
        from_ts:
            Start of the range as a Unix timestamp (seconds).
        to_ts:
            End of the range as a Unix timestamp (seconds).
        """
        payload = {
            "symbol": symbol,
            "resolution": resolution,
            "date_format": "0",
            "range_from": str(from_ts),
            "range_to": str(to_ts),
            "cont_flag": "1",
        }
        return await self._call("history", data=payload)

    async def get_market_depth(self, symbol: str) -> dict[str, Any]:
        """Fetch Level-2 market depth (order book) for *symbol*."""
        payload = {"symbol": symbol, "ohlcv_flag": "1"}
        return await self._call("depth", data=payload)

    async def get_profile(self) -> dict[str, Any]:
        """Fetch the authenticated user's Fyers profile."""
        return await self._call("get_profile")

    async def get_funds(self) -> dict[str, Any]:
        """Fetch fund/margin details for the authenticated account."""
        return await self._call("funds")

    async def get_positions(self) -> dict[str, Any]:
        """Fetch open positions for the authenticated account."""
        return await self._call("positions")

    async def get_holdings(self) -> dict[str, Any]:
        """Fetch equity holdings for the authenticated account."""
        return await self._call("holdings")
