"""Tests for Fyers option symbol builder and parser."""
from datetime import date

import pytest

from quant.data.fyers.symbols import (
    MONTH_CODES,
    INDEX_SYMBOLS,
    VIX_SYMBOL,
    build_option_symbol,
    build_chain_symbols,
    parse_option_symbol,
)
from quant.utils.types import Underlying


# ---------------------------------------------------------------------------
# MONTH_CODES
# ---------------------------------------------------------------------------

class TestMonthCodes:
    def test_months_1_to_9_are_digit_strings(self):
        for m in range(1, 10):
            assert MONTH_CODES[m] == str(m), f"Month {m} should map to '{m}'"

    def test_october_is_O(self):
        assert MONTH_CODES[10] == "O"

    def test_november_is_N(self):
        assert MONTH_CODES[11] == "N"

    def test_december_is_D(self):
        assert MONTH_CODES[12] == "D"

    def test_all_12_months_present(self):
        assert set(MONTH_CODES.keys()) == set(range(1, 13))

    def test_all_values_are_single_characters(self):
        for m, code in MONTH_CODES.items():
            assert len(code) == 1, f"Month {m} code '{code}' must be a single character"


# ---------------------------------------------------------------------------
# INDEX_SYMBOLS
# ---------------------------------------------------------------------------

class TestIndexSymbols:
    def test_nifty_index_symbol(self):
        assert INDEX_SYMBOLS[Underlying.NIFTY] == "NSE:NIFTY50-INDEX"

    def test_banknifty_index_symbol(self):
        assert INDEX_SYMBOLS[Underlying.BANKNIFTY] == "NSE:NIFTYBANK-INDEX"

    def test_both_underlyings_present(self):
        assert Underlying.NIFTY in INDEX_SYMBOLS
        assert Underlying.BANKNIFTY in INDEX_SYMBOLS


# ---------------------------------------------------------------------------
# VIX_SYMBOL
# ---------------------------------------------------------------------------

class TestVixSymbol:
    def test_vix_symbol_value(self):
        assert VIX_SYMBOL == "NSE:INDIAVIX-INDEX"


# ---------------------------------------------------------------------------
# build_option_symbol
# ---------------------------------------------------------------------------

class TestBuildOptionSymbol:
    def test_nifty_march_call(self):
        # NIFTY March 27 2026 CE 24000 → NSE:NIFTY2632724000CE
        expiry = date(2026, 3, 27)
        symbol = build_option_symbol(Underlying.NIFTY, expiry, 24000, "CE")
        assert symbol == "NSE:NIFTY2632724000CE"

    def test_banknifty_november_put(self):
        # BANKNIFTY Nov 6 2026 PE 52000 → NSE:BANKNIFTY26N0652000PE
        expiry = date(2026, 11, 6)
        symbol = build_option_symbol(Underlying.BANKNIFTY, expiry, 52000, "PE")
        assert symbol == "NSE:BANKNIFTY26N0652000PE"

    def test_nifty_october_call(self):
        # NIFTY Oct 1 2026 CE 25000 → NSE:NIFTY26O0125000CE
        expiry = date(2026, 10, 1)
        symbol = build_option_symbol(Underlying.NIFTY, expiry, 25000, "CE")
        assert symbol == "NSE:NIFTY26O0125000CE"

    def test_nifty_december_put(self):
        # NIFTY Dec 31 2026 PE 23000 → NSE:NIFTY26D3123000PE
        expiry = date(2026, 12, 31)
        symbol = build_option_symbol(Underlying.NIFTY, expiry, 23000, "PE")
        assert symbol == "NSE:NIFTY26D3123000PE"

    def test_banknifty_january_call(self):
        # BANKNIFTY Jan 2 2026 CE 48000 → NSE:BANKNIFTY2610248000CE
        # Format: YY=26, M=1 (January code), DD=02
        expiry = date(2026, 1, 2)
        symbol = build_option_symbol(Underlying.BANKNIFTY, expiry, 48000, "CE")
        assert symbol == "NSE:BANKNIFTY2610248000CE"

    def test_nifty_september_call(self):
        # NIFTY Sep 10 2026 CE 22000 → NSE:NIFTY269 1022000CE
        # Month 9 → "9"
        expiry = date(2026, 9, 10)
        symbol = build_option_symbol(Underlying.NIFTY, expiry, 22000, "CE")
        assert symbol == "NSE:NIFTY2691022000CE"

    def test_day_is_zero_padded(self):
        expiry = date(2026, 3, 5)
        symbol = build_option_symbol(Underlying.NIFTY, expiry, 24000, "CE")
        # Day 5 → "05"
        assert symbol == "NSE:NIFTY2630524000CE"

    def test_uses_two_digit_year(self):
        # Year 2027 → "27"
        expiry = date(2027, 3, 27)
        symbol = build_option_symbol(Underlying.NIFTY, expiry, 24000, "CE")
        assert symbol.startswith("NSE:NIFTY27")

    def test_underlying_name_in_symbol(self):
        expiry = date(2026, 3, 27)
        sym_nifty = build_option_symbol(Underlying.NIFTY, expiry, 24000, "CE")
        sym_bn = build_option_symbol(Underlying.BANKNIFTY, expiry, 48000, "CE")
        assert "NIFTY" in sym_nifty
        assert "BANKNIFTY" in sym_bn

    def test_option_type_ce_and_pe(self):
        expiry = date(2026, 3, 27)
        sym_ce = build_option_symbol(Underlying.NIFTY, expiry, 24000, "CE")
        sym_pe = build_option_symbol(Underlying.NIFTY, expiry, 24000, "PE")
        assert sym_ce.endswith("CE")
        assert sym_pe.endswith("PE")


