"""Fyers WebSocket manager with auto-reconnect and price cache.

Wraps FyersDataSocket to provide a clean async-friendly interface with:
- Thread-safe price cache keyed by symbol
- Auto-resubscription on reconnect
- Configurable callbacks for price updates and disconnections
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any, Callable

log = logging.getLogger(__name__)

# Maximum symbols Fyers WebSocket supports per connection
_MAX_SYMBOLS = 200


class FyersWebSocket:
    """Managed WebSocket connection to the Fyers market data feed.

    Parameters
    ----------
    auth:
        A ``FyersAuth`` instance (or compatible mock) that provides
        ``get_valid_token()`` and ``._credentials["app_id"]``.
    on_price_update:
        Callable invoked with the raw message dict on every tick.
    on_disconnect:
        Callable invoked (no arguments) when the connection closes.
    """

    def __init__(
        self,
        auth: Any,
        *,
        on_price_update: Callable[[dict], None],
        on_disconnect: Callable[[], None],
    ) -> None:
        self._auth = auth
        self._on_price_update = on_price_update
        self._on_disconnect_cb = on_disconnect

        # Public state
        self.subscribed_symbols: set[str] = set()
        self.price_cache: dict[str, dict] = {}
        self.last_update: dict[str, datetime] = {}

        # Internal state
        self._connected: bool = False
        self._socket: Any = None
        self._loop: asyncio.AbstractEventLoop | None = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def connect(self) -> None:
        """Open the WebSocket connection to Fyers market data feed.

        Builds the ``access_token`` in ``APPID:token`` format required by
        ``FyersDataSocket``, then starts the connection with lite-mode
        disabled and auto-reconnect enabled.
        """
        from fyers_apiv3.FyersWebsocket import data_ws  # type: ignore[import]

        token = self._auth.get_valid_token()
        app_id = self._auth._credentials["app_id"]
        access_token = f"{app_id}:{token}"

        self._socket = data_ws.FyersDataSocket(
            access_token=access_token,
            log_path="",
            litemode=False,
            message_handler=self._on_message,
            reconnect=True,
            on_connect=self._on_connect,
            on_close=self._on_close,
        )
        # Capture the running loop if we are inside an async context
        try:
            self._loop = asyncio.get_event_loop()
        except RuntimeError:
            self._loop = None

        self._socket.connect()

    def subscribe(self, symbols: list[str]) -> None:
        """Subscribe to market data for *symbols*.

        Parameters
        ----------
        symbols:
            List of Fyers symbol strings, e.g. ``["NSE:NIFTY50-INDEX"]``.

        Raises
        ------
        ValueError:
            If the total number of subscribed symbols would exceed 200.
        """
        prospective = self.subscribed_symbols | set(symbols)
        if len(prospective) > _MAX_SYMBOLS:
            raise ValueError(
                f"Cannot subscribe to more than {_MAX_SYMBOLS} symbols; "
                f"requested total would be {len(prospective)}."
            )
        self.subscribed_symbols = prospective
        if self._connected and self._socket is not None:
            self._socket.subscribe(symbols=list(symbols), data_type="SymbolUpdate")

    def unsubscribe(self, symbols: list[str]) -> None:
        """Unsubscribe from market data for *symbols*.

        Parameters
        ----------
        symbols:
            List of previously-subscribed symbol strings to remove.
        """
        for sym in symbols:
            self.subscribed_symbols.discard(sym)
        if self._connected and self._socket is not None:
            self._socket.unsubscribe(symbols=list(symbols))

    def disconnect(self) -> None:
        """Close the WebSocket connection gracefully."""
        if self._socket is not None:
            self._socket.close_connection()

    def is_connected(self) -> bool:
        """Return ``True`` if the WebSocket is currently connected."""
        return self._connected

    # ------------------------------------------------------------------
    # Socket callbacks
    # ------------------------------------------------------------------

    def _on_connect(self) -> None:
        """Called by the Fyers SDK when the connection is established."""
        log.info("FyersWebSocket connected.")
        self._connected = True
        # Re-subscribe to any symbols tracked before a reconnect
        if self.subscribed_symbols and self._socket is not None:
            self._socket.subscribe(
                symbols=list(self.subscribed_symbols), data_type="SymbolUpdate"
            )

    def _on_close(self) -> None:
        """Called by the Fyers SDK when the connection closes."""
        log.info("FyersWebSocket disconnected.")
        self._connected = False
        if self._loop is not None and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._on_disconnect_cb)
        else:
            self._on_disconnect_cb()

    def _on_message(self, msg: dict) -> None:
        """Thread-safe bridge from the Fyers SDK thread to the event loop.

        If an asyncio event loop is running, schedules ``_handle_message``
        via ``call_soon_threadsafe``; otherwise calls it directly.
        """
        if self._loop is not None and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._handle_message, msg)
        else:
            self._handle_message(msg)

    def _handle_message(self, msg: dict) -> None:
        """Update the price cache and fire the on_price_update callback."""
        symbol = msg.get("symbol")
        if symbol is None:
            return

        self.price_cache[symbol] = msg
        self.last_update[symbol] = datetime.now()
        self._on_price_update(msg)
