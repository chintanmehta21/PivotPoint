from decimal import Decimal
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict
import sys

class DiscordSettings(BaseModel):
    bot_token: str = ""
    channel_id: str = ""

class TelegramSettings(BaseModel):
    bot_token: str = ""
    chat_id: str = ""

class DatabaseSettings(BaseModel):
    url: str = "sqlite+aiosqlite:///pivotpoint.db"

class RiskSettings(BaseModel):
    max_portfolio_loss: Decimal = Decimal("50000")
    max_positions_per_underlying: int = 3
    vix_high_threshold: float = 20.0
    vix_low_threshold: float = 14.0

class FyersSettings(BaseModel):
    """Fyers API operational configuration."""
    secrets_path: str = "secrets/fyers"
    ws_reconnect_max_delay: int = 30
    ws_max_symbols: int = 200
    quotes_batch_size: int = 50
    rate_limit_per_sec: int = 10
    rate_limit_per_min: int = 200
    risk_free_rate: float = 0.065
    cache_dir: str = "data/candles"
    strike_range_nifty: int = 500
    strike_interval_nifty: int = 50
    strike_range_banknifty: int = 500
    strike_interval_banknifty: int = 100
    lot_size_nifty: int = 75
    lot_size_banknifty: int = 15

class Settings(BaseSettings):
    discord: DiscordSettings = DiscordSettings()
    telegram: TelegramSettings = TelegramSettings()
    database: DatabaseSettings = DatabaseSettings()
    risk: RiskSettings = RiskSettings()
    fyers: FyersSettings = FyersSettings()
    log_level: str = "INFO"
    environment: str = "local"

    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        env_file=".env",
        env_file_encoding="utf-8",
    )

try:
    settings = Settings()
except Exception as e:
    print(f"Configuration error: {e}", file=sys.stderr)
    sys.exit(1)
