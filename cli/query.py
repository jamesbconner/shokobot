"""Query command - Query the anime database with natural language."""

import sys
from pathlib import Path

import rich_click as click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table


@click.command()
@click.option(
    "--question",
    "-q",
    help="Single question to ask",
)
@click.option(
    "--file",
    "-f",
    "input_file",
    type=click.Path(exists=True, path_type=Path),
    help="File with questions (one per line)",
)
@click.option(
    "--stdin",
    is_flag=True,
    help="Read questions from stdin",
)
@click.option(
    "--interactive",
    "-i",
    is_flag=True,
    help="Start interactive REPL mode",
)
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
@click.pass_context
def query(
    ctx: click.Context,
    question: str | None,
    input_file: Path | None,
    stdin: bool,
    interactive: bool,
    show_context: bool,
    k: int,
) -> None:
    """Query the anime database with natural language.

    Ask questions about anime and get AI-powered recommendations based on
    semantic search through your anime collection.
    """
    from services.rag_service import build_rag_chain

    config: ConfigService = ctx.obj["config"]
    console: Console = ctx.obj["console"]

    # Build RAG chain
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Building RAG chain...", total=None)
        rag = build_rag_chain(config)
        progress.update(task, description="[green]✓[/] RAG chain ready")

    console.print()

    # Handle different input modes
    if question:
        _run_single_question(console, rag, question, show_context)
    elif input_file:
        _run_file_questions(console, rag, input_file, show_context)
    elif stdin:
        _run_stdin_questions(console, rag, show_context)
    elif interactive:
        _run_interactive(console, rag, show_context)
    else:
        # Default to interactive if no input specified
        _run_interactive(console, rag, show_context)


def _run_single_question(console: Console, rag, question: str, show_context: bool) -> None:
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


def _run_file_questions(console: Console, rag, file_path: Path, show_context: bool) -> None:
    """Run questions from a file."""
    try:
        with file_path.open("r", encoding="utf-8") as f:
            questions = [line.strip() for line in f if line.strip()]

        for i, q in enumerate(questions, 1):
            console.print(f"[dim]Question {i}/{len(questions)}[/]")
            _run_single_question(console, rag, q, show_context)
            if i < len(questions):
                console.print("\n" + "─" * 80 + "\n")

    except Exception as e:
        console.print(f"[red]Error reading file:[/] {e}")
        sys.exit(1)


def _run_stdin_questions(console: Console, rag, show_context: bool) -> None:
    """Run questions from stdin."""
    for line in sys.stdin:
        q = line.strip()
        if q:
            _run_single_question(console, rag, q, show_context)
            console.print()


def _run_interactive(console: Console, rag, show_context: bool) -> None:
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


def _display_context(console: Console, docs) -> None:
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
