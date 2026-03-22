"""Tests for system identity configuration."""
import os


def test_default_app_name():
    from quant.config.identity import APP_NAME
    assert APP_NAME == os.environ.get("APP_NAME", "PivotPoint")


def test_app_version_format():
    from quant.config.identity import APP_VERSION
    parts = APP_VERSION.split(".")
    assert len(parts) == 3


def test_app_name_derivatives():
    from quant.config.identity import APP_NAME, APP_NAME_LOWER, APP_NAME_SNAKE
    assert APP_NAME_LOWER == APP_NAME.lower()
    assert APP_NAME_SNAKE == APP_NAME.lower().replace(" ", "_")
