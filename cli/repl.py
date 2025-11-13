"""REPL command - Interactive query mode."""

import asyncio
from typing import TYPE_CHECKING, Any

import rich_click as click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

if TYPE_CHECKING:
    from services.app_context import AppContext


@click.command()
@click.option(
    "--show-context",
    "-c",
    is_flag=True,
    help="Display retrieved context documents",
)
@click.option(
    "--k",
    type=int,
    default=10,
    help="Number of documents to retrieve",
)
@click.option(
    "--output-format",
    type=click.Choice(["text", "json"], case_sensitive=False),
    default="text",
    help="Output format for responses (text or json)",
)
@click.pass_obj
def repl(
    ctx: "AppContext",
    show_context: bool,
    k: int,
    output_format: str,
) -> None:
    """Start interactive REPL mode for querying the anime database.

    Launch an interactive session where you can ask multiple questions
    without restarting the command. Type 'exit', 'quit', or 'q' to leave.
    """
    console = Console()

    # Set retrieval k from CLI parameter
    ctx.retrieval_k = k

    # Build RAG chain with specified output format
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Building RAG chain...", total=None)
        rag = ctx.get_rag_chain(output_format=output_format.lower())
        progress.update(task, description="[green]✓[/] RAG chain ready")

    console.print()

    # Start interactive mode
    asyncio.run(_run_interactive(console, rag, show_context, output_format.lower()))


async def _run_interactive(
    console: Console, rag: Any, show_context: bool, output_format: str
) -> None:
    """Run interactive REPL."""
    if output_format != "json":
        console.print("[bold]Interactive RAG Mode[/]")
        console.print("Type your questions or [dim]'exit'/'quit'[/] to leave\n")

    try:
        while True:
            try:
                if output_format == "json":
                    question = input().strip()
                else:
                    question = console.input("[bold cyan]>[/] ").strip()
            except EOFError:
                break

            if not question:
                continue

            if question.lower() in ("exit", "quit", "q"):
                break

            await _run_single_question(console, rag, question, show_context, output_format)
            if output_format != "json":
                console.print()

    except KeyboardInterrupt:
        pass

    if output_format != "json":
        console.print("\n[dim]Goodbye![/]\n")


async def _run_single_question(
    console: Console, rag: Any, question: str, show_context: bool, output_format: str
) -> None:
    """Run a single question."""
    if output_format == "json":
        # For JSON output, skip fancy formatting
        import json

        answer, docs = await rag(question)
        output = {"question": question, "answer": answer}
        if show_context:
            output["context"] = [
                {
                    "title": doc.metadata.get("title_main", "Unknown"),
                    "anime_id": doc.metadata.get("anime_id"),
                    "year": doc.metadata.get("begin_year"),
                    "episodes": doc.metadata.get("episode_count_normal"),
                }
                for doc in docs
            ]
        console.print(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        # Text output with rich formatting
        console.print(f"[bold cyan]Q:[/] {question}\n")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Thinking...", total=None)
            answer, docs = await rag(question)
            progress.update(task, description="[green]✓[/] Answer ready")

        console.print(f"\n[bold green]A:[/] {answer}\n")

        if show_context:
            _display_context(console, docs)


def _display_context(console: Console, docs: Any) -> None:
    """Display context documents in a table."""
    if not docs:
        return

    table = Table(title="Retrieved Context", show_header=True, header_style="bold magenta")
    table.add_column("Title", style="cyan", no_wrap=False)
    table.add_column("ID", style="dim", width=10)
    table.add_column("Year", style="yellow", width=10)
    table.add_column("Episodes", style="green", width=10)
    table.add_column("Similarity", style="blue", width=12)

    for doc in docs:
        title = doc.metadata.get("title_main", "Unknown")
        anime_id = str(doc.metadata.get("anime_id", "N/A"))
        year = str(doc.metadata.get("begin_year", "N/A"))
        episodes = str(doc.metadata.get("episode_count_normal", "N/A"))
        distance = doc.metadata.get("_distance_score")

        # Format similarity score with quality indicator
        if distance is not None:
            if distance == 0.0:
                similarity = "[green]MCP[/]"
            elif distance <= 0.3:
                similarity = f"[green]{distance:.3f}[/]"
            elif distance <= 0.6:
                similarity = f"[blue]{distance:.3f}[/]"
            elif distance <= 0.9:
                similarity = f"[yellow]{distance:.3f}[/]"
            else:
                similarity = f"[red]{distance:.3f}[/]"
        else:
            similarity = "[dim]N/A[/]"

        table.add_row(title, anime_id, year, episodes, similarity)

    console.print(table)
    console.print()
