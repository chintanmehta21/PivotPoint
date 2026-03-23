"""Command-line interface for the trading system."""
from __future__ import annotations

import click

from quant.config.identity import APP_NAME, APP_VERSION
from quant.config.settings import settings
from quant.utils.logger import configure_logging


@click.group()
@click.version_option(version=APP_VERSION, prog_name=APP_NAME)
def cli() -> None:
    """Options trading signal generation system."""
    configure_logging(settings.log_level, settings.environment)


@cli.command()
def info() -> None:
    """Show system info and registered strategies."""
    from quant.strategies.registry import StrategyRegistry

    registry = StrategyRegistry()
    click.echo(f"{APP_NAME} v{APP_VERSION}")
    click.echo(f"Environment: {settings.environment}")
    click.echo(f"Log level: {settings.log_level}")
    click.echo(f"Strategies registered: {registry.count}")
    click.echo()

    for direction_label in ["BULLISH", "BEARISH"]:
        strategies = [s for s in registry.all().values() if s.direction.value == direction_label]
        if strategies:
            click.echo(f"  {direction_label}:")
            for s in sorted(strategies, key=lambda x: x.strategy_id):
                click.echo(f"    [{s.strategy_id}] {s.name} ({s.timeframe.value})")


@cli.command()
def scan() -> None:
    """Run all strategies against current market data."""
    from quant.strategies.registry import StrategyRegistry

    registry = StrategyRegistry()
    click.echo(f"[{APP_NAME}] Scanning {registry.count} strategies...")
    click.echo("  NOTE: Requires MarketDataProvider implementation (Fyers API)")
    click.echo("  No live market data available yet — strategies will be skipped.")


@cli.command()
def serve() -> None:
    """Start alert bots (Discord + Telegram)."""
    click.echo(f"[{APP_NAME}] Starting alert services...")
    click.echo("  NOTE: Requires DISCORD__BOT_TOKEN and TELEGRAM__BOT_TOKEN in .env")
    click.echo("  Bot implementations pending (Phase 4).")


@cli.command()
@click.option("--type", "report_type", type=click.Choice(["morning", "evening"]), required=True,
              help="Report type: morning (pre-market) or evening (post-market)")
@click.option("--dry-run", is_flag=True, help="Generate report but don't dispatch to channels")
def report(report_type: str, dry_run: bool) -> None:
    """Generate and send the daily report."""
    import asyncio

    from quant.models.daily_report import ReportStatus, ReportType
    from quant.report.engine import DailyReportEngine

    rt = ReportType.MORNING if report_type == "morning" else ReportType.EVENING
    click.echo(f"[{APP_NAME}] Generating {report_type} report...")

    engine = DailyReportEngine()
    result = asyncio.run(engine.generate(rt, dry_run=dry_run))

    if result.report_status == ReportStatus.SUCCESS:
        click.echo("  Status: SUCCESS")
        click.echo(f"  Date: {result.date}")
        if result.market_macros:
            click.echo(f"  NIFTY: {result.market_macros.nifty_price}")
    elif result.report_status == ReportStatus.MARKET_HOLIDAY:
        click.echo(f"  Status: MARKET HOLIDAY — {result.holiday_name}")
        click.echo(f"  Next trading day: {result.next_trading_day}")
    else:
        click.echo(f"  Status: ERROR — {result.error_category}")
        click.echo(f"  Detail: {result.error_detail}")
        raise SystemExit(1)


if __name__ == "__main__":
    cli()
