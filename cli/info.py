"""Info command - Display configuration and system information."""

from typing import TYPE_CHECKING

import rich_click as click
from rich.table import Table

if TYPE_CHECKING:
    from rich.console import Console

    from services.config_service import ConfigService


@click.command()
@click.pass_context
def info(ctx: click.Context) -> None:
    """Display configuration and system information."""
    config: ConfigService = ctx.obj["config"]
    console: Console = ctx.obj["console"]

    console.print("\n[bold]ShokoBot Configuration[/]\n")

    # Create info table
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="yellow")

    # Add configuration rows
    cfg_dict = config.as_dict()

    table.add_row("[bold]ChromaDB[/]", "")
    table.add_row("  Collection", cfg_dict.get("chroma", {}).get("collection_name", "N/A"))
    table.add_row("  Directory", cfg_dict.get("chroma", {}).get("persist_directory", "N/A"))

    table.add_row("[bold]OpenAI[/]", "")
    table.add_row("  Model", cfg_dict.get("openai", {}).get("model", "N/A"))
    table.add_row("  Embedding Model", cfg_dict.get("openai", {}).get("embedding_model", "N/A"))
    table.add_row("  Reasoning Effort", cfg_dict.get("openai", {}).get("reasoning_effort", "N/A"))
    table.add_row("  Output Verbosity", cfg_dict.get("openai", {}).get("output_verbosity", "N/A"))

    table.add_row("[bold]Data[/]", "")
    table.add_row("  Shows JSON", cfg_dict.get("data", {}).get("shows_json", "N/A"))

    table.add_row("[bold]Ingestion[/]", "")
    table.add_row("  Batch Size", str(cfg_dict.get("ingest", {}).get("batch_size", "N/A")))

    console.print(table)
    console.print()
