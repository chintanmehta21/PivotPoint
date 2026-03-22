"""Single source of truth for system identity.

Change APP_NAME here to rebrand the entire system —
all outputs, logs, bot names, DB tables, and docs reference this.
"""
import os

APP_NAME: str = os.environ.get("APP_NAME", "PivotPoint")
APP_NAME_LOWER: str = APP_NAME.lower()
APP_NAME_SNAKE: str = APP_NAME.lower().replace(" ", "_")
APP_VERSION: str = "0.1.0"
APP_DESCRIPTION: str = f"{APP_NAME} — Options Trading Signal System"
