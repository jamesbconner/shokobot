# ShokoBot

RAG-based anime recommendation system using LangChain, ChromaDB, and OpenAI GPT-5.

## Features

- 🔍 **Vector-based semantic search** - Find anime using natural language queries
- 🎯 **Comprehensive metadata** - 21 fields per anime including ratings, episodes, dates, and relationships
- 📊 **Efficient ingestion** - Batch processing with progress indicators (1,458 anime records)
- 💬 **Multiple query modes** - Interactive REPL, single questions, file input, or stdin
- 🎨 **Beautiful CLI** - Rich formatting with tables, colors, and progress bars
- 📤 **JSON output format** - Structured output for programmatic usage and API integration
- ⚙️ **Flexible configuration** - JSON config with environment variable overrides
- 🤖 **GPT-5 integration** - Responses API with configurable reasoning effort
- 🏗️ **Modular architecture** - Auto-loading CLI commands with dependency injection
- ✅ **Type-safe** - Full Pydantic validation and mypy strict mode
- 📝 **Well-documented** - Comprehensive guides and architecture documentation

## Requirements

- Python 3.12+
- Poetry (for build system) or uv (for dependency management)
- OpenAI API key

## Quick Start

### Automated Setup

```bash
# Run the setup script
./setup.sh

# Edit .env and add your OpenAI API key
export OPENAI_API_KEY='your-key-here'

# Verify configuration
poetry run shokobot info

# Ingest anime data
poetry run shokobot ingest

# Start querying
poetry run shokobot repl
```

## Installation

### Using Poetry (Recommended)

```bash
# Install poetry if not already installed
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install

# Activate virtual environment (optional)
poetry shell
```

### Using uv (Alternative)

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e ".[dev]"
```

## Configuration

### Environment Setup

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` and add your OpenAI API key:
```bash
OPENAI_API_KEY='your-api-key-here'
```

3. (Optional) Override config.json settings via environment variables:
```bash
# Pattern: SECTION_KEY (e.g., OPENAI_MODEL overrides openai.model)
OPENAI_MODEL='gpt-5-nano'
OPENAI_REASONING_EFFORT='high'
CHROMA_COLLECTION_NAME='my_anime'
```

### Configuration File

Edit `resources/config.json` to customize:

```json
{
  "chroma": {
    "persist_directory": "./.chroma",
    "collection_name": "tvshows"
  },
  "data": {
    "shows_json": "input/shoko_tvshows.json"
  },
  "openai": {
    "model": "gpt-5-nano",
    "embedding_model": "text-embedding-3-small",
    "reasoning_effort": "medium",
    "output_verbosity": "medium",
    "max_output_tokens": 8192
  },
  "ingest": {
    "batch_size": 100
  },
  "logging": {
    "level": "INFO"
  }
}
```

## Usage

### CLI Commands

#### View Configuration
```bash
poetry run shokobot info
```

Displays current configuration, including ChromaDB settings, OpenAI model, and data paths.

#### Ingest Data
```bash
# Use default settings (1,458 anime records)
poetry run shokobot ingest

# Dry-run: validate data without ingesting
poetry run shokobot ingest --dry-run

# Custom input file and batch size
poetry run shokobot ingest -i custom.json -b 200

# Use AniDB_AnimeID as primary identifier
poetry run shokobot ingest --id-field AniDB_AnimeID
```

**Options:**
- `-i, --input PATH` - Path to JSON file (overrides config)
- `-b, --batch-size INTEGER` - Documents per batch (overrides config)
- `--id-field [AnimeID|AniDB_AnimeID]` - Primary ID field
- `--dry-run` - Validate mappings and show statistics without ingesting

**Dry-Run Mode:**
Use `--dry-run` to validate your data before ingestion. This mode:
- Validates all document mappings
- Shows total document count and batch statistics
- Displays year range and episode statistics
- Lists sample titles (first 10)
- Reports any validation errors
- Does NOT insert data into the vector store

#### Query Database
```bash
# Single question
poetry run shokobot query -q "What anime are similar to Cowboy Bebop?"

# With context display
poetry run shokobot query -q "Best mecha anime?" -c

# From file (batch processing)
poetry run shokobot query -f questions.txt

# From stdin
echo "What is Steins;Gate about?" | poetry run shokobot query --stdin

# Interactive mode
poetry run shokobot query -i
```

**Options:**
- `-q, --question TEXT` - Single question to ask
- `-f, --file PATH` - File with questions (one per line)
- `--stdin` - Read questions from stdin
- `-i, --interactive` - Start interactive REPL mode
- `-c, --show-context` - Display retrieved context documents
- `--k INTEGER` - Number of documents to retrieve (default: 10)
- `--output-format [text|json]` - Output format (default: text)

