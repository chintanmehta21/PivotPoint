"""Telegram alert bot for signal dispatch."""
from __future__ import annotations
from typing import TYPE_CHECKING

import structlog

from pivotpoint.config.identity import APP_NAME
from pivotpoint.config.settings import settings
from pivotpoint.outputs.telegram.formatter import TelegramFormatter

if TYPE_CHECKING:
    from pivotpoint.models.signals import SignalPayload

logger = structlog.get_logger()


class TelegramAlertBot:
    """Dispatches signals to Telegram."""

    def __init__(self) -> None:
        self._formatter = TelegramFormatter()
        self._token = settings.telegram.bot_token
        self._chat_id = settings.telegram.chat_id

    async def send_signal(self, signal: SignalPayload) -> None:
        """Send a signal to the configured Telegram chat."""
        if not self._token:
            logger.warning("Telegram bot token not configured", app=APP_NAME)
            return

        from pivotpoint.utils.types import SignalType

        if signal.signal_type == SignalType.ENTRY:
            text = self._formatter.format_entry(signal)
        elif signal.signal_type == SignalType.EXIT:
            text = self._formatter.format_exit(signal)
        else:
            text = self._formatter.format_adjustment(signal)

        # TODO: Implement actual Telegram API call
        logger.info(
            "Telegram signal prepared",
            strategy=signal.strategy_id,
            chat_id=self._chat_id,
        )
