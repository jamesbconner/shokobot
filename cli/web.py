"""Web interface command for ShokoBot."""

import logging

import rich_click as click
from rich.console import Console

from ui.app import create_app
from ui.utils import validate_environment

console = Console()
logger = logging.getLogger(__name__)


@click.command()
@click.option(
    "--port",
    default=7860,
    type=int,
    help="Port to run the server on",
    show_default=True,
)
@click.option(
    "--share",
    is_flag=True,
    help="Create a public shareable link (via Gradio)",
)
@click.option(
    "--debug",
    is_flag=True,
    help="Enable debug mode with verbose logging",
)
def web(port: int, share: bool, debug: bool) -> None:
    """Start the Gradio web interface.

    Launch a browser-based chat interface for anime recommendations.
    The interface provides an intuitive way to query your anime collection
    without using the command line.

    Examples:

        # Start on default port (7860)
        shokobot web

        # Start on custom port
        shokobot web --port 8080

        # Create a public shareable link
        shokobot web --share

        # Enable debug logging
        shokobot web --debug
    """
    # Configure logging
    if debug:
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        console.print("[yellow]Debug mode enabled[/]")
    else:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
        )

    console.print("\n[bold cyan]🎌 ShokoBot Web Interface[/]\n")

    # Validate environment
    try:
        console.print("[dim]Validating environment...[/]")
        validate_environment()
        console.print("[green]✓[/] Environment validated")
    except OSError as e:
        console.print(f"\n[red]✗ Configuration Error:[/] {e}\n")
        console.print("[yellow]Please ensure:[/]")
        console.print("  1. OPENAI_API_KEY is set in your .env file")
        console.print("  2. You have run 'shokobot ingest' to initialize the database\n")
        raise click.Abort() from e

    # Create and launch app
    try:
        console.print("[dim]Creating Gradio application...[/]")
        app = create_app()
        console.print("[green]✓[/] Application created")

        console.print(f"\n[bold green]Starting server on port {port}...[/]\n")

        if share:
            console.print(
                "[yellow]Note:[/] Share mode will create a public URL "
                "that expires after 72 hours.\n"
            )

        # Launch the app
        app.launch(
            server_name="0.0.0.0",  # Listen on all interfaces
            server_port=port,
            share=share,
            debug=debug,
            show_error=True,
            quiet=not debug,
        )

    except KeyboardInterrupt:
        console.print("\n\n[yellow]Shutting down gracefully...[/]")
    except Exception as e:
        console.print(f"\n[red]✗ Error starting server:[/] {e}\n")
        if debug:
            raise
        raise click.Abort() from e
