"""Query command - Query the anime database with natural language."""

import asyncio
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

import rich_click as click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

if TYPE_CHECKING:
    from services.app_context import AppContext


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
@click.option(
    "--output-format",
    type=click.Choice(["text", "json"], case_sensitive=False),
    default="text",
    help="Output format for responses (text or json)",
)
@click.pass_obj
def query(
    ctx: "AppContext",
    question: str | None,
    input_file: Path | None,
    stdin: bool,
    interactive: bool,
    show_context: bool,
    k: int,
    output_format: str,
) -> None:
    """Query the anime database with natural language.

    Ask questions about anime and get AI-powered recommendations based on
    semantic search through your anime collection.
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

    # Handle different input modes
    if question:
        asyncio.run(
            _run_single_question(console, rag, question, show_context, output_format.lower())
        )
    elif input_file:
        asyncio.run(
            _run_file_questions(console, rag, input_file, show_context, output_format.lower())
        )
    elif stdin:
        asyncio.run(_run_stdin_questions(console, rag, show_context, output_format.lower()))
    elif interactive:
        asyncio.run(_run_interactive(console, rag, show_context, output_format.lower()))
    else:
        # Default to interactive if no input specified
        asyncio.run(_run_interactive(console, rag, show_context, output_format.lower()))


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


async def _run_file_questions(
    console: Console, rag: Any, file_path: Path, show_context: bool, output_format: str
) -> None:
    """Run questions from a file."""
    try:
        with file_path.open("r", encoding="utf-8") as f:
            questions = [line.strip() for line in f if line.strip()]

        for i, q in enumerate(questions, 1):
            if output_format != "json":
                console.print(f"[dim]Question {i}/{len(questions)}[/]")
            await _run_single_question(console, rag, q, show_context, output_format)
            if i < len(questions) and output_format != "json":
                console.print("\n" + "─" * 80 + "\n")

    except Exception as e:
        console.print(f"[red]Error reading file:[/] {e}")
        sys.exit(1)


async def _run_stdin_questions(
    console: Console, rag: Any, show_context: bool, output_format: str
) -> None:
    """Run questions from stdin."""
    for line in sys.stdin:
        q = line.strip()
        if q:
            await _run_single_question(console, rag, q, show_context, output_format)
            if output_format != "json":
                console.print()


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
