"""Tests for Discord formatter."""
import discord
from outputs.discord.formatter import DiscordFormatter
from quant.config.identity import APP_NAME
from quant.utils.types import Direction


def test_format_entry_returns_embed(sample_signal):
    formatter = DiscordFormatter()
    result = formatter.format_entry(sample_signal)
    assert isinstance(result, discord.Embed)


def test_entry_embed_has_app_name(sample_signal):
    formatter = DiscordFormatter()
    embed = formatter.format_entry(sample_signal)
    assert APP_NAME in embed.title


def test_entry_embed_color_bullish(sample_signal):
    formatter = DiscordFormatter()
    embed = formatter.format_entry(sample_signal)
    assert embed.color == discord.Color.green()


def test_exit_embed(sample_signal):
    formatter = DiscordFormatter()
    embed = formatter.format_exit(sample_signal)
    assert isinstance(embed, discord.Embed)
    assert "EXIT" in embed.title
