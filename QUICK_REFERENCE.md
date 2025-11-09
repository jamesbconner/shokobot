# Shokobot Quick Reference

## Setup (First Time)
```bash
./setup.sh                    # Automated setup
# or manually:
poetry install --with dev     # Install dependencies
cp .env.example .env          # Create environment file
# Edit .env with your OPENAI_API_KEY
```

## Common Commands

### Development
```bash
make format          # Format code with ruff
make lint            # Lint code with ruff
make type-check      # Type check with mypy
make security        # Security scan with bandit
make test            # Run tests
make test-cov        # Run tests with coverage
make check           # Run all quality checks
```

### Application
```bash
make ingest          # Ingest anime data
make rag             # Start interactive REPL
make rag Q="..."     # Ask single question
```

### Poetry Commands
```bash
poetry install                # Install dependencies
poetry install --with dev     # Install with dev tools
poetry run shokobot-ingest    # Run ingestion
poetry run shokobot-rag       # Run RAG interface
poetry shell                  # Activate virtual environment
poetry update                 # Update dependencies
```

## File Structure
```
shokobot/
├── services/              # Core business logic
│   ├── config_service.py
│   ├── ingest_service.py
│   ├── rag_service.py
│   └── vectorstore_service.py
├── models/               # Data models
│   └── show_doc.py
├── utils/                # Utilities
│   ├── batch_utils.py
│   └── text_utils.py
├── resources/            # Config and data
│   ├── config.json
│   └── tvshows.json
├── tests/                # Test suite
├── main_ingest.py        # Ingestion entry point
├── main_rag.py           # Query entry point
├── pyproject.toml        # Project config
├── .env                  # Environment variables (not in git)
└── .env.example          # Environment template
```

## Configuration

### Environment Variables (.env)
```bash
OPENAI_API_KEY='sk-...'                              # Required
CHROMA_PERSIST_DIRECTORY='./.chroma'                 # Optional
CHROMA_COLLECTION_NAME='tvshows'                     # Optional
OPENAI_MODEL='gpt-5-nano'                            # Required: Must be a gpt-5 model
OPENAI_EMBEDDING_MODEL='text-embedding-3-small'      # Optional
OPENAI_REASONING_EFFORT='medium'                     # Optional: low/medium/high
OPENAI_OUTPUT_VERBOSITY='medium'                     # Optional: low/medium/high
OPENAI_MAX_OUTPUT_TOKENS='4096'                      # Optional
INGEST_BATCH_SIZE='100'                              # Optional
LOGGING_LEVEL='INFO'                                 # Optional
```

**Note:** Shokobot is configured specifically for GPT-5 models. The service will validate that the configured model starts with "gpt-5" and raise an error otherwise.

### Config File (resources/config.json)
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
    "model_type": "reasoning",
    "max_output_tokens": 4096
  },
  "ingest": {
    "batch_size": 100
  },
  "logging": {
    "level": "INFO"
  }
}
```

**Model Types:**
- `"reasoning"` - For GPT-5 and o1 models (no temperature, uses max_output_tokens)
- `"standard"` - For GPT-4, GPT-3.5 models (supports temperature, top_p, etc.)

## Query Modes

### Interactive REPL
```bash
poetry run shokobot-rag --repl
> What anime are similar to Cowboy Bebop?
```

### Single Question
```bash
poetry run shokobot-rag -q "What are the best mecha anime?"
```

### From File
```bash
poetry run shokobot-rag -f questions.txt --show-context
```

### From Stdin
```bash
echo "What anime have great soundtracks?" | poetry run shokobot-rag --stdin
```

### Special Query Patterns
- Exact title: `"Cowboy Bebop"` (use quotes)
- Alias search: `alias:bebop`
- Content search: Regular text

## Quality Checks

### Before Committing
```bash
make format          # Format code
make check           # Run all checks
git add .
git commit -m "..."  # Pre-commit hooks run automatically
```

### Manual Pre-commit
```bash
pre-commit run --all-files
```

### Skip Hooks (Emergency Only)
```bash
git commit --no-verify
```

## Testing

### Run Tests
```bash
make test            # Basic test run
make test-cov        # With coverage report
pytest -v            # Verbose output
pytest tests/config/ # Specific directory
```

### Coverage Report
```bash
make test-cov
open htmlcov/index.html  # View HTML report
```

## Troubleshooting

### Import Errors
```bash
poetry shell         # Activate environment
# or
poetry run python your_script.py
```

### Dependency Issues
```bash
poetry lock --no-update
poetry install
```

### Type Check Errors
```bash
mypy . --show-error-codes  # See detailed errors
```

### Pre-commit Failures
```bash
pre-commit run --all-files  # See what failed
make format                 # Fix formatting
make lint                   # Fix linting
```

## Documentation

- `README.md` - Project overview and usage
- `SETUP_GUIDE.md` - Detailed setup and development guide
- `MIGRATION_SUMMARY.md` - Dependency management migration
- `IMPROVEMENTS.md` - All improvements made
- `QUICK_REFERENCE.md` - This file

## Resources

- [Poetry Docs](https://python-poetry.org/docs/)
- [Ruff Docs](https://docs.astral.sh/ruff/)
- [MyPy Docs](https://mypy.readthedocs.io/)
- [LangChain Docs](https://python.langchain.com/)
- [ChromaDB Docs](https://docs.trychroma.com/)
