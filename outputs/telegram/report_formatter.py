"""Telegram daily report formatter using MarkdownV2."""

from __future__ import annotations

from typing import TYPE_CHECKING

from outputs.base_report_formatter import BaseReportFormatter
from outputs.telegram.formatter import _escape_md
from quant.config.identity import APP_NAME
from quant.models.daily_report import ERROR_LABELS, PortfolioTier

if TYPE_CHECKING:
    from quant.models.daily_report import DailyReport

# Callback data patterns for inline keyboard buttons
CALLBACK_PORTFOLIO = "report:portfolio_drilldown"
CALLBACK_ANALYSIS = "report:analysis_drilldown"


def _vix_label(vix: float) -> str:
    if vix < 15:
        return "Low"
    if vix < 20:
        return "Moderate"
    if vix < 25:
        return "High"
    return "Extreme"


def _change_arrow(pct: float) -> str:
    return "▲" if pct >= 0 else "▼"


class TelegramReportFormatter(BaseReportFormatter):
    """Formats DailyReport objects as Telegram MarkdownV2 messages."""

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def format_report(self, report: DailyReport) -> tuple[str, list | None]:
        """Return (MarkdownV2 text, inline keyboard) for a successful report."""
        lines: list[str] = []
        m = report.market_macros

        # Header
        report_type_label = _escape_md(report.report_type.value.capitalize())
        date_str = _escape_md(report.date.strftime("%d %b %Y"))
        lines.append(f"*\\[{_escape_md(APP_NAME)}\\] {report_type_label} Report — {date_str}*")
        lines.append("")

        # Market snapshot
        if m is not None:
            nifty_arrow = _change_arrow(m.nifty_change_pct)
            bn_arrow = _change_arrow(m.banknifty_change_pct)
            vix_arrow = _change_arrow(m.vix_change)
            fii_arrow = _change_arrow(float(m.fii_net_cash))
            dii_arrow = _change_arrow(float(m.dii_net_cash))

            lines.append("*📊 Market Snapshot*")
            lines.append(
                f"├ NIFTY: *{_escape_md(f'{m.nifty_price:,.2f}')}* "
                f"{_escape_md(f'{nifty_arrow} {abs(m.nifty_change_pct):.2f}%')}"
            )
            lines.append(
                f"├ BANKNIFTY: *{_escape_md(f'{m.banknifty_price:,.2f}')}* "
                f"{_escape_md(f'{bn_arrow} {abs(m.banknifty_change_pct):.2f}%')}"
            )
            lines.append(
                f"└ India VIX: *{_escape_md(f'{m.india_vix:.2f}')}* "
                f"{_escape_md(f'({_vix_label(m.india_vix)}) {vix_arrow} {abs(m.vix_change):.2f}')}"
            )
            lines.append("")

            # Options data
            lines.append("*📈 Options Data*")
            lines.append(f"├ PCR \\(OI\\): *{_escape_md(f'{m.nifty_pcr_oi:.2f}')}*")
            lines.append(f"├ NIFTY Max Pain: *{_escape_md(f'{m.nifty_max_pain:,.0f}')}*")
            lines.append(f"├ BANKNIFTY Max Pain: *{_escape_md(f'{m.banknifty_max_pain:,.0f}')}*")
            lines.append(f"├ NIFTY IV Pctile: *{_escape_md(f'{m.nifty_iv_percentile:.1f}%')}*")
            lines.append(f"└ BANKNIFTY IV Pctile: *{_escape_md(f'{m.banknifty_iv_percentile:.1f}%')}*")
            lines.append("")

            # Institutional flow
            lines.append("*🏦 Institutional Flow*")
            lines.append(f"├ FII: *{_escape_md(f'{fii_arrow} ₹{abs(float(m.fii_net_cash)):,.0f} Cr')}*")
            lines.append(f"└ DII: *{_escape_md(f'{dii_arrow} ₹{abs(float(m.dii_net_cash)):,.0f} Cr')}*")
            lines.append("")

        # Top signals
        if report.top_3_bullish:
            lines.append("*🟢 Top Bullish Setups*")
            for i, r in enumerate(report.top_3_bullish):
                prefix = "└" if i == len(report.top_3_bullish) - 1 else "├"
                score = f"  _{_escape_md(f'{r.confidence_score:.0f}/100')}_" if r.confidence_score else ""
                lines.append(f"{prefix} {_escape_md(r.strategy_name)} \\({_escape_md(r.strategy_id)}\\){score}")
            lines.append("")

        if report.top_3_bearish:
            lines.append("*🔴 Top Bearish Setups*")
            for i, r in enumerate(report.top_3_bearish):
                prefix = "└" if i == len(report.top_3_bearish) - 1 else "├"
                score = f"  _{_escape_md(f'{r.confidence_score:.0f}/100')}_" if r.confidence_score else ""
                lines.append(f"{prefix} {_escape_md(r.strategy_name)} \\({_escape_md(r.strategy_id)}\\){score}")
            lines.append("")

        # Portfolio summary
        if report.portfolios:
            lines.append("*💼 Virtual Portfolio*")
            for i, p in enumerate(report.portfolios):
                prefix = "└" if i == len(report.portfolios) - 1 else "├"
                pnl_arrow = _change_arrow(float(p.total_pnl))
                lines.append(
                    f"{prefix} {_escape_md(p.tier.value.capitalize())} "
                    f"\\(≥{p.threshold}\\): "
                    f"*{_escape_md(f'{pnl_arrow} ₹{abs(float(p.total_pnl)):,.0f}')}* "
                    f"| WR: {_escape_md(f'{p.win_rate:.0%}')}"
                )
            lines.append("")

        lines.append(f"`{_escape_md(APP_NAME)}`")

        keyboard = [
            [
                {"text": "📈 Virtual Portfolio", "callback_data": CALLBACK_PORTFOLIO},
                {"text": "🔍 Detailed Analysis", "callback_data": CALLBACK_ANALYSIS},
            ]
        ]
        return "\n".join(lines), keyboard

    def format_holiday(self, report: DailyReport) -> tuple[str, None]:
        """Return (MarkdownV2 text, None) for a market holiday."""
        holiday = _escape_md(report.holiday_name or "Market Holiday")
        date_str = _escape_md(report.date.strftime("%d %b %Y"))
        next_day = ""
        if report.next_trading_day:
            next_day = f"\n\n_Next trading day: {_escape_md(report.next_trading_day.strftime('%d %b %Y'))}_"

        text = (
            f"*\\[{_escape_md(APP_NAME)}\\] 🏖 Market Holiday — {date_str}*\n\n"
            f"Markets are closed today for *{holiday}*\\."
            f"{next_day}"
        )
        return text, None

    def format_error(self, report: DailyReport) -> tuple[str, None]:
        """Return (MarkdownV2 text, None) for an error report."""
        date_str = _escape_md(report.date.strftime("%d %b %Y"))
        category_label = "Unexpected Error"
        if report.error_category is not None:
            category_label = ERROR_LABELS.get(report.error_category, "Unexpected Error")
        detail = ""
        if report.error_detail:
            detail = f"\n\n_Details: {_escape_md(report.error_detail)}_"

        text = (
            f"*\\[{_escape_md(APP_NAME)}\\] ⚠️ Report Error — {date_str}*\n\n"
            f"*Error:* {_escape_md(category_label)}"
            f"{detail}"
        )
        return text, None

    def format_portfolio_drilldown(self, report: DailyReport) -> str:
        """Return MarkdownV2 string for the virtual portfolio drill-down."""
        date_str = _escape_md(report.date.strftime("%d %b %Y"))
        lines: list[str] = [
            f"*\\[{_escape_md(APP_NAME)}\\] 📈 Virtual Portfolio — {date_str}*",
            "",
        ]

        if not report.portfolios:
            lines.append("_No portfolio data available\\._")
            return "\n".join(lines)

        tier_emojis = {
            PortfolioTier.CONSERVATIVE: "🛡",
            PortfolioTier.MODERATE: "⚖️",
            PortfolioTier.AGGRESSIVE: "⚡",
        }

        for p in report.portfolios:
            emoji = tier_emojis.get(p.tier, "•")
            lines.append(f"*{emoji} {_escape_md(p.tier.value.capitalize())} Tier* \\(confidence ≥{p.threshold}\\)")
            lines.append(f"├ Active Positions: *{p.active_positions}* / {p.total_trades} total")
            lines.append(f"├ Realized P&L: *{_escape_md(f'₹{float(p.realized_pnl):+,.0f}')}*")
            lines.append(f"├ Unrealized P&L: *{_escape_md(f'₹{float(p.unrealized_pnl):+,.0f}')}*")
            lines.append(f"├ Total P&L: *{_escape_md(f'₹{float(p.total_pnl):+,.0f}')}*")
            lines.append(f"├ Win Rate: *{_escape_md(f'{p.win_rate:.0%}')}*")
            lines.append(f"├ Best Strategy: {_escape_md(p.best_strategy)}")
            lines.append(f"└ Worst Strategy: {_escape_md(p.worst_strategy)}")
            lines.append("")

        lines.append(f"`{_escape_md(APP_NAME)}`")
        return "\n".join(lines)

    def format_analysis_drilldown(self, report: DailyReport) -> str:
        """Return MarkdownV2 string for the detailed analysis drill-down."""
        date_str = _escape_md(report.date.strftime("%d %b %Y"))
        lines: list[str] = [
            f"*\\[{_escape_md(APP_NAME)}\\] 🔍 Detailed Analysis — {date_str}*",
            "",
        ]
        m = report.market_macros

        if m is None:
            lines.append("_No market data available\\._")
            return "\n".join(lines)

        # Volatility section
        lines.append("*📉 Volatility*")
        lines.append(f"├ India VIX: *{_escape_md(f'{m.india_vix:.2f}')}* \\({_escape_md(_vix_label(m.india_vix))}\\)")
        if m.nifty_atm_iv is not None:
            lines.append(f"├ NIFTY ATM IV: *{_escape_md(f'{m.nifty_atm_iv:.2f}%')}*")
        if m.banknifty_atm_iv is not None:
            lines.append(f"├ BANKNIFTY ATM IV: *{_escape_md(f'{m.banknifty_atm_iv:.2f}%')}*")
        if m.realized_vol_20d is not None:
            lines.append(f"├ Realized Vol 20D: *{_escape_md(f'{m.realized_vol_20d:.2f}%')}*")
        if m.iv_rv_spread is not None:
            lines.append(f"└ IV\\-RV Spread: *{_escape_md(f'{m.iv_rv_spread:.2f}')}*")
        else:
            lines[-1] = lines[-1].replace("├", "└", 1) if lines[-1].startswith("├") else lines[-1]
        lines.append("")

        # Gamma exposure
        if any([m.net_gamma_exposure, m.call_wall, m.put_wall, m.gamma_flip_level]):
            lines.append("*⚡ Gamma Exposure*")
            if m.call_wall is not None:
                lines.append(f"├ Call Wall: *{_escape_md(f'{m.call_wall:,.0f}')}*")
            if m.put_wall is not None:
                lines.append(f"├ Put Wall: *{_escape_md(f'{m.put_wall:,.0f}')}*")
            if m.gamma_flip_level is not None:
                lines.append(f"├ Gamma Flip: *{_escape_md(f'{m.gamma_flip_level:,.0f}')}*")
            if m.net_gamma_exposure is not None:
                lines.append(f"└ Net GEX: *{_escape_md(f'{float(m.net_gamma_exposure):+,.0f}')}*")
            lines.append("")

        # Technical levels
        if m.nifty_support_levels or m.nifty_resistance_levels:
            lines.append("*📐 Technical Levels*")
            if m.nifty_support_levels:
                supports = ", ".join(_escape_md(f"{s:,.0f}") for s in m.nifty_support_levels)
                lines.append(f"├ Support: {supports}")
            if m.nifty_resistance_levels:
                resistances = ", ".join(_escape_md(f"{r:,.0f}") for r in m.nifty_resistance_levels)
                lines.append(f"└ Resistance: {resistances}")
            lines.append("")

        # Breadth
        if any([m.advance_decline_ratio, m.pct_above_20dma, m.pct_above_200dma]):
            lines.append("*🌐 Market Breadth*")
            if m.advance_decline_ratio is not None:
                lines.append(f"├ A/D Ratio: *{_escape_md(f'{m.advance_decline_ratio:.2f}')}*")
            if m.pct_above_20dma is not None:
                lines.append(f"├ % Above 20DMA: *{_escape_md(f'{m.pct_above_20dma:.1f}%')}*")
            if m.pct_above_200dma is not None:
                lines.append(f"└ % Above 200DMA: *{_escape_md(f'{m.pct_above_200dma:.1f}%')}*")
            lines.append("")

        lines.append(f"`{_escape_md(APP_NAME)}`")
        return "\n".join(lines)
