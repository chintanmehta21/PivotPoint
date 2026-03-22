"""Discord alert bot for signal dispatch."""
from __future__ import annotations
from typing import TYPE_CHECKING

import structlog

from quant.config.identity import APP_NAME
from quant.config.settings import settings
from outputs.discord.formatter import DiscordFormatter

if TYPE_CHECKING:
    from quant.models.signals import SignalPayload

logger = structlog.get_logger()


class DiscordAlertBot:
    """Dispatches signals to Discord via bot or webhook."""

    def __init__(self) -> None:
        self._formatter = DiscordFormatter()
        self._token = settings.discord.bot_token
        self._channel_id = settings.discord.channel_id

    async def send_signal(self, signal: SignalPayload) -> None:
        """Send a signal to the configured Discord channel."""
        if not self._token:
            logger.warning("Discord bot token not configured", app=APP_NAME)
            return

        from quant.utils.types import SignalType

        if signal.signal_type == SignalType.ENTRY:
            embed = self._formatter.format_entry(signal)
        elif signal.signal_type == SignalType.EXIT:
            embed = self._formatter.format_exit(signal)
        else:
            embed = self._formatter.format_adjustment(signal)

        # TODO: Implement actual Discord API call
        logger.info(
            "Discord signal prepared",
            strategy=signal.strategy_id,
            channel=self._channel_id,
            embed_title=embed.title,
        )
