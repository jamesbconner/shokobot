"""ShokoBot CLI - Modular command-line interface."""

import importlib
import pkgutil
import sys
from pathlib import Path

import rich_click as click
from dotenv import load_dotenv
from rich.console import Console

from services.app_context import AppContext

# Configure rich-click for beautiful output
click.rich_click.USE_RICH_MARKUP = True
click.rich_click.USE_MARKDOWN = True
click.rich_click.SHOW_ARGUMENTS = True
click.rich_click.GROUP_ARGUMENTS_OPTIONS = True
click.rich_click.STYLE_ERRORS_SUGGESTION = "magenta italic"
click.rich_click.ERRORS_SUGGESTION = "Try running the '--help' flag for more information."
click.rich_click.ERRORS_EPILOGUE = ""
click.rich_click.SHOW_METAVARS_COLUMN = True
click.rich_click.APPEND_METAVARS_HELP = True
click.rich_click.STYLE_OPTION = "bold cyan"
click.rich_click.STYLE_ARGUMENT = "bold cyan"
click.rich_click.STYLE_COMMAND = "bold cyan"
click.rich_click.STYLE_SWITCH = "bold green"
click.rich_click.STYLE_METAVAR = "bold yellow"
click.rich_click.STYLE_METAVAR_APPEND = "dim yellow"
click.rich_click.STYLE_HEADER_TEXT = "bold magenta"
click.rich_click.STYLE_FOOTER_TEXT = "dim"
click.rich_click.STYLE_USAGE = "bold yellow"
click.rich_click.STYLE_USAGE_COMMAND = "bold"
click.rich_click.STYLE_HELPTEXT_FIRST_LINE = "bold"
click.rich_click.STYLE_HELPTEXT = "dim"
click.rich_click.STYLE_OPTION_HELP = ""
click.rich_click.STYLE_OPTION_DEFAULT = "dim"
click.rich_click.STYLE_REQUIRED_SHORT = "red"
click.rich_click.STYLE_REQUIRED_LONG = "dim red"
click.rich_click.ALIGN_OPTIONS_PANEL = "left"
click.rich_click.ALIGN_COMMANDS_PANEL = "left"

# Load environment variables
load_dotenv()

console = Console()


@click.group()
@click.version_option(version="0.1.0", prog_name="shokobot")
@click.pass_context
def cli(ctx: click.Context) -> None:
    """ShokoBot - Anime recommendation system with RAG.

    A powerful CLI for managing anime data and querying with semantic search
    powered by ChromaDB and OpenAI embeddings.
    """
    # Initialize AppContext and store in context
    ctx.ensure_object(dict)
    try:
        ctx.obj = AppContext.create()
    except Exception as e:
        console.print(f"[red]Error loading configuration:[/] {e}")
        sys.exit(1)


def load_commands() -> None:
    """Auto-load all command modules from the cli package.

    Discovers and imports all Python modules in the cli package,
    automatically registering their Click commands with the main CLI group.
    """
    # Get the cli package directory
    cli_dir = Path(__file__).parent

    # Iterate through all modules in the cli package
    for _, module_name, is_pkg in pkgutil.iter_modules([str(cli_dir)]):
        # Skip __init__ and non-command modules
        if module_name.startswith("_") or is_pkg:
            continue

        # Import the module
        try:
            module = importlib.import_module(f"cli.{module_name}")

            # Look for a Click command or group in the module
            for attr_name in dir(module):
                attr = getattr(module, attr_name)

                # Check if it's a Click command and not the main cli group
                if (
                    isinstance(attr, click.Command)
                    and attr is not cli
                    and not attr_name.startswith("_")
                ):
                    # Register the command with the main CLI group
                    cli.add_command(attr)

        except Exception as e:
            console.print(f"[yellow]Warning: Failed to load command module '{module_name}': {e}[/]")


# Auto-load all commands
load_commands()
