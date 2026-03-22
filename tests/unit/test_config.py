"""Tests for configuration management."""
from quant.config.settings import Settings


def test_settings_loads():
    settings = Settings()
    assert settings.log_level in ("DEBUG", "INFO", "WARNING", "ERROR")


def test_settings_has_nested_groups():
    settings = Settings()
    assert hasattr(settings, "discord")
    assert hasattr(settings, "telegram")
    assert hasattr(settings, "database")
    assert hasattr(settings, "risk")
    assert hasattr(settings, "fyers")


def test_risk_defaults():
    settings = Settings()
    assert settings.risk.max_positions_per_underlying == 3
    assert settings.risk.vix_high_threshold == 20.0