#### Interactive REPL
```bash
# Start REPL mode (recommended for multiple queries)
poetry run shokobot repl

# With context display
poetry run shokobot repl -c

# With custom retrieval count
poetry run shokobot repl --k 15
```

**Options:**
- `-c, --show-context` - Display retrieved context documents
- `--k INTEGER` - Number of documents to retrieve
- `--output-format [text|json]` - Output format (default: text)

**REPL Commands:**
- Type your question and press Enter
- `exit`, `quit`, or `q` to leave
- Questions are processed with cached RAG chain for efficiency

#### JSON Output Format

For programmatic usage and service integration, both `query` and `repl` commands support JSON output:

```bash
# Single question with JSON output
poetry run shokobot query -q "What is Frieren about?" --output-format json

# With context metadata
poetry run shokobot query -q "Recommend a sci-fi anime" --output-format json --show-context

# Interactive mode with JSON
poetry run shokobot repl --output-format json

# From file (batch processing)
poetry run shokobot query -f questions.txt --output-format json

# From stdin (pipeline integration)
echo "What is Cowboy Bebop about?" | poetry run shokobot query --stdin --output-format json
```

**JSON Response Structure:**
```json
{
  "question": "What is Frieren about?",
  "answer": "Frieren (Sousou no Frieren) is an action-adventure fantasy...",
  "context": [
    {
      "title": "Sousou no Frieren",
      "anime_id": "17617",
      "year": 2023,
      "episodes": 28
    }
  ]
}
```

**Use Cases:**
- Building APIs or microservices on top of ShokoBot
- Automating batch processing of queries
- Integrating with other services that expect structured data
- Parsing and storing responses in databases
- Creating custom frontends or chatbots

**Programmatic Example:**
```python
import subprocess
import json

result = subprocess.run(
    ["poetry", "run", "shokobot", "query", 
     "-q", "Recommend a sci-fi anime", 
     "--output-format", "json"],
    capture_output=True,
    text=True
)

data = json.loads(result.stdout)
print(f"Answer: {data['answer']}")
if 'context' in data:
    print(f"Found {len(data['context'])} relevant anime")
```

### Using with uv

Replace `poetry run` with `uv run`:

```bash
uv run shokobot info
uv run shokobot ingest
uv run shokobot repl
uv run shokobot query -q "..."
```

## Development

### Setup Development Environment

```bash
# Install with dev dependencies
poetry install --with dev

# Install pre-commit hooks
pre-commit install
```

### Code Quality Tools

```bash
# Format code with ruff
poetry run ruff format .

# Lint code with ruff
poetry run ruff check .
poetry run ruff check . --fix  # Auto-fix issues

# Type checking with mypy (strict mode)
poetry run mypy . --strict

# Security scanning with bandit
poetry run bandit -r services models utils cli

# Run all pre-commit hooks
poetry run pre-commit run --all-files
```

### Testing

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov

# Run specific test file
poetry run pytest tests/config/test_config_service.py

# Verbose output
poetry run pytest -v

