import typer
import os
from rich.console import Console
from rich.align import Align
from rich.panel import Panel
from cockroachdb_mcp_server.schema_init import run_schema_init
from cockroachdb_mcp_server.config import resolve_crdb_url
from cockroachdb_mcp_server.server import start_server
from cockroachdb_mcp_server.logging_config import setup_logging
from cockroachdb_mcp_server import __version__

cli = typer.Typer(help="Model Context Protocol Server (Powered by CockroachDB)")


@cli.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(
        False, "--version", "-v", help="Show version and exit"
    ),
    log_level: str = typer.Option(
        "INFO", "--log-level", help="Set logging level (DEBUG, INFO, WARN, etc.)"
    ),
):
    setup_logging(log_level)
    show_banner()

    if version:
        typer.echo(f"cockroachdb-mcp-server version {__version__}")
        raise typer.Exit()
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit()


@cli.command()
def serve(
    host: str = typer.Option("0.0.0.0", help="Host to bind to"),
    port: int = typer.Option(8081, help="Port to listen on"),
    reload: bool = typer.Option(False, help="Enable auto-reload"),
    init_schema: bool = typer.Option(
        False, "--init-schema", help="Initialize DB schema"
    ),
    log_level: str = typer.Option(
        "INFO", "--log-level", help="Logging level (DEBUG, INFO, WARN, etc.)"
    ),
    demo_mode: bool = typer.Option(
        False, "--demo-mode", help="Enable demo/debug endpoints"
    ),
):
    """Start the MCP server."""

    setup_logging(log_level)

    if init_schema or os.getenv("MCP_AUTO_INIT_SCHEMA") == "true":
        typer.echo("Initializing schema...")
        run_schema_init(resolve_crdb_url())

    start_server(host, port, reload, demo_mode=demo_mode)


def show_banner():
    console = Console()
    title = "[bold cyan]cockroachdb-mcp-server[/bold cyan]"
    subtitle = "[white]Model Context Protocol Server for CockroachDB[/white]"
    version = f"[dim]v{__version__}[/dim]"

    banner = f"{title}\n{subtitle}\n{version}"
    panel = Panel(Align.center(banner), border_style="cyan", padding=(1, 4))
    console.print(panel)
