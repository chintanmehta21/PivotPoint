"""Discord daily report formatting using Embeds."""
from __future__ import annotations

from typing import TYPE_CHECKING

import discord

from outputs.base_report_formatter import BaseReportFormatter
from quant.config.identity import APP_NAME, APP_VERSION
from quant.models.daily_report import ERROR_LABELS

if TYPE_CHECKING:
    from quant.models.daily_report import DailyReport

# Colors
COLOR_REPORT = discord.Color.gold()
COLOR_HOLIDAY = discord.Color.green()
COLOR_ERROR = discord.Color.red()
COLOR_DRILLDOWN = discord.Color.blurple()


class DiscordReportFormatter(BaseReportFormatter):
    """Formats daily reports as Discord Embed objects."""

    def format_report(self, report: DailyReport) -> discord.Embed:
        """Format a successful daily report as a gold embed."""
        embed = discord.Embed(
            title=f"[{APP_NAME}] {report.report_type.value} Report — {report.date}",
            color=COLOR_REPORT,
        )

        if report.market_macros:
            m = report.market_macros
            nifty_sign = "+" if m.nifty_change_pct >= 0 else ""
            bnf_sign = "+" if m.banknifty_change_pct >= 0 else ""
            vix_sign = "+" if m.vix_change >= 0 else ""

            embed.add_field(
                name="NIFTY",
                value=f"{m.nifty_price:,.2f} ({nifty_sign}{m.nifty_change_pct:.2f}%)",
                inline=True,
            )
            embed.add_field(
                name="BANKNIFTY",
                value=f"{m.banknifty_price:,.2f} ({bnf_sign}{m.banknifty_change_pct:.2f}%)",
                inline=True,
            )
            embed.add_field(
                name="India VIX",
                value=f"{m.india_vix:.2f} ({vix_sign}{m.vix_change:.2f})",
                inline=True,
            )
            embed.add_field(name="PCR (OI)", value=f"{m.nifty_pcr_oi:.2f}", inline=True)
            embed.add_field(name="NIFTY Max Pain", value=f"{m.nifty_max_pain:,.0f}", inline=True)
            embed.add_field(name="BANKNIFTY Max Pain", value=f"{m.banknifty_max_pain:,.0f}", inline=True)
            embed.add_field(
                name="IV Percentile",
                value=f"NIFTY {m.nifty_iv_percentile:.1f}% | BNF {m.banknifty_iv_percentile:.1f}%",
                inline=True,
            )
            embed.add_field(
                name="FII / DII (Cash)",
                value=f"FII Rs {m.fii_net_cash:+,.0f}Cr | DII Rs {m.dii_net_cash:+,.0f}Cr",
                inline=True,
            )

        if report.top_3_bullish:
            lines = [
                f"{i + 1}. {r.strategy_name} ({r.strategy_id})"
                + (f" — {r.confidence_score:.0f}/100" if r.confidence_score is not None else "")
                for i, r in enumerate(report.top_3_bullish)
            ]
            embed.add_field(name="Top Bullish Setups", value="\n".join(lines), inline=False)

        if report.top_3_bearish:
            lines = [
                f"{i + 1}. {r.strategy_name} ({r.strategy_id})"
                + (f" — {r.confidence_score:.0f}/100" if r.confidence_score is not None else "")
                for i, r in enumerate(report.top_3_bearish)
            ]
            embed.add_field(name="Top Bearish Setups", value="\n".join(lines), inline=False)

        embed.set_footer(text=f"{APP_NAME} v{APP_VERSION}")
        embed.timestamp = report.timestamp
        return embed

    def format_holiday(self, report: DailyReport) -> discord.Embed:
        """Format a market holiday message as a green embed."""
        holiday_name = report.holiday_name or "Market Holiday"
        embed = discord.Embed(
            title=f"[{APP_NAME}] Market Holiday — {report.date}",
            description=f"**{holiday_name}**\nMarkets are closed today.",
            color=COLOR_HOLIDAY,
        )
        if report.next_trading_day:
            embed.add_field(name="Next Trading Day", value=str(report.next_trading_day), inline=False)
        embed.set_footer(text=f"{APP_NAME} v{APP_VERSION}")
        embed.timestamp = report.timestamp
        return embed

    def format_error(self, report: DailyReport) -> discord.Embed:
        """Format an error report as a red embed."""
        category = report.error_category
        label = ERROR_LABELS.get(category, "Unexpected Error") if category else "Unexpected Error"
        embed = discord.Embed(
            title=f"[{APP_NAME}] Report Error — {report.date}",
            description=f"**Error Category:** {label}",
            color=COLOR_ERROR,
        )
        if report.error_detail:
            embed.add_field(name="Detail", value=report.error_detail, inline=False)
        embed.set_footer(text=f"{APP_NAME} v{APP_VERSION}")
        embed.timestamp = report.timestamp
        return embed

    def format_portfolio_drilldown(self, report: DailyReport) -> discord.Embed:
        """Format the virtual portfolio drill-down as a blurple embed."""
        embed = discord.Embed(
            title=f"[{APP_NAME}] Virtual Portfolio Drill-Down — {report.date}",
            color=COLOR_DRILLDOWN,
        )
        for portfolio in report.portfolios:
            value_lines = [
                f"Active Positions: {portfolio.active_positions}",
                f"Total Trades: {portfolio.total_trades}",
                f"Win Rate: {portfolio.win_rate * 100:.1f}%",
                f"Realized P&L: Rs {portfolio.realized_pnl:+,.0f}",
                f"Unrealized P&L: Rs {portfolio.unrealized_pnl:+,.0f}",
                f"Total P&L: Rs {portfolio.total_pnl:+,.0f}",
                f"Best: {portfolio.best_strategy} | Worst: {portfolio.worst_strategy}",
            ]
            embed.add_field(
                name=f"{portfolio.tier.value} (≥{portfolio.threshold})",
                value="\n".join(value_lines),
                inline=False,
            )
        embed.set_footer(text=f"{APP_NAME} v{APP_VERSION}")
        embed.timestamp = report.timestamp
        return embed

    def format_analysis_drilldown(self, report: DailyReport) -> discord.Embed:
        """Format the detailed analysis drill-down as a blurple embed."""
        embed = discord.Embed(
            title=f"[{APP_NAME}] Market Analysis Drill-Down — {report.date}",
            color=COLOR_DRILLDOWN,
        )
        if report.market_macros:
            m = report.market_macros

            # Dealer / gamma positioning
            positioning_lines: list[str] = []
            if m.net_gamma_exposure is not None:
                positioning_lines.append(f"Net Gamma Exposure: {m.net_gamma_exposure:+,.0f}")
            if m.call_wall is not None:
                positioning_lines.append(f"Call Wall: {m.call_wall:,.0f}")
            if m.put_wall is not None:
                positioning_lines.append(f"Put Wall: {m.put_wall:,.0f}")
            if m.gamma_flip_level is not None:
                positioning_lines.append(f"Gamma Flip: {m.gamma_flip_level:,.0f}")
            if m.fii_net_derivatives is not None:
                positioning_lines.append(f"FII Net Derivatives: Rs {m.fii_net_derivatives:+,.0f}Cr")
            if positioning_lines:
                embed.add_field(name="Dealer Positioning", value="\n".join(positioning_lines), inline=False)

            # Support / resistance
            if m.nifty_support_levels:
                supports = " | ".join(f"{s:,.0f}" for s in m.nifty_support_levels)
                embed.add_field(name="NIFTY Support", value=supports, inline=True)
            if m.nifty_resistance_levels:
                resistances = " | ".join(f"{r:,.0f}" for r in m.nifty_resistance_levels)
                embed.add_field(name="NIFTY Resistance", value=resistances, inline=True)

            # Additional technical signals
            technical_lines: list[str] = []
            if m.supertrend_signal is not None:
                technical_lines.append(f"Supertrend: {m.supertrend_signal}")
            if m.nifty_rsi is not None:
                technical_lines.append(f"RSI: {m.nifty_rsi:.1f}")
            if m.nifty_macd_state is not None:
                technical_lines.append(f"MACD: {m.nifty_macd_state}")
            if technical_lines:
                embed.add_field(name="Technical Signals", value="\n".join(technical_lines), inline=False)

        embed.set_footer(text=f"{APP_NAME} v{APP_VERSION}")
        embed.timestamp = report.timestamp
        return embed
