"""Fyers option symbol format builder and parser.

Fyers option symbol format:
    NSE:{UNDERLYING}{YY}{M}{DD}{STRIKE}{TYPE}

Where:
    YY     = 2-digit year (e.g. 2026 → "26")
    M      = month code: "1"-"9" for Jan-Sep, "O" for Oct, "N" for Nov, "D" for Dec
    DD     = 2-digit zero-padded day (e.g. 6 → "06")
    STRIKE = integer strike price (no padding)
    TYPE   = "CE" or "PE"

Examples:
    NIFTY  2026-03-27 CE 24000 → NSE:NIFTY2632724000CE
    BANKNIFTY 2026-11-06 PE 52000 → NSE:BANKNIFTY26N0652000PE
"""

from __future__ import annotations

import re
from datetime import date
from typing import Dict

from quant.utils.types import Underlying

# ---------------------------------------------------------------------------
# Month codes
# ---------------------------------------------------------------------------

MONTH_CODES: Dict[int, str] = {
    1: "1", 2: "2", 3: "3", 4: "4",
    5: "5", 6: "6", 7: "7", 8: "8",
    9: "9", 10: "O", 11: "N", 12: "D",
}

# Reverse mapping: single-char code → month number (used in parse)
_MONTH_CODE_TO_INT: Dict[str, int] = {v: k for k, v in MONTH_CODES.items()}

# ---------------------------------------------------------------------------
# Index and VIX symbols
# ---------------------------------------------------------------------------

INDEX_SYMBOLS: Dict[Underlying, str] = {
    Underlying.NIFTY: "NSE:NIFTY50-INDEX",
    Underlying.BANKNIFTY: "NSE:NIFTYBANK-INDEX",
}

VIX_SYMBOL: str = "NSE:INDIAVIX-INDEX"

# ---------------------------------------------------------------------------
# Default chain parameters per underlying
# ---------------------------------------------------------------------------

_DEFAULT_RANGE: Dict[Underlying, int] = {
    Underlying.NIFTY: 500,
    Underlying.BANKNIFTY: 500,
}

_DEFAULT_INTERVAL: Dict[Underlying, int] = {
    Underlying.NIFTY: 50,
    Underlying.BANKNIFTY: 100,
}

# ---------------------------------------------------------------------------
# build_option_symbol
# ---------------------------------------------------------------------------

def build_option_symbol(
    underlying: Underlying,
    expiry: date,
    strike: int,
    option_type: str,
) -> str:
    """Build a Fyers-format option symbol string.

    Args:
        underlying:  NIFTY or BANKNIFTY
        expiry:      Option expiry date
        strike:      Strike price (integer)
        option_type: "CE" or "PE"

    Returns:
        Fyers symbol string, e.g. "NSE:NIFTY2632724000CE"
    """
    yy = f"{expiry.year % 100:02d}"
    m_code = MONTH_CODES[expiry.month]
    dd = f"{expiry.day:02d}"
    return f"NSE:{underlying.value}{yy}{m_code}{dd}{strike}{option_type}"


# ---------------------------------------------------------------------------
# build_chain_symbols
# ---------------------------------------------------------------------------

def build_chain_symbols(
    underlying: Underlying,
    expiry: date,
    atm_strike: int,
    strike_range: int | None = None,
    strike_interval: int | None = None,
) -> list[str]:
    """Build a list of Fyers option symbols covering a range around the ATM strike.

    Args:
        underlying:       NIFTY or BANKNIFTY
        expiry:           Option expiry date
        atm_strike:       The at-the-money strike (centre of the chain)
        strike_range:     Total range on each side in points. Defaults to 500 for
                          both NIFTY and BANKNIFTY.
        strike_interval:  Interval between adjacent strikes. Defaults to 50 for
                          NIFTY, 100 for BANKNIFTY.

    Returns:
        List of Fyers symbol strings for every CE and PE across the range.
        Ordered from lowest to highest strike, CE before PE per strike.
    """
    r = strike_range if strike_range is not None else _DEFAULT_RANGE[underlying]
    i = strike_interval if strike_interval is not None else _DEFAULT_INTERVAL[underlying]

    symbols: list[str] = []
    steps = r // i
    for step in range(-steps, steps + 1):
        k = atm_strike + step * i
        symbols.append(build_option_symbol(underlying, expiry, k, "CE"))
        symbols.append(build_option_symbol(underlying, expiry, k, "PE"))
    return symbols


# ---------------------------------------------------------------------------
# parse_option_symbol
# ---------------------------------------------------------------------------

# Regex captures:
#   name  = underlying name (NIFTY or BANKNIFTY)
#   yy    = 2-digit year
#   m     = single-char month code
#   dd    = 2-digit day
#   strike= digits
#   type  = CE or PE
_SYMBOL_RE = re.compile(
    r"^NSE:(?P<name>BANKNIFTY|NIFTY)"
    r"(?P<yy>\d{2})"
    r"(?P<m>[1-9OND])"
    r"(?P<dd>\d{2})"
    r"(?P<strike>\d+)"
    r"(?P<type>CE|PE)$"
)


def parse_option_symbol(symbol: str) -> tuple[Underlying, date, int, str]:
    """Parse a Fyers option symbol string back into its components.

    Args:
        symbol: A Fyers-format option symbol, e.g. "NSE:NIFTY2632724000CE"

    Returns:
        Tuple of (underlying, expiry_date, strike, option_type)

    Raises:
        ValueError: If the symbol does not match the expected format.
    """
    m = _SYMBOL_RE.match(symbol)
    if m is None:
        raise ValueError(f"Cannot parse Fyers symbol: {symbol!r}")

    underlying = Underlying(m.group("name"))
    year = 2000 + int(m.group("yy"))
    month = _MONTH_CODE_TO_INT[m.group("m")]
    day = int(m.group("dd"))
    expiry = date(year, month, day)
    strike = int(m.group("strike"))
    option_type = m.group("type")

    return underlying, expiry, strike, option_type
