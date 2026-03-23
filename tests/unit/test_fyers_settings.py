from quant.config.settings import FyersSettings

def test_fyers_settings_defaults():
    s = FyersSettings()
    assert s.secrets_path == "secrets/fyers"
    assert s.ws_max_symbols == 200
    assert s.quotes_batch_size == 50
    assert s.rate_limit_per_sec == 10
    assert s.rate_limit_per_min == 200
    assert s.risk_free_rate == 0.065
    assert s.cache_dir == "data/candles"
    assert s.strike_range_nifty == 500
    assert s.strike_interval_nifty == 50
    assert s.strike_range_banknifty == 500
    assert s.strike_interval_banknifty == 100
    assert s.lot_size_nifty == 75
    assert s.lot_size_banknifty == 15
    assert s.ws_reconnect_max_delay == 30

def test_fyers_settings_no_longer_has_credentials():
    s = FyersSettings()
    assert not hasattr(s, "app_id")
    assert not hasattr(s, "secret_key")
    assert not hasattr(s, "redirect_url")
