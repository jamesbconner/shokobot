# Shokobot

RAG-based anime recommendation system using LangChain, ChromaDB, and OpenAI.

## Features

- Vector-based semantic search for anime shows
- Support for exact title and alias matching
- Streaming ingestion with batch processing
- Interactive REPL and CLI query modes
- Comprehensive error handling and logging

## Requirements

- Python 3.12+
- Poetry or uv for dependency management
- OpenAI API key

## Installation

### Using Poetry (Recommended)

```bash
# Install poetry if not already installed
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install

# Activate virtual environment
poetry shell
```

### Using uv (Alternative)

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .
```

## Configuration

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` and add your OpenAI API key:
```bash
OPENAI_API_KEY='your-api-key-here'
```

3. (Optional) Customize `resources/config.json` for:
   - Model selection
   - Embedding model
   - ChromaDB settings
   - Batch sizes
   - Logging levels

## Usage

### Ingestion

Load anime data into the vector store:

```bash
# Using poetry
poetry run shokobot-ingest

# Or directly
python main_ingest.py
```

### Querying

#### Interactive REPL
```bash
poetry run shokobot-rag --repl
```

#### Single Question
```bash
poetry run shokobot-rag -q "What anime are similar to Cowboy Bebop?"
```

#### From File
```bash
poetry run shokobot-rag -f questions.txt --show-context
```

#### From Stdin
```bash
echo "What are the best mecha anime?" | poetry run shokobot-rag --stdin
```

### Query Options

- `-q, --question`: Ask a single question
- `-f, --file`: Read questions from file (one per line)
- `--stdin`: Read questions from stdin
- `--repl`: Start interactive mode
- `--show-context`: Display retrieved anime titles and IDs
- `--k`: Number of documents to retrieve (default: 10)

### Special Query Patterns

- **Exact title match**: `"Cowboy Bebop"` (use quotes)
- **Alias search**: `alias:bebop`
- **Content search**: Regular text queries

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
# Format code
ruff format .

# Lint code
ruff check . --fix

# Type checking
mypy .

# Security scanning
bandit -r services models utils

# Run all pre-commit hooks
pre-commit run --all-files
```

### Testing

```bash
# Run tests with coverage
pytest

# Run specific test file
pytest tests/config/test_config_service.py

# Generate HTML coverage report
pytest --cov-report=html
open htmlcov/index.html
```

## Project Structure

```
shokobot/
├── services/           # Core business logic
│   ├── config_service.py
│   ├── ingest_service.py
│   ├── rag_service.py
│   └── vectorstore_service.py
├── models/            # Data models
│   └── show_doc.py
├── utils/             # Utility functions
│   ├── batch_utils.py
│   └── text_utils.py
├── resources/         # Configuration and metadata
│   └── config.json
├── input/             # Input files for RAG
│   └── tvshows.json
├── tests/             # Test suite
├── main_ingest.py     # Ingestion entry point
├── main_rag.py        # Query entry point
└── pyproject.toml     # Project configuration
```

## Environment Variables

All config.json settings can be overridden via environment variables:

```bash
CHROMA_PERSIST_DIRECTORY='./.chroma'
CHROMA_COLLECTION_NAME='tvshows'
OPENAI_MODEL='gpt-5-nano'
OPENAI_EMBEDDING_MODEL='text-embedding-3-small'
OPENAI_MODEL_TYPE='reasoning'
OPENAI_MAX_OUTPUT_TOKENS='4096'
INGEST_BATCH_SIZE='100'
LOGGING_LEVEL='INFO'
```

### Model Configuration

The system supports two types of OpenAI models:

**Reasoning Models** (GPT-5):
- Set `model_type: "reasoning"` in config
- Use `max_output_tokens` instead of `max_tokens`
- Do not support `temperature`, `top_p`, or `logprobs` parameters
- Examples: `gpt-5-nano`, `gpt-5`, `gpt-5-mini`

**Standard Models** (GPT-4, GPT-3.5 family):
- Set `model_type: "standard"` in config (or omit, it's the default)
- Support `temperature`, `top_p`, `logprobs` parameters
- Examples: `gpt-4o`, `gpt-4o-mini`, `gpt-3.5-turbo`

## Logging

Logs are written to stdout with configurable levels:

- `DEBUG`: Detailed diagnostic information
- `INFO`: General informational messages (default)
- `WARNING`: Warning messages
- `ERROR`: Error messages
- `CRITICAL`: Critical errors

Set via `LOGGING_LEVEL` environment variable or `logging.level` in config.json.

## License

MIT
