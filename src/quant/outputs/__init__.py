"""Output channels for signal dispatch."""
from quant.outputs.base_formatter import BaseFormatter
from quant.outputs.discord import DiscordFormatter, DiscordAlertBot
from quant.outputs.telegram import TelegramFormatter, TelegramAlertBot
from quant.outputs.website import DatabaseWriter

__all__ = [
    "BaseFormatter", "DiscordFormatter", "DiscordAlertBot",
    "TelegramFormatter", "TelegramAlertBot", "DatabaseWriter",
]
