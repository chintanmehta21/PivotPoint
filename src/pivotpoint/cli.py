"""Command-line interface for the trading system."""
from __future__ import annotations

import click
import structlog

from pivotpoint.config.identity import APP_NAME, APP_VERSION
from pivotpoint.config.settings import settings
from pivotpoint.utils.logger import configure_logging


@click.group()
@click.version_option(version=APP_VERSION, prog_name=APP_NAME)
def cli() -> None:
    """Options trading signal generation system."""
    configure_logging(settings.log_level, settings.environment)


@cli.command()
def info() -> None:
    """Show system info and registered strategies."""
    from pivotpoint.strategies.registry import StrategyRegistry

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
    from pivotpoint.strategies.registry import StrategyRegistry

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


if __name__ == "__main__":
    cli()