# Generate HTML coverage report
poetry run pytest --cov-report=html
open htmlcov/index.html
```

### Pre-commit Hooks

The project uses pre-commit hooks for automated quality checks:

- **ruff** - Code formatting and linting
- **mypy** - Type checking
- **trailing-whitespace** - Remove trailing whitespace
- **end-of-file-fixer** - Ensure files end with newline
- **check-yaml** - Validate YAML files
- **check-json** - Validate JSON files

Hooks run automatically on `git commit`. To run manually:

```bash
pre-commit run --all-files
```

## Project Structure

```
shokobot/
├── cli/                         # Modular CLI commands (auto-loaded)
│   ├── __init__.py             # Main CLI group with auto-loader
│   ├── info.py                 # Configuration display
│   ├── ingest.py               # Data ingestion
│   ├── query.py                # Natural language queries
│   └── repl.py                 # Interactive REPL mode
├── services/                    # Business logic (dependency injection)
│   ├── app_context.py          # Application context
│   ├── config_service.py       # Configuration management
│   ├── ingest_service.py       # Data ingestion logic
│   ├── rag_service.py          # RAG chain with GPT-5
│   └── vectorstore_service.py  # ChromaDB operations
├── models/                      # Pydantic data models
│   └── show_doc.py             # ShowDoc model (21 fields)
├── prompts/                     # LLM prompt templates (versioned)
│   ├── __init__.py             # Prompt exports
│   ├── anime_rag.py            # Anime RAG prompts
│   └── README.md               # Prompt engineering guide
├── utils/                       # Utility functions
│   ├── batch_utils.py          # Batch processing helpers
│   └── text_utils.py           # Text cleaning utilities
├── docs/                        # Documentation
│   ├── README.md               # Documentation index
│   ├── MODULAR_CLI_ARCHITECTURE.md
│   ├── APPCONTEXT_USAGE.md     # Dependency injection guide
│   └── ASYNC_OPPORTUNITIES_ANALYSIS.md
├── resources/                   # Configuration files
│   └── config.json             # Main configuration
├── input/                       # Data files
│   └── shoko_tvshows.json      # Anime data (1,458 records)
├── tests/                       # Test suite
│   ├── config/                 # Config service tests
│   ├── ingest/                 # Ingestion tests
│   └── models/                 # Model tests
├── .env.example                 # Environment template
├── pyproject.toml              # Poetry configuration
├── setup.sh                    # Automated setup script
├── README.md                   # This file
├── SETUP_GUIDE.md              # Detailed setup instructions
└── QUICK_REFERENCE.md          # Command reference
```

## Data Model

The `ShowDoc` Pydantic model includes 21 comprehensive fields:

**Identifiers:**
- `anime_id` - Unique Shoko anime identifier
- `anidb_anime_id` - AniDB anime identifier

**Titles:**
- `title_main` - Primary anime title
- `title_alts` - Alternate titles (auto-cleaned)

**Content:**
- `description` - Anime description
- `tags` - Tags and genres (auto-cleaned)

**Episodes:**
- `episode_count_normal` - Number of regular episodes
- `episode_count_special` - Number of special episodes

**Dates:**
- `air_date` - Initial air date
- `end_date` - Final air date
- `begin_year` - Year began airing
- `end_year` - Year finished airing

**Ratings:**
- `rating` - AniDB rating score (0-1000)
- `vote_count` - Number of votes
- `avg_review_rating` - Average review rating
- `review_count` - Number of reviews

**External IDs:**
- `ann_id` - Anime News Network ID
- `crunchyroll_id` - Crunchyroll ID
- `wikipedia_id` - Wikipedia page identifier

**Relationships:**
- `relations` - JSON string of related anime
- `similar` - JSON string of similar anime

## Environment Variables

All `config.json` settings can be overridden via environment variables using the pattern `SECTION_KEY`:

```bash
# ChromaDB
CHROMA_PERSIST_DIRECTORY='./.chroma'
CHROMA_COLLECTION_NAME='tvshows'

# Data
DATA_SHOWS_JSON='input/shoko_tvshows.json'

# OpenAI
OPENAI_MODEL='gpt-5-nano'
OPENAI_EMBEDDING_MODEL='text-embedding-3-small'
OPENAI_REASONING_EFFORT='medium'      # low/medium/high
OPENAI_OUTPUT_VERBOSITY='medium'      # low/medium/high
OPENAI_MAX_OUTPUT_TOKENS='8192'

# Ingestion
INGEST_BATCH_SIZE='100'

# Logging
LOGGING_LEVEL='INFO'                  # DEBUG/INFO/WARNING/ERROR/CRITICAL
```

## GPT-5 Configuration

ShokoBot uses OpenAI's GPT-5 Responses API with reasoning capabilities:

**Supported Models:**
- `gpt-5-nano` (default)
- `gpt-5-mini`
- `gpt-5`

**Reasoning Effort:**
- `low` - Faster responses, less reasoning
- `medium` - Balanced (default)
- `high` - More thorough reasoning, slower

**Output Verbosity:**
- `low` - Concise responses
- `medium` - Balanced (default)
- `high` - Detailed explanations

**Note:** GPT-5 models use `max_output_tokens` instead of `max_tokens` and do not support `temperature`, `top_p`, or `logprobs` parameters.

## Architecture

### System Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                         CLI Layer                           │
│  ┌──────┐  ┌────────┐  ┌───────┐  ┌──────┐                  │
│  │ info │  │ ingest │  │ query │  │ repl │                  │
│  └──┬───┘  └───┬────┘  └───┬───┘  └───┬──┘                  │
└─────┼─────────┼───────────┼──────────┼──────────────────────┘
      │         │           │          │
      └─────────┴───────────┴──────────┘
                     │
      ┌──────────────▼──────────────────────────────────────┐
      │           Application Context                       │
      │  ┌────────────────┐  ┌────────────────────┐         │
      │  │ ConfigService  │  │ VectorStoreService │         │
      │  └────────────────┘  └────────────────────┘         │
      └─────────────────────────────────────────────────────┘
                     │
      ┌──────────────┴──────────────────────────────────────┐
      │              Service Layer                          │
      │  ┌────────────────┐  ┌──────────────────┐           │
      │  │ IngestService  │  │   RAGService     │           │
      │  └────────────────┘  └──────────────────┘           │
      └─────────────────────────────────────────────────────┘
                     │
      ┌──────────────┴──────────────────────────────────────┐
      │            Data & External                          │
      │  ┌──────────┐  ┌──────────┐  ┌──────────┐           │
      │  │ ChromaDB │  │ OpenAI   │  │ ShowDoc  │           │
      │  └──────────┘  └──────────┘  └──────────┘           │
      └─────────────────────────────────────────────────────┘
```

