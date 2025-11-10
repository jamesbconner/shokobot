"""Ingest command - Load anime data into vector database."""

import sys
from pathlib import Path
from typing import TYPE_CHECKING

import rich_click as click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

if TYPE_CHECKING:
    from services.app_context import AppContext


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
@click.pass_obj
def ingest(
    ctx: "AppContext",
    input_file: Path | None,
    batch_size: int | None,
    id_field: str,  # Click passes as str, we cast below
) -> None:
    """Ingest anime data into the vector database.

    Reads anime data from JSON and creates embeddings for semantic search.
    Progress is displayed with a progress bar.
    """
    from services.ingest_service import ingest_showdocs_streaming, iter_showdocs_from_json

    console = Console()

    # Get configuration
    input_path = input_file or ctx.config.get("data.shows_json")
    batch_size = batch_size or int(ctx.config.get("ingest.batch_size", 100))

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
            # id_field is validated by Click's Choice, safe to pass as-is
            docs_iter = iter_showdocs_from_json(ctx, path=input_path, id_field=id_field)  # type: ignore[arg-type]

            progress.update(task, description="Ingesting documents...")

            # Ingest with progress updates
            total = ingest_showdocs_streaming(docs_iter, ctx, batch_size=batch_size)

            progress.update(task, description=f"[green]✓[/] Ingested {total} documents")

        console.print(f"\n[green]✓ Successfully ingested {total} documents![/]\n")

        # Reset cached services after ingestion
        ctx.reset_all()

    except Exception as e:
        console.print(f"\n[red]✗ Ingestion failed:[/] {e}\n")
        sys.exit(1)
