"""NSE market hours and IST timezone constants."""

from datetime import time
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")

MARKET_OPEN = time(9, 15)
MARKET_CLOSE = time(15, 30)
PRE_MARKET_OPEN = time(9, 0)
PRE_MARKET_CLOSE = time(9, 8)
