"""Shared type aliases and enums for the trading system."""
from decimal import Decimal
from enum import Enum
from typing import TypeAlias

class OptionType(str, Enum):
    CE = "CE"
    PE = "PE"

class Direction(str, Enum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"

class TimeFrame(str, Enum):
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    QUARTERLY = "QUARTERLY"

class SignalType(str, Enum):
    ENTRY = "ENTRY"
    EXIT = "EXIT"
    ADJUSTMENT = "ADJUSTMENT"

class Side(str, Enum):
    BUY = "BUY"
    SELL = "SELL"

class Underlying(str, Enum):
    NIFTY = "NIFTY"
    BANKNIFTY = "BANKNIFTY"

# Type aliases
Strike: TypeAlias = Decimal
Premium: TypeAlias = Decimal
