"""Discord alert bot for signal dispatch."""
from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from outputs.discord.formatter import DiscordFormatter
from quant.config.identity import APP_NAME
from quant.config.settings import settings

if TYPE_CHECKING:
    from quant.models.daily_report import DailyReport
    from quant.models.signals import SignalPayload

logger = structlog.get_logger()


class DiscordAlertBot:
    """Dispatches signals to Discord via bot or webhook."""

    def __init__(self) -> None:
        self._formatter = DiscordFormatter()
        self._token = settings.discord.bot_token
        self._channel_id = settings.discord.channel_id

    async def send_signal(self, signal: SignalPayload) -> None:
        """Send a signal to the configured Discord channel."""
        if not self._token:
            logger.warning("Discord bot token not configured", app=APP_NAME)
            return

        from quant.utils.types import SignalType

        if signal.signal_type == SignalType.ENTRY:
            embed = self._formatter.format_entry(signal)
        elif signal.signal_type == SignalType.EXIT:
            embed = self._formatter.format_exit(signal)
        else:
            embed = self._formatter.format_adjustment(signal)

        # TODO: Implement actual Discord API call
        logger.info(
            "Discord signal prepared",
            strategy=signal.strategy_id,
            channel=self._channel_id,
            embed_title=embed.title,
        )

    async def send_daily_report(self, report: DailyReport) -> None:
        """Send a daily report to the configured Discord channel."""
        if not self._token:
            logger.warning("Discord bot token not configured", app=APP_NAME)
            return

        from outputs.discord.report_formatter import DiscordReportFormatter
        from quant.models.daily_report import ReportStatus

        fmt = DiscordReportFormatter()
        if report.report_status == ReportStatus.SUCCESS:
            embed = fmt.format_report(report)
            portfolio_embed = fmt.format_portfolio_drilldown(report)
            analysis_embed = fmt.format_analysis_drilldown(report)
            embeds = [embed, portfolio_embed, analysis_embed]
        elif report.report_status == ReportStatus.MARKET_HOLIDAY:
            embeds = [fmt.format_holiday(report)]
        else:
            embeds = [fmt.format_error(report)]

        # TODO: Actual Discord API call
        logger.info("Discord daily report prepared", status=report.report_status.value, embeds_count=len(embeds), channel=self._channel_id)
