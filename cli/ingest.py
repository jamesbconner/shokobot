"""Ingest command - Load anime data into vector database."""

import sys
from pathlib import Path
from typing import TYPE_CHECKING

import rich_click as click
from rich.progress import Progress, SpinnerColumn, TextColumn

if TYPE_CHECKING:
    from rich.console import Console

    from services.config_service import ConfigService


@click.command()
@click.option(
    "--input",
    "-i",
    "input_file",
    type=click.Path(exists=True, path_type=Path),
    help="Path to JSON file with anime data (overrides config)",
)
@click.option(
    "--batch-size",
    "-b",
    type=int,
    help="Number of documents per batch (overrides config)",
)
@click.option(
    "--id-field",
    type=click.Choice(["AnimeID", "AniDB_AnimeID"]),
    default="AnimeID",
    help="Field to use as primary ID",
)
@click.pass_context
def ingest(
    ctx: click.Context,
    input_file: Path | None,
    batch_size: int | None,
    id_field: str,
) -> None:
    """Ingest anime data into the vector database.

    Reads anime data from JSON and creates embeddings for semantic search.
    Progress is displayed with a progress bar.
    """
    from services.ingest_service import ingest_showdocs_streaming, iter_showdocs_from_json

    config: ConfigService = ctx.obj["config"]
    console: Console = ctx.obj["console"]

    # Get configuration
    input_path = input_file or config.get("data.shows_json")
    batch_size = batch_size or int(config.get("ingest.batch_size", 100))

    console.print("\n[bold]Ingesting anime data[/]")
    console.print(f"  Input: [cyan]{input_path}[/]")
    console.print(f"  Batch size: [cyan]{batch_size}[/]")
    console.print(f"  ID field: [cyan]{id_field}[/]\n")

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Loading documents...", total=None)

            # Create document iterator
            docs_iter = iter_showdocs_from_json(config, path=input_path, id_field=id_field)

            progress.update(task, description="Ingesting documents...")

            # Ingest with progress updates
            total = ingest_showdocs_streaming(docs_iter, config, batch_size=batch_size)

            progress.update(task, description=f"[green]✓[/] Ingested {total} documents")

        console.print(f"\n[green]✓ Successfully ingested {total} documents![/]\n")

    except Exception as e:
        console.print(f"\n[red]✗ Ingestion failed:[/] {e}\n")
        sys.exit(1)
