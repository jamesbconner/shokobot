# ShokoBot Documentation

## Architecture Documentation

### [Modular CLI Architecture](MODULAR_CLI_ARCHITECTURE.md)
Comprehensive guide to the modular CLI architecture, including:
- Auto-loading command discovery
- Rich-Click integration for beautiful output
- Dependency injection patterns
- How to add new commands
- Testing strategies
- Best practices

## Quick Links

### For Users
- [Main README](../README.md) - Getting started and usage
- [Quick Reference](../QUICK_REFERENCE.md) - Common commands
- [Setup Guide](../SETUP_GUIDE.md) - Installation instructions

### For Developers
- [Modular CLI Architecture](MODULAR_CLI_ARCHITECTURE.md) - CLI design and patterns
- [AppContext Usage Guide](APPCONTEXT_USAGE.md) - **Dependency injection with AppContext** ⭐
- [Async Opportunities](ASYNC_OPPORTUNITIES_ANALYSIS.md) - Performance optimization opportunities

## Contributing

When adding new CLI commands:
1. Create a new file in `cli/` directory
2. Use `@click.command()` decorator
3. Follow the patterns in existing commands
4. The command will be auto-discovered

See [Modular CLI Architecture](MODULAR_CLI_ARCHITECTURE.md) for detailed guidance.
