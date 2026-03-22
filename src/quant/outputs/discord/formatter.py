"""Discord-specific signal formatting using Embeds."""
from __future__ import annotations
from typing import TYPE_CHECKING

import discord

from quant.config.identity import APP_NAME, APP_VERSION
from quant.outputs.base_formatter import BaseFormatter
from quant.utils.types import Direction, SignalType

if TYPE_CHECKING:
    from quant.models.signals import SignalPayload

# Colors
COLOR_BULLISH = discord.Color.green()
COLOR_BEARISH = discord.Color.red()
COLOR_ADJUSTMENT = discord.Color.gold()


class DiscordFormatter(BaseFormatter):
    """Formats signals as Discord Embed objects."""

    def format_entry(self, signal: SignalPayload) -> discord.Embed:
        """Format entry signal as Discord Embed."""
        color = COLOR_BULLISH if signal.direction == Direction.BULLISH else COLOR_BEARISH
        embed = discord.Embed(
            title=f"[{APP_NAME}] {signal.direction.value} Entry Signal",
            description=signal.strategy_name,
            color=color,
        )
        embed.add_field(name="Strategy", value=f"{signal.strategy_name} ({signal.strategy_id})", inline=True)
        embed.add_field(name="Underlying", value=signal.underlying.value, inline=True)
        embed.add_field(name="Timeframe", value=signal.timeframe.value, inline=True)
        embed.add_field(name="R:R", value=f"{signal.risk_reward_ratio:.2f}", inline=True)
        embed.add_field(name="Confidence", value=f"{signal.confidence_score:.0f}/100", inline=True)
        embed.add_field(name="Max Profit", value=f"Rs {signal.max_profit:,.0f}", inline=True)
        embed.add_field(name="Max Loss", value=f"Rs {signal.max_loss:,.0f}", inline=True)

        # Greeks
        g = signal.greeks
        greeks_str = f"D:{g.delta:+.2f} G:{g.gamma:+.4f} V:{g.vega:+.2f} T:{g.theta:+.2f}"
        embed.add_field(name="Greeks", value=greeks_str, inline=False)

        if signal.notes:
            embed.add_field(name="Notes", value=signal.notes, inline=False)

        embed.set_footer(text=f"{APP_NAME} v{APP_VERSION}")
        embed.timestamp = signal.timestamp
        return embed

    def format_exit(self, signal: SignalPayload) -> discord.Embed:
        """Format exit signal as Discord Embed."""
        embed = discord.Embed(
            title=f"[{APP_NAME}] EXIT — {signal.strategy_name}",
            color=discord.Color.blue(),
        )
        embed.add_field(name="Strategy", value=signal.strategy_id, inline=True)
        embed.add_field(name="Underlying", value=signal.underlying.value, inline=True)
        if signal.notes:
            embed.add_field(name="Reason", value=signal.notes, inline=False)
        embed.set_footer(text=f"{APP_NAME} v{APP_VERSION}")
        embed.timestamp = signal.timestamp
        return embed

    def format_adjustment(self, signal: SignalPayload) -> discord.Embed:
        """Format adjustment signal as Discord Embed."""
        embed = discord.Embed(
            title=f"[{APP_NAME}] ADJUSTMENT — {signal.strategy_name}",
            color=COLOR_ADJUSTMENT,
        )
        embed.add_field(name="Strategy", value=signal.strategy_id, inline=True)
        embed.add_field(name="Underlying", value=signal.underlying.value, inline=True)
        if signal.notes:
            embed.add_field(name="Details", value=signal.notes, inline=False)
        embed.set_footer(text=f"{APP_NAME} v{APP_VERSION}")
        embed.timestamp = signal.timestamp
        return embed
