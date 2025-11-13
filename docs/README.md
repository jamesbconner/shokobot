# ShokoBot Documentation

Complete documentation for ShokoBot, an anime RAG (Retrieval-Augmented Generation) system.

## For Users

### [User Guide](USER_GUIDE.md) 📖
Complete guide to using ShokoBot for anime queries and recommendations.

**Topics:**
- Quick start and CLI commands
- Context display with similarity scores
- Understanding distance scores and MCP fallback
- Configuration and troubleshooting
- Advanced usage and batch processing

## For Developers

### [Modular CLI Architecture](MODULAR_CLI_ARCHITECTURE.md) 🏗️
Comprehensive guide to the CLI architecture.

**Topics:**
- Auto-loading command discovery
- Rich-Click integration
- Adding new commands
- Testing strategies
- Best practices

### [AppContext Usage Guide](APPCONTEXT_USAGE.md) 💉
Dependency injection with AppContext.

**Topics:**
- Creating and using AppContext
- Lazy-loaded services
- Testing with mocks
- Best practices and patterns
- Migration examples

### [MCP Integration Guide](MCP_INTEGRATION.md) 🔌
Model Context Protocol integration for anime data fallback.

**Topics:**
- Configuration and thresholds
- Title extraction (regex + LLM)
- Fallback logic
- Monitoring and troubleshooting
- Performance considerations

### [Testing Strategy](TESTING_STRATEGY.md) ✅
Testing philosophy and best practices.

**Topics:**
- What to test (and what not to)
- Test organization and fixtures
- AAA pattern and best practices
- Coverage goals
- Pre-commit hooks and CI/CD

## Reference

### [ShowDoc JSON Format](SHOWDOC_JSON_EXAMPLE.md) 📄
Data format reference for ShowDoc persistence.

**Topics:**
- JSON structure and fields
- Usage examples
- Cache management
- Integration workflow

## Quick Start

```bash
# Set your OpenAI API key
export OPENAI_API_KEY="your-api-key"

# Basic query
poetry run shokobot query -q "What is Cowboy Bebop about?"

# With context display
poetry run shokobot query -q "Tell me about mecha anime" --show-context

# Interactive mode
poetry run shokobot repl --show-context
```

## Key Features

- ✅ **Vector Store Search**: Fast local anime database queries
- ✅ **MCP Fallback**: Automatic AniDB integration for comprehensive coverage
- ✅ **Smart Title Extraction**: Regex + LLM hybrid for natural language queries
- ✅ **Rich Context Display**: Color-coded similarity scores and source indicators
- ✅ **GPT-5 Integration**: Latest model with Responses API support

## System Requirements

- Python 3.11+
- OpenAI API key (GPT-5 access)
- uvx (for MCP server)
- 4GB+ RAM (for vector store)

## Documentation Structure

```
docs/
├── README.md                      # This file
├── USER_GUIDE.md                  # User-facing guide
├── MCP_INTEGRATION.md             # MCP integration guide
├── MODULAR_CLI_ARCHITECTURE.md    # CLI architecture
├── APPCONTEXT_USAGE.md            # Dependency injection guide
├── TESTING_STRATEGY.md            # Testing guidelines
├── SHOWDOC_JSON_EXAMPLE.md        # Data format reference
└── archive/                       # Historical documentation
```

## Support

- **Debug Scripts**: `debug/` directory contains troubleshooting tools
- **Configuration**: `resources/config.json` for system settings
- **Examples**: `examples/` directory for usage examples

---

**Status**: ✅ All systems operational
**Last Updated**: 2024-11-13
**Version**: Latest
