"""REPL command - Interactive query mode."""

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
@click.pass_obj
def repl(
    ctx: "AppContext",
    show_context: bool,
    k: int,
) -> None:
    """Start interactive REPL mode for querying the anime database.

    Launch an interactive session where you can ask multiple questions
    without restarting the command. Type 'exit', 'quit', or 'q' to leave.
    """
    console = Console()

    # Build RAG chain (lazy-loaded from context)
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Building RAG chain...", total=None)
        rag = ctx.rag_chain
        progress.update(task, description="[green]✓[/] RAG chain ready")

    console.print()

    # Start interactive mode
    _run_interactive(console, rag, show_context)


def _run_interactive(console: Console, rag: Any, show_context: bool) -> None:
    """Run interactive REPL."""
    console.print("[bold]Interactive RAG Mode[/]")
    console.print("Type your questions or [dim]'exit'/'quit'[/] to leave\n")

    try:
        while True:
            try:
                question = console.input("[bold cyan]>[/] ").strip()
            except EOFError:
                break

            if not question:
                continue

            if question.lower() in ("exit", "quit", "q"):
                break

            _run_single_question(console, rag, question, show_context)
            console.print()

    except KeyboardInterrupt:
        pass

    console.print("\n[dim]Goodbye![/]\n")


def _run_single_question(console: Console, rag: Any, question: str, show_context: bool) -> None:
    """Run a single question."""
    console.print(f"[bold cyan]Q:[/] {question}\n")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Thinking...", total=None)
        answer, docs = rag(question)
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

    for doc in docs:
        title = doc.metadata.get("title_main", "Unknown")
        anime_id = str(doc.metadata.get("anime_id", "N/A"))
        year = str(doc.metadata.get("begin_year", "N/A"))
        episodes = str(doc.metadata.get("episode_count_normal", "N/A"))

        table.add_row(title, anime_id, year, episodes)

    console.print(table)
    console.print()
