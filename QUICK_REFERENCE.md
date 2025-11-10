# ShokoBot Quick Reference

Quick command reference for daily use. See [README.md](README.md) for full documentation.

## Quick Start

```bash
# Setup
./setup.sh
export OPENAI_API_KEY='your-key-here'

# Verify
poetry run shokobot info

# Ingest
poetry run shokobot ingest

# Query
poetry run shokobot repl
```

## CLI Commands

### info - View Configuration
```bash
poetry run shokobot info
```

### ingest - Load Data
```bash
# Default settings
poetry run shokobot ingest

# Custom options
poetry run shokobot ingest -i custom.json -b 200 --id-field AniDB_AnimeID
```

**Options:**
- `-i, --input PATH` - Custom JSON file
- `-b, --batch-size INTEGER` - Batch size (default: 100)
- `--id-field [AnimeID|AniDB_AnimeID]` - Primary ID field

### query - Ask Questions
```bash
# Single question
poetry run shokobot query -q "What anime are similar to Cowboy Bebop?"

# With context
poetry run shokobot query -q "Best mecha anime?" -c

# From file
poetry run shokobot query -f questions.txt

# From stdin
echo "What is Steins;Gate about?" | poetry run shokobot query --stdin

# Interactive mode
poetry run shokobot query -i
```

**Options:**
- `-q, --question TEXT` - Single question
- `-f, --file PATH` - Read from file
- `--stdin` - Read from stdin
- `-i, --interactive` - Interactive mode
- `-c, --show-context` - Show retrieved docs
- `--k INTEGER` - Number of docs (default: 10)

### repl - Interactive Mode (Recommended)
```bash
# Start REPL
poetry run shokobot repl

# With context display
poetry run shokobot repl -c

# Custom retrieval count
poetry run shokobot repl --k 15
```

**Options:**
- `-c, --show-context` - Show retrieved docs
- `--k INTEGER` - Number of docs

**REPL Commands:**
- Type question and press Enter
- `exit`, `quit`, or `q` to leave

## Configuration

### Environment Variables

```bash
# Required
OPENAI_API_KEY='your-key-here'

# Optional overrides (pattern: SECTION_KEY)
CHROMA_PERSIST_DIRECTORY='./.chroma'
CHROMA_COLLECTION_NAME='tvshows'
OPENAI_MODEL='gpt-5-nano'
OPENAI_REASONING_EFFORT='medium'    # low/medium/high
OPENAI_OUTPUT_VERBOSITY='medium'    # low/medium/high
OPENAI_MAX_OUTPUT_TOKENS='8192'
INGEST_BATCH_SIZE='100'
LOGGING_LEVEL='INFO'
```

### Config File Location

`resources/config.json` - Edit for persistent settings

## Common Workflows

### First Time Setup
```bash
./setup.sh
# Edit .env with your OPENAI_API_KEY
poetry run shokobot info
poetry run shokobot ingest
poetry run shokobot repl
```

### Daily Usage
```bash
# Quick question
poetry run shokobot query -q "recommend sci-fi anime"

# Multiple questions
poetry run shokobot repl
```

### Batch Processing
```bash
# Create questions file
cat > questions.txt << EOF
What is Cowboy Bebop about?
What are some good mecha anime?
Recommend romance anime from 2010s
EOF

# Process all questions
poetry run shokobot query -f questions.txt -c
```

### Custom Data Ingestion
```bash
# Use custom data file
poetry run shokobot ingest -i /path/to/anime.json -b 200

# Use different ID field
poetry run shokobot ingest --id-field AniDB_AnimeID
```

## Using with uv

Replace `poetry run` with `uv run`:

```bash
uv run shokobot info
uv run shokobot ingest
uv run shokobot repl
uv run shokobot query -q "..."
```

## Troubleshooting

### API Key Issues
```bash
# Check if set
echo $OPENAI_API_KEY

# Set temporarily
export OPENAI_API_KEY='your-key-here'

# Set permanently (add to .env)
echo "OPENAI_API_KEY='your-key-here'" >> .env
```

### ChromaDB Issues
```bash
# Reset database
rm -rf ./.chroma
poetry run shokobot ingest
```

### Import/Module Errors
```bash
# Reinstall dependencies
poetry install

# Verify installation
poetry run shokobot --help

# Or activate shell
poetry shell
shokobot --help
```

### Configuration Check
```bash
# View current settings
poetry run shokobot info

# Test with single query
poetry run shokobot query -q "test" -c
```

## Tips & Best Practices

### Performance
- Use `repl` for multiple queries (faster, cached)
- Adjust `--k` for more/fewer context documents
- Increase batch size on powerful machines
- Use env vars for quick config changes

### Querying
- Be specific: "romance anime with strong female leads"
- Try different phrasings if unsatisfied
- Use `-c` to see what context was retrieved
- REPL mode is fastest for multiple questions

### Data Quality
- Validate JSON before ingesting
- Check logs for validation errors
- Use `--id-field` if needed

### Development
- Run `shokobot info` to verify config
- Use `--show-context` to debug retrieval
- Check `docs/` for architecture details

## Command Cheat Sheet

```bash
# View config
poetry run shokobot info

# Ingest data
poetry run shokobot ingest

# Quick question
poetry run shokobot query -q "..."

# Interactive (best for multiple questions)
poetry run shokobot repl

# Show context
poetry run shokobot query -q "..." -c
poetry run shokobot repl -c

# Batch from file
poetry run shokobot query -f questions.txt

# Custom ingestion
poetry run shokobot ingest -i file.json -b 200

# Check version
poetry run shokobot --version

# Get help
poetry run shokobot --help
poetry run shokobot query --help
```

## Statistics

- **Anime Records**: 1,458
- **Fields per Record**: 21
- **Ingestion Time**: ~40-50 seconds
- **Query Response**: ~3-6 seconds
- **Default Batch Size**: 100
- **Default Context Docs**: 10

## Documentation

- [README.md](README.md) - Full documentation
- [SETUP_GUIDE.md](SETUP_GUIDE.md) - Detailed setup
- [docs/](docs/) - Architecture documentation

## Resources

- [OpenAI API Docs](https://platform.openai.com/docs/)
- [LangChain Docs](https://python.langchain.com/)
- [ChromaDB Docs](https://docs.trychroma.com/)
- [Poetry Docs](https://python-poetry.org/docs/)
