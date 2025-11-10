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
@click.option(
    "--dry-run",
    is_flag=True,
    help="Validate mappings and show statistics without ingesting",
)
@click.pass_obj
def ingest(
    ctx: "AppContext",
    input_file: Path | None,
    batch_size: int | None,
    id_field: str,  # Click passes as str, we cast below
    dry_run: bool,
) -> None:
    """Ingest anime data into the vector database.

    Reads anime data from JSON and creates embeddings for semantic search.
    Progress is displayed with a progress bar.

    Use --dry-run to validate data without actually ingesting.
    """
    from services.ingest_service import (
        ingest_showdocs_streaming,
        iter_showdocs_from_json,
        validate_showdocs_dry_run,
    )

    console = Console()

    # Get configuration
    input_path = input_file or ctx.config.get("data.shows_json")
    batch_size = batch_size or int(ctx.config.get("ingest.batch_size", 100))

    mode = "[yellow]DRY RUN[/]" if dry_run else "Ingesting anime data"
    console.print(f"\n[bold]{mode}[/]")
    console.print(f"  Input: [cyan]{input_path}[/]")
    console.print(f"  Batch size: [cyan]{batch_size}[/]")
    console.print(f"  ID field: [cyan]{id_field}[/]")
    if dry_run:
        console.print(f"  Mode: [yellow]Validation only (no ingestion)[/]")
    console.print()

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

            if dry_run:
                # Dry-run mode: validate only
                progress.update(task, description="Validating documents...")
                stats = validate_showdocs_dry_run(docs_iter, batch_size=batch_size)
                progress.update(
                    task, description=f"[green]✓[/] Validated {stats['total']} documents"
                )

                # Display statistics
                console.print(f"\n[bold green]✓ Validation Complete[/]\n")
                console.print(f"[bold]Statistics:[/]")
                console.print(f"  Total documents: [cyan]{stats['total']}[/]")
                console.print(f"  Batches: [cyan]{stats['batch_count']}[/]")

                if stats["year_range"]:
                    console.print(
                        f"  Year range: [cyan]{stats['year_range'][0]} - {stats['year_range'][1]}[/]"
                    )

                if stats["episode_stats"]:
                    eps = stats["episode_stats"]
                    console.print(
                        f"  Episodes: [cyan]min={eps['min']}, max={eps['max']}, avg={eps['avg']:.1f}[/]"
                    )

                if stats["sample_titles"]:
                    console.print(f"\n[bold]Sample titles:[/]")
                    for title in stats["sample_titles"]:
                        console.print(f"  • {title}")

                if stats["errors"]:
                    console.print(f"\n[bold yellow]Validation errors ({len(stats['errors'])}):[/]")
                    for error in stats["errors"][:10]:  # Show first 10 errors
                        console.print(f"  [yellow]⚠[/] {error}")
                    if len(stats["errors"]) > 10:
                        console.print(
                            f"  [dim]... and {len(stats['errors']) - 10} more errors[/]"
                        )

                console.print()
            else:
                # Normal mode: ingest
                progress.update(task, description="Ingesting documents...")
                total = ingest_showdocs_streaming(docs_iter, ctx, batch_size=batch_size)
                progress.update(task, description=f"[green]✓[/] Ingested {total} documents")

                console.print(f"\n[green]✓ Successfully ingested {total} documents![/]\n")

                # Reset cached services after ingestion
                ctx.reset_all()

    except Exception as e:
        console.print(f"\n[red]✗ {'Validation' if dry_run else 'Ingestion'} failed:[/] {e}\n")
        sys.exit(1)
