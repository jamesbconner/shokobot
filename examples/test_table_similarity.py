#!/usr/bin/env python3
"""Test table output with similarity scores.

This example demonstrates the enhanced --show-context table that now
includes similarity scores with color-coded quality indicators.

Usage:
    export OPENAI_API_KEY="your-api-key"
    python examples/test_table_similarity.py
"""

import asyncio
import os
import sys


async def main():
    """Test table output with similarity scores."""
    if not os.environ.get("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY environment variable not set!")
        print("Set it with: export OPENAI_API_KEY='your-key'")
        sys.exit(1)

    from rich.console import Console
    from rich.table import Table

    from services.app_context import AppContext

    console = Console()

    console.print("[bold]Testing Table Output with Similarity Scores[/]\n")

    ctx = AppContext.create()
    rag = ctx.get_rag_chain()

    # Test query
    question = "What is Cowboy Bebop about?"
    console.print(f"[bold cyan]Q:[/] {question}\n")

    answer, docs = await rag(question)

    console.print(f"[bold green]A:[/] {answer[:200]}...\n")

    # Display context table with similarity scores
    if docs:
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

    console.print("[bold]Similarity Score Guide:[/]")
    console.print("  [green]MCP[/] = Result from external source (AniDB)")
    console.print("  [green]0.0-0.3[/] = Excellent match")
    console.print("  [blue]0.3-0.6[/] = Very good match")
    console.print("  [yellow]0.6-0.9[/] = Good match")
    console.print("  [red]0.9+[/] = Moderate/poor match")
    console.print()
    console.print("[dim]Lower scores = better semantic similarity![/]")
    console.print()
    console.print("[bold]Try it yourself:[/]")
    console.print("  python -m cli.query --show-context")
    console.print("  python -m cli.repl --show-context")


if __name__ == "__main__":
    asyncio.run(main())
