# Modular CLI Architecture

## Overview
The ShokoBot CLI uses a modular, auto-loading architecture where each command is a separate module in the `cli/` directory. Commands are automatically discovered and registered without manual configuration, making it easy to add new functionality.

## Structure

```
cli/
├── __init__.py      # Main CLI group with auto-loader
├── info.py          # Display configuration and system information
├── ingest.py        # Ingest anime data into vector database
├── query.py         # Query database with natural language
└── repl.py          # Interactive REPL mode

cli.py               # Optional entry point for direct execution
```

## How It Works

### 1. Auto-Loading Mechanism

The `cli/__init__.py` module contains an auto-loader that:
1. Scans the `cli/` directory for Python modules
2. Imports each module
3. Discovers Click commands in each module
4. Automatically registers them with the main CLI group

```python
def load_commands() -> None:
    """Auto-load all command modules from the cli package."""
    cli_dir = Path(__file__).parent

    for _, module_name, is_pkg in pkgutil.iter_modules([str(cli_dir)]):
        if module_name.startswith("_") or is_pkg:
            continue

        module = importlib.import_module(f"cli.{module_name}")

        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if isinstance(attr, click.Command) and attr is not cli:
                cli.add_command(attr)
```

### 2. Command Modules

Each command module follows this pattern:

```python
"""Command description."""

import rich_click as click

if TYPE_CHECKING:
    from rich.console import Console
    from services.config_service import ConfigService


@click.command()
@click.option(...)  # Command-specific options
@click.pass_context
def command_name(ctx: click.Context, ...) -> None:
    """Command help text."""
    config: ConfigService = ctx.obj["config"]
    console: Console = ctx.obj["console"]

    # Command implementation
```

### 3. Rich-Click Integration

The CLI uses Rich-Click for beautiful, formatted output with:
- Boxed sections with Unicode borders
- Color-coded options and commands
- Professional styling and layout
- Enhanced help text formatting

```python
import rich_click as click

# Rich-Click configuration in cli/__init__.py
click.rich_click.USE_RICH_MARKUP = True
click.rich_click.STYLE_OPTION = "bold cyan"
click.rich_click.STYLE_COMMAND = "bold cyan"
# ... additional styling options
```

### 4. Shared Context

The main CLI group initializes shared resources:
- `ConfigService` instance (with dependency injection)
- `Console` instance for Rich output

These are stored in the Click context and accessed by commands:

```python
@click.group()
@click.version_option(version="0.1.0", prog_name="shokobot")
@click.pass_context
def cli(ctx: click.Context) -> None:
    """ShokoBot - Anime recommendation system with RAG."""
    ctx.ensure_object(dict)
    try:
        ctx.obj["config"] = ConfigService()
        ctx.obj["console"] = console
    except Exception as e:
        console.print(f"[red]Error loading configuration:[/] {e}")
        sys.exit(1)
```

## Adding New Commands

To add a new command, simply create a new file in `cli/`:

```python
# cli/stats.py
"""Stats command - Display database statistics."""

import rich_click as click

if TYPE_CHECKING:
    from rich.console import Console
    from services.config_service import ConfigService


@click.command()
@click.pass_context
def stats(ctx: click.Context) -> None:
    """Display database statistics."""
    config: ConfigService = ctx.obj["config"]
    console: Console = ctx.obj["console"]

    console.print("[bold]Database Statistics[/]\n")
    # Implementation here
```

The command will be automatically discovered and registered. No need to modify `__init__.py`!

## Benefits

### 1. Modularity
- Each command is self-contained in its own file
- Easy to understand and maintain
- Clear separation of concerns

### 2. Scalability
- Add new commands without modifying existing code
- No central registration required
- Commands can be developed independently

### 3. Discoverability
- All commands are in one directory
- Easy to find and navigate
- Clear naming convention

### 4. Testability
- Each command can be tested in isolation
- Mock context objects easily
- Unit test individual commands

### 5. Maintainability
- Changes to one command don't affect others
- Easier code reviews (smaller files)
- Reduced merge conflicts

## Command Structure

### Required Elements

1. **Click decorator**: `@click.command()`
2. **Context parameter**: `@click.pass_context`
3. **Docstring**: For help text
4. **Context access**: Get config and console from `ctx.obj`

### Optional Elements

1. **Options**: `@click.option(...)`
2. **Arguments**: `@click.argument(...)`
3. **Helper functions**: Private functions prefixed with `_`

## Example: Complete Command Module

