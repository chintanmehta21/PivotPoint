"""Async signal router — dispatches signals to all output channels."""
from __future__ import annotations
import asyncio
from typing import TYPE_CHECKING, Protocol

import structlog

from pivotpoint.config.identity import APP_NAME

if TYPE_CHECKING:
    from pivotpoint.models.signals import SignalPayload

logger = structlog.get_logger()


class OutputChannel(Protocol):
    """Protocol for output channels (Discord, Telegram, DB)."""
    async def send_signal(self, signal: SignalPayload) -> None: ...


class SignalRouter:
    """Routes signals to registered output channels with error isolation."""

    def __init__(self) -> None:
        self._channels: list[OutputChannel] = []

    def register_channel(self, channel: OutputChannel) -> None:
        """Register an output channel."""
        self._channels.append(channel)

    async def dispatch(self, signal: SignalPayload) -> None:
        """Dispatch signal to all channels concurrently. Errors isolated per channel."""
        if not self._channels:
            logger.warning("No output channels registered", app=APP_NAME)
            return

        tasks = [self._safe_send(ch, signal) for ch in self._channels]
        await asyncio.gather(*tasks)

    async def _safe_send(self, channel: OutputChannel, signal: SignalPayload) -> None:
        """Send to a channel with error isolation."""
        try:
            await channel.send_signal(signal)
            logger.info("Signal dispatched", channel=type(channel).__name__, strategy=signal.strategy_id)
        except Exception as e:
            logger.error(
                "Channel dispatch failed",
                channel=type(channel).__name__,
                strategy=signal.strategy_id,
                error=str(e),
            )
