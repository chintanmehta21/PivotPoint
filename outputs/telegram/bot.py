"""Telegram alert bot for signal dispatch."""
from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from outputs.telegram.formatter import TelegramFormatter
from quant.config.identity import APP_NAME
from quant.config.settings import settings

if TYPE_CHECKING:
    from quant.models.daily_report import DailyReport
    from quant.models.signals import SignalPayload

logger = structlog.get_logger()


class TelegramAlertBot:
    """Dispatches signals to Telegram."""

    def __init__(self) -> None:
        self._formatter = TelegramFormatter()
        self._token = settings.telegram.bot_token
        self._chat_id = settings.telegram.chat_id

    async def send_signal(self, signal: SignalPayload) -> None:
        """Send a signal to the configured Telegram chat."""
        if not self._token:
            logger.warning("Telegram bot token not configured", app=APP_NAME)
            return

        from quant.utils.types import SignalType

        if signal.signal_type == SignalType.ENTRY:
            _text = self._formatter.format_entry(signal)
        elif signal.signal_type == SignalType.EXIT:
            _text = self._formatter.format_exit(signal)
        else:
            _text = self._formatter.format_adjustment(signal)

        # TODO: Implement actual Telegram API call
        logger.info(
            "Telegram signal prepared",
            strategy=signal.strategy_id,
            chat_id=self._chat_id,
        )

    async def send_daily_report(self, report: DailyReport) -> None:
        """Send a daily report to the configured Telegram chat."""
        if not self._token:
            logger.warning("Telegram bot token not configured", app=APP_NAME)
            return

        from outputs.telegram.report_formatter import TelegramReportFormatter
        from quant.models.daily_report import ReportStatus

        fmt = TelegramReportFormatter()
        if report.report_status == ReportStatus.SUCCESS:
            text, keyboard = fmt.format_report(report)
        elif report.report_status == ReportStatus.MARKET_HOLIDAY:
            text, keyboard = fmt.format_holiday(report)
        else:
            text, keyboard = fmt.format_error(report)

        # TODO: Actual Telegram API call
        logger.info("Telegram daily report prepared", status=report.report_status.value, has_keyboard=keyboard is not None, chat_id=self._chat_id)
