"""Telegram-specific signal formatting using MarkdownV2."""
from __future__ import annotations
from typing import TYPE_CHECKING

from quant.config.identity import APP_NAME, APP_VERSION
from quant.outputs.base_formatter import BaseFormatter
from quant.utils.types import Direction

if TYPE_CHECKING:
    from quant.models.signals import SignalPayload


def _escape_md(text: str) -> str:
    """Escape special characters for Telegram MarkdownV2."""
    special = r"_*[]()~`>#+-=|{}.!"
    for ch in special:
        text = text.replace(ch, f"\\{ch}")
    return text


class TelegramFormatter(BaseFormatter):
    """Formats signals as Telegram MarkdownV2 strings."""

    def format_entry(self, signal: SignalPayload) -> str:
        """Format entry signal as MarkdownV2."""
        emoji = "\U0001f7e2" if signal.direction == Direction.BULLISH else "\U0001f534"
        g = signal.greeks
        lines = [
            f"*\\[{_escape_md(APP_NAME)}\\] {emoji} {_escape_md(signal.direction.value)} Entry*",
            "",
            f"*Strategy:* {_escape_md(signal.strategy_name)} \\({_escape_md(signal.strategy_id)}\\)",
            f"*Underlying:* {_escape_md(signal.underlying.value)}",
            f"*Timeframe:* {_escape_md(signal.timeframe.value)}",
            f"*R:R:* {signal.risk_reward_ratio:.2f}",
            f"*Confidence:* {signal.confidence_score:.0f}/100",
            f"*Max Profit:* Rs {signal.max_profit:,.0f}",
            f"*Max Loss:* Rs {signal.max_loss:,.0f}",
            "",
            f"*Greeks:* D:{g.delta:+.2f} G:{g.gamma:+.4f} V:{g.vega:+.2f} T:{g.theta:+.2f}",
        ]
        if signal.notes:
            lines.append(f"\n_{_escape_md(signal.notes)}_")
        lines.append(f"\n`{APP_NAME} v{APP_VERSION}`")
        return "\n".join(lines)

    def format_exit(self, signal: SignalPayload) -> str:
        """Format exit signal as MarkdownV2."""
        lines = [
            f"*\\[{_escape_md(APP_NAME)}\\] EXIT*",
            f"*Strategy:* {_escape_md(signal.strategy_name)}",
        ]
        if signal.notes:
            lines.append(f"*Reason:* {_escape_md(signal.notes)}")
        return "\n".join(lines)

    def format_adjustment(self, signal: SignalPayload) -> str:
        """Format adjustment signal as MarkdownV2."""
        lines = [
            f"*\\[{_escape_md(APP_NAME)}\\] ADJUSTMENT*",
            f"*Strategy:* {_escape_md(signal.strategy_name)}",
        ]
        if signal.notes:
            lines.append(f"*Details:* {_escape_md(signal.notes)}")
        return "\n".join(lines)
