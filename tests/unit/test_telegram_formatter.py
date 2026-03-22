"""Tests for Telegram formatter."""
from quant.outputs.telegram.formatter import TelegramFormatter
from quant.config.identity import APP_NAME


def test_format_entry_returns_string(sample_signal):
    formatter = TelegramFormatter()
    result = formatter.format_entry(sample_signal)
    assert isinstance(result, str)


def test_entry_contains_app_name(sample_signal):
    formatter = TelegramFormatter()
    result = formatter.format_entry(sample_signal)
    assert APP_NAME in result


def test_entry_contains_strategy(sample_signal):
    formatter = TelegramFormatter()
    result = formatter.format_entry(sample_signal)
    assert "Test Strategy" in result or "TEST1" in result


def test_exit_format(sample_signal):
    formatter = TelegramFormatter()
    result = formatter.format_exit(sample_signal)
    assert "EXIT" in result