### Design Patterns

- **Modular CLI** - Auto-loading command discovery from `cli/` directory
- **Dependency Injection** - Services injected via `AppContext`
- **Rich Formatting** - Professional CLI with Rich-Click
- **Pydantic Validation** - Type-safe data models with automatic validation
- **Batch Processing** - Efficient chunked operations for large datasets

### Key Components

1. **CLI Layer** - Rich-Click commands with auto-loading
2. **Application Context** - Centralized service management
3. **Service Layer** - Business logic with dependency injection
4. **Data Layer** - ChromaDB vector store and OpenAI embeddings
5. **Model Layer** - Pydantic models with validation

## Documentation

### User Guides
- [README.md](README.md) - This file (project overview)
- [SETUP_GUIDE.md](SETUP_GUIDE.md) - Detailed setup instructions
- [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Command reference and examples

### Architecture Documentation
- [docs/README.md](docs/README.md) - Documentation index
- [docs/MODULAR_CLI_ARCHITECTURE.md](docs/MODULAR_CLI_ARCHITECTURE.md) - CLI design patterns
- [docs/APPCONTEXT_USAGE.md](docs/APPCONTEXT_USAGE.md) - Dependency injection guide
- [docs/ASYNC_OPPORTUNITIES_ANALYSIS.md](docs/ASYNC_OPPORTUNITIES_ANALYSIS.md) - Performance analysis

## Troubleshooting

### Common Issues

**OpenAI API Key not set:**
```bash
export OPENAI_API_KEY='your-key-here'
# Or add to .env file
```

**ChromaDB permission issues:**
```bash
rm -rf ./.chroma
poetry run shokobot ingest
```

**Import errors:**
```bash
poetry install
poetry run shokobot --help
```

**Module not found:**
```bash
# Ensure you're using poetry run or uv run
poetry run shokobot info

# Or activate the virtual environment
poetry shell
shokobot info
```

## Performance

- **Ingestion**: ~40-50 seconds for 1,458 anime records
- **Query Response**: ~3-6 seconds (including LLM processing)
- **Interactive Mode**: Cached RAG chain for efficiency
- **Batch Size**: 100 documents per batch (configurable)

## Tips & Best Practices

### Performance
- Use `repl` mode for multiple queries (avoids reloading RAG chain)
- Adjust `--k` parameter to control context size (default: 10)
- Increase batch size for faster ingestion on powerful machines
- Use environment variables for quick configuration changes

### Data Quality
- Ensure `input/shoko_tvshows.json` is properly formatted JSON
- Check logs for validation errors during ingestion
- Use `--id-field` to control primary identifier selection

### Querying
- Be specific in questions for better results
- Use natural language (e.g., "romance anime with strong characters")
- Try different phrasings if results aren't satisfactory
- Use context display (`-c`) to understand retrieval quality

### Development
- Run `poetry run shokobot info` to verify configuration
- Use `--show-context` to debug RAG retrieval
- Check `docs/` for architecture details before modifying
- Follow Python 3.12+ type hints and Pydantic patterns

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run quality checks: `pre-commit run --all-files`
5. Run tests: `pytest`
6. Submit a pull request

## License

MIT

## Resources

### Python & Tools
- [Python 3.12 Docs](https://docs.python.org/3.12/)
- [Poetry Documentation](https://python-poetry.org/docs/)
- [uv Documentation](https://docs.astral.sh/uv/)
- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [MyPy Documentation](https://mypy.readthedocs.io/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Bandit Documentation](https://bandit.readthedocs.io/)
- [Pre-commit Documentation](https://pre-commit.com/)

### Frameworks & Libraries
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Click Documentation](https://click.palletsprojects.com/)
- [Rich Documentation](https://rich.readthedocs.io/)
- [Rich-Click Documentation](https://github.com/ewels/rich-click)

### AI & Vector Databases
- [LangChain Documentation](https://python.langchain.com/)
- [LangChain ChatOpenAI](https://python.langchain.com/docs/integrations/chat/openai)
- [LangChain API Reference](https://api.python.langchain.com/)
- [ChromaDB Documentation](https://docs.trychroma.com/)
- [OpenAI API Documentation](https://platform.openai.com/docs/)
- [OpenAI Responses API](https://platform.openai.com/docs/guides/responses-vs-chat-completions)
- [OpenAI Reasoning Models](https://platform.openai.com/docs/guides/reasoning)