# ---------------------------------------------------------------------------
# build_chain_symbols
# ---------------------------------------------------------------------------

class TestBuildChainSymbols:
    def test_nifty_atm_24000_default_range_interval(self):
        # NIFTY: range=500, interval=50 → 500/50 = 10 steps each side
        # strikes: 23500, 23550, ..., 24000, ..., 24450, 24500 → 21 strikes × 2 types = 42 symbols
        expiry = date(2026, 3, 27)
        symbols = build_chain_symbols(Underlying.NIFTY, expiry, 24000)
        assert len(symbols) == 42

    def test_banknifty_default_range_interval(self):
        # BANKNIFTY: range=500, interval=100 → 500/100 = 5 steps each side
        # strikes: 51500, 51600, ..., 52000, ..., 52400, 52500 → 11 strikes × 2 types = 22 symbols
        expiry = date(2026, 11, 6)
        symbols = build_chain_symbols(Underlying.BANKNIFTY, expiry, 52000)
        assert len(symbols) == 22

    def test_nifty_contains_atm_call(self):
        expiry = date(2026, 3, 27)
        symbols = build_chain_symbols(Underlying.NIFTY, expiry, 24000)
        atm_ce = build_option_symbol(Underlying.NIFTY, expiry, 24000, "CE")
        assert atm_ce in symbols

    def test_nifty_contains_atm_put(self):
        expiry = date(2026, 3, 27)
        symbols = build_chain_symbols(Underlying.NIFTY, expiry, 24000)
        atm_pe = build_option_symbol(Underlying.NIFTY, expiry, 24000, "PE")
        assert atm_pe in symbols

    def test_banknifty_contains_atm_symbols(self):
        expiry = date(2026, 11, 6)
        symbols = build_chain_symbols(Underlying.BANKNIFTY, expiry, 52000)
        atm_ce = build_option_symbol(Underlying.BANKNIFTY, expiry, 52000, "CE")
        atm_pe = build_option_symbol(Underlying.BANKNIFTY, expiry, 52000, "PE")
        assert atm_ce in symbols
        assert atm_pe in symbols

    def test_custom_range_and_interval(self):
        # range=200, interval=100 → 200/100 = 2 steps each side
        # strikes: 23800, 23900, 24000, 24100, 24200 → 5 strikes × 2 = 10 symbols
        expiry = date(2026, 3, 27)
        symbols = build_chain_symbols(Underlying.NIFTY, expiry, 24000, strike_range=200, strike_interval=100)
        assert len(symbols) == 10

    def test_custom_range_interval_boundary(self):
        # range=100, interval=50 → 2 steps each side → 5 strikes × 2 = 10 symbols
        expiry = date(2026, 3, 27)
        symbols = build_chain_symbols(Underlying.NIFTY, expiry, 24000, strike_range=100, strike_interval=50)
        assert len(symbols) == 10

    def test_lowest_strike_present(self):
        expiry = date(2026, 3, 27)
        symbols = build_chain_symbols(Underlying.NIFTY, expiry, 24000)
        low_ce = build_option_symbol(Underlying.NIFTY, expiry, 23500, "CE")
        assert low_ce in symbols

    def test_highest_strike_present(self):
        expiry = date(2026, 3, 27)
        symbols = build_chain_symbols(Underlying.NIFTY, expiry, 24000)
        high_pe = build_option_symbol(Underlying.NIFTY, expiry, 24500, "PE")
        assert high_pe in symbols

    def test_all_symbols_are_strings(self):
        expiry = date(2026, 3, 27)
        symbols = build_chain_symbols(Underlying.NIFTY, expiry, 24000)
        assert all(isinstance(s, str) for s in symbols)

    def test_no_duplicate_symbols(self):
        expiry = date(2026, 3, 27)
        symbols = build_chain_symbols(Underlying.NIFTY, expiry, 24000)
        assert len(symbols) == len(set(symbols))