```python
"""Example command - Demonstrates command structure."""

import rich_click as click

if TYPE_CHECKING:
    from rich.console import Console
    from rich.table import Table
    from services.config_service import ConfigService


@click.command()
@click.option(
    "--format",
    "-f",
    type=click.Choice(["table", "json"]),
    default="table",
    help="Output format",
)
@click.pass_context
def example(ctx: click.Context, format: str) -> None:
    """Example command demonstrating structure.

    This command shows how to:
    - Access shared context
    - Use options
    - Display formatted output
    """
    config: ConfigService = ctx.obj["config"]
    console: Console = ctx.obj["console"]

    if format == "table":
        _display_table(console)
    else:
        _display_json(console)


def _display_table(console: Console) -> None:
    """Display output as a table."""
    table = Table(title="Example Data")
    table.add_column("Name", style="cyan")
    table.add_column("Value", style="yellow")
    table.add_row("Example", "Data")
    console.print(table)


def _display_json(console: Console) -> None:
    """Display output as JSON."""
    import json
    data = {"example": "data"}
    console.print(json.dumps(data, indent=2))
```

## Testing Commands

Commands can be tested using Click's testing utilities:

```python
from click.testing import CliRunner
from cli import cli


def test_info_command():
    runner = CliRunner()
    result = runner.invoke(cli, ['info'])
    assert result.exit_code == 0
    assert "ShokoBot Configuration" in result.output


def test_query_command():
    runner = CliRunner()
    result = runner.invoke(cli, ['query', '-q', 'test question'])
    assert result.exit_code == 0
```

## File Organization

### Current Commands (4 commands)

- `cli/info.py` - Display configuration and system information
- `cli/ingest.py` - Ingest anime data into vector database
- `cli/query.py` - Query database with natural language (multiple input modes)
- `cli/repl.py` - Interactive REPL mode for querying

### Potential Future Commands

- `cli/stats.py` - Database statistics
- `cli/export.py` - Export data
- `cli/validate.py` - Validate data integrity
- `cli/backup.py` - Backup/restore operations
- `cli/search.py` - Advanced search features

## Best Practices

1. **Keep commands focused**: One command, one responsibility
2. **Use helper functions**: Extract complex logic into private functions
3. **Consistent naming**: Use descriptive, verb-based names
4. **Rich formatting**: Leverage Rich for beautiful output
5. **Error handling**: Provide clear error messages
6. **Documentation**: Include comprehensive docstrings
7. **Type hints**: Use type annotations for clarity

## Advantages Over Monolithic Approach

1. **Easier navigation**: Find commands quickly
2. **Parallel development**: Multiple developers can work on different commands
3. **Clearer git history**: Changes are isolated to specific files
4. **Better IDE support**: Smaller files load faster
5. **Reduced cognitive load**: Focus on one command at a time
6. **Flexible organization**: Can add subdirectories for command groups

## Future Enhancements

1. **Command groups**: Organize related commands
   ```
   cli/
   ├── db/
   │   ├── backup.py
   │   ├── restore.py
   │   └── stats.py
   └── data/
       ├── import.py
       └── export.py
   ```

2. **Plugin system**: Load commands from external packages
3. **Command aliases**: Short names for common commands
4. **Shell completion**: Auto-complete for commands and options
5. **Configuration profiles**: Switch between different configs


## Entry Points

### Poetry Script (Recommended)
```bash
poetry run shokobot [command] [options]
```

Defined in `pyproject.toml`:
```toml
[tool.poetry.scripts]
shokobot = "cli:cli"
```

This points to the `cli()` function in `cli/__init__.py`.

### Direct Execution (Optional)
```bash
python cli.py [command] [options]
```

The `cli.py` file in the project root provides a convenience wrapper for direct execution without poetry. This is useful for development and debugging.

## Dependency Injection

All services use dependency injection - configuration is passed as parameters rather than using global instances:

```python
# Services accept config parameter
def get_chroma_vectorstore(config: ConfigService) -> Chroma:
    persist_dir = config.get("chroma.persist_directory")
    ...

# CLI commands pass config from context
config: ConfigService = ctx.obj["config"]
rag = build_rag_chain(config)
```

This makes the code:
- More testable (easy to mock configuration)
- More maintainable (explicit dependencies)
- More flexible (support multiple configurations)

## Conclusion

The modular CLI architecture provides a scalable, maintainable foundation for the ShokoBot CLI. Adding new commands is as simple as creating a new file, and the auto-loader handles the rest.

**Key Features**:
- Auto-loading command discovery
- Rich-Click for beautiful output
- Dependency injection throughout
- Modular, testable architecture
- Easy to extend and maintain
