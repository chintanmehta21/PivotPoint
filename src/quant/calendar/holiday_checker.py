"""Layered holiday detection for NSE India.

Deviation from spec: YAML overrides checked first (not last) so manual
force-OPEN/force-HOLIDAY always wins regardless of other layers.

Layer 1: Weekend check (Saturday/Sunday)
Layer 2: exchange_calendars XBOM.is_session()
Layer 3: NSE API fetch (cached daily)
Layer 4: holidays.yaml manual overrides (checked first, highest priority)
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Any

import exchange_calendars as ec
import httpx
import structlog
import yaml

from quant.config.identity import APP_NAME

logger = structlog.get_logger()

_HOLIDAYS_YAML = Path(__file__).resolve().parent.parent / "config" / "holidays.yaml"
_NSE_HOLIDAY_URL = "https://www.nseindia.com/api/holiday-master?type=trading"
_NSE_HEADERS = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}


class HolidayChecker:
    """Determines if a given date is an NSE trading day."""

    def __init__(self) -> None:
        self._xbom = ec.get_calendar("XBOM")
        self._overrides = self._load_overrides()
        self._nse_cache: dict[int, list[dict[str, str]]] | None = None

    def is_trading_day(self, target: dt.date) -> bool:
        """Check all layers. Returns True if market is open."""
        # YAML overrides checked first — highest priority
        override = self._check_override(target)
        if override is not None:
            return override

        # Layer 1: weekends
        if target.weekday() >= 5:
            return False

        # Layer 2: exchange_calendars
        ts = dt.datetime(target.year, target.month, target.day)
        xbom_open = self._xbom.is_session(ts)

        # Layer 3: NSE API cross-validation
        nse_holiday = self._check_nse_api(target)
        if nse_holiday is True:
            return False
        if nse_holiday is False:
            return True
        return xbom_open

    def get_holiday_name(self, target: dt.date) -> str | None:
        override_name = self._get_override_name(target)
        if override_name:
            return override_name
        return self._get_nse_holiday_name(target)

    def get_next_trading_day(self, target: dt.date) -> dt.date:
        candidate = target + dt.timedelta(days=1)
        for _ in range(10):
            if self.is_trading_day(candidate):
                return candidate
            candidate += dt.timedelta(days=1)
        days_until_monday = (7 - candidate.weekday()) % 7 or 7
        return candidate + dt.timedelta(days=days_until_monday)

    def get_previous_trading_day(self, target: dt.date) -> dt.date:
        candidate = target - dt.timedelta(days=1)
        for _ in range(10):
            if self.is_trading_day(candidate):
                return candidate
            candidate -= dt.timedelta(days=1)
        return candidate

    def _check_nse_api(self, target: dt.date) -> bool | None:
        try:
            entries = self._fetch_nse_holidays(target.year)
            date_str = target.strftime("%d-%b-%Y")
            return any(e["tradingDate"] == date_str for e in entries)
        except Exception:
            logger.warning("NSE holiday API unavailable, trusting exchange_calendars", app=APP_NAME)
            return None

    def _fetch_nse_holidays(self, year: int) -> list[dict[str, str]]:
        if self._nse_cache and year in self._nse_cache:
            return self._nse_cache[year]
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(_NSE_HOLIDAY_URL, headers=_NSE_HEADERS)
                resp.raise_for_status()
                data = resp.json()
            entries: list[dict[str, str]] = []
            for segment in ("FO", "CM"):
                for entry in data.get(segment, []):
                    entries.append(
                        {
                            "tradingDate": entry.get("tradingDate", ""),
                            "description": entry.get("description", "Market Holiday"),
                        }
                    )
            if self._nse_cache is None:
                self._nse_cache = {}
            self._nse_cache[year] = entries
            return entries
        except Exception as e:
            logger.debug("NSE API fetch failed", error=str(e))
            raise

    def _get_nse_holiday_name(self, target: dt.date) -> str | None:
        try:
            entries = self._fetch_nse_holidays(target.year)
            date_str = target.strftime("%d-%b-%Y")
            for entry in entries:
                if entry["tradingDate"] == date_str:
                    return entry["description"]
        except Exception:
            pass
        return None

    def _load_overrides(self) -> list[dict[str, Any]]:
        if not _HOLIDAYS_YAML.exists():
            return []
        try:
            with open(_HOLIDAYS_YAML) as f:
                data = yaml.safe_load(f) or {}
            return data.get("overrides", []) or []
        except Exception as e:
            logger.warning("Failed to load holidays.yaml", error=str(e))
            return []

    def _check_override(self, target: dt.date) -> bool | None:
        target_str = target.isoformat()
        for entry in self._overrides:
            if entry.get("date") == target_str:
                status = entry.get("status", "").upper()
                if status == "HOLIDAY":
                    return False
                if status == "OPEN":
                    return True
        return None

    def _get_override_name(self, target: dt.date) -> str | None:
        target_str = target.isoformat()
        for entry in self._overrides:
            if entry.get("date") == target_str:
                return entry.get("name")
        return None