# ---------------------------------------------------------------------------
# parse_option_symbol
# ---------------------------------------------------------------------------

class TestParseOptionSymbol:
    def test_parse_nifty_march_call(self):
        symbol = "NSE:NIFTY2632724000CE"
        underlying, expiry, strike, option_type = parse_option_symbol(symbol)
        assert underlying == Underlying.NIFTY
        assert expiry == date(2026, 3, 27)
        assert strike == 24000
        assert option_type == "CE"

    def test_parse_banknifty_november_put(self):
        symbol = "NSE:BANKNIFTY26N0652000PE"
        underlying, expiry, strike, option_type = parse_option_symbol(symbol)
        assert underlying == Underlying.BANKNIFTY
        assert expiry == date(2026, 11, 6)
        assert strike == 52000
        assert option_type == "PE"

    def test_roundtrip_nifty(self):
        expiry = date(2026, 3, 27)
        original = build_option_symbol(Underlying.NIFTY, expiry, 24000, "CE")
        underlying, parsed_expiry, strike, option_type = parse_option_symbol(original)
        assert underlying == Underlying.NIFTY
        assert parsed_expiry == expiry
        assert strike == 24000
        assert option_type == "CE"

    def test_roundtrip_banknifty(self):
        expiry = date(2026, 11, 6)
        original = build_option_symbol(Underlying.BANKNIFTY, expiry, 52000, "PE")
        underlying, parsed_expiry, strike, option_type = parse_option_symbol(original)
        assert underlying == Underlying.BANKNIFTY
        assert parsed_expiry == expiry
        assert strike == 52000
        assert option_type == "PE"

    def test_roundtrip_all_12_months(self):
        base_day = 15
        strike = 24000
        for month in range(1, 13):
            expiry = date(2026, month, base_day)
            built = build_option_symbol(Underlying.NIFTY, expiry, strike, "CE")
            underlying, parsed_expiry, parsed_strike, parsed_type = parse_option_symbol(built)
            assert underlying == Underlying.NIFTY, f"Month {month}: underlying mismatch"
            assert parsed_expiry == expiry, f"Month {month}: expiry mismatch — built '{built}', got {parsed_expiry}"
            assert parsed_strike == strike, f"Month {month}: strike mismatch"
            assert parsed_type == "CE", f"Month {month}: option_type mismatch"

    def test_parse_returns_int_strike(self):
        symbol = "NSE:NIFTY2632724000CE"
        _, _, strike, _ = parse_option_symbol(symbol)
        assert isinstance(strike, int)

    def test_parse_returns_date_expiry(self):
        symbol = "NSE:NIFTY2632724000CE"
        _, expiry, _, _ = parse_option_symbol(symbol)
        assert isinstance(expiry, date)

    def test_parse_invalid_symbol_raises(self):
        with pytest.raises((ValueError, AttributeError)):
            parse_option_symbol("INVALID_SYMBOL")

    def test_parse_october_symbol(self):
        expiry = date(2026, 10, 1)
        built = build_option_symbol(Underlying.NIFTY, expiry, 25000, "CE")
        assert "O" in built  # October code
        underlying, parsed_expiry, strike, option_type = parse_option_symbol(built)
        assert parsed_expiry == expiry
        assert strike == 25000

    def test_parse_december_symbol(self):
        expiry = date(2026, 12, 31)
        built = build_option_symbol(Underlying.NIFTY, expiry, 23000, "PE")
        assert "D" in built  # December code
        underlying, parsed_expiry, strike, option_type = parse_option_symbol(built)
        assert parsed_expiry == expiry
        assert strike == 23000
