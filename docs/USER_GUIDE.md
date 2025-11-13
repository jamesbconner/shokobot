# ShokoBot User Guide

Complete guide to using ShokoBot for anime queries and recommendations.

## Quick Start

```bash
# Set your OpenAI API key
export OPENAI_API_KEY="your-api-key"

# Query mode
poetry run shokobot query -q "What is Cowboy Bebop about?"

# Interactive mode with context display
poetry run shokobot repl --show-context

# Adjust number of results
poetry run shokobot query -q "Tell me about Gundam" --k 15 --show-context
```

## CLI Commands

### Query Command

Single or batch queries with various input modes.

```bash
poetry run shokobot query [OPTIONS]
```

**Options:**
- `-q, --question TEXT` - Single question to ask
- `-f, --file PATH` - File with questions (one per line)
- `--stdin` - Read questions from stdin
- `-i, --interactive` - Start interactive REPL mode
- `-c, --show-context` - Display retrieved context documents with similarity scores
- `--k INTEGER` - Number of documents to retrieve [default: 10]
- `--output-format [text|json]` - Output format [default: text]

**Examples:**

```bash
# Single question
poetry run shokobot query -q "What is Cowboy Bebop about?"

# With context display
poetry run shokobot query -q "Tell me about mecha anime" --show-context

# Retrieve more results
poetry run shokobot query -q "Tell me about Gundam" --k 20 --show-context

# JSON output
poetry run shokobot query -q "Cowboy Bebop" --output-format json

# Batch from file
poetry run shokobot query -f questions.txt --show-context

# From stdin
echo "What is Trigun about?" | poetry run shokobot query --stdin
```

### REPL Command

Interactive mode for multiple queries in one session.

```bash
poetry run shokobot repl [OPTIONS]
```

**Options:**
- `-c, --show-context` - Display retrieved context documents
- `--k INTEGER` - Number of documents to retrieve [default: 10]
- `--output-format [text|json]` - Output format [default: text]

**Example:**

```bash
poetry run shokobot repl --show-context --k 15

> What is Cowboy Bebop about?
[Answer with context table]

> Tell me about mecha anime
[Answer with context table]

> exit
```

## Context Display with Similarity Scores

When using `--show-context`, you'll see a table with similarity scores:

```
                            Retrieved Context                             
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━┓
┃ Title                          ┃ ID       ┃ Year     ┃ Episodes ┃ Similarity ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━┩
│ Cowboy Bebop                   │ 1        │ 1998     │ 26       │ 0.277      │
│ Cowboy Bebop: Tengoku no Tobira│ 5        │ 2001     │ 1        │ 0.368      │
│ Trigun                         │ 11       │ 1998     │ 26       │ 0.488      │
└────────────────────────────────┴──────────┴──────────┴──────────┴────────────┘
```

### Understanding Similarity Scores

**Color Coding:**
- 🟢 **Green (0.0-0.3)**: Excellent match - very close semantic similarity
- 🔵 **Blue (0.3-0.6)**: Very good match - close semantic similarity
- 🟡 **Yellow (0.6-0.9)**: Good match - moderate semantic similarity
- 🔴 **Red (0.9+)**: Moderate/poor match - low semantic similarity
- 🟢 **Green "MCP"**: Result from external AniDB source (perfect match)

**Key Point**: Lower scores = better matches! These are distance scores, not similarity scores.

### What is MCP?

When your local vector store doesn't have good results, ShokoBot automatically fetches data from AniDB via the MCP (Model Context Protocol) server. These results show as "MCP" in the similarity column.

**MCP Fallback Triggers When:**
- Best similarity score > 0.5 (poor match), OR
- Fewer than 3 results found

**Benefits:**
- ✅ Automatic data enrichment
- ✅ Always get relevant results
- ✅ Cached for future queries
- ✅ Transparent (shows "MCP" indicator)

## Understanding Distance Scores

ShokoBot uses **distance scores** (not similarity scores) from ChromaDB:

- **0.0-0.3**: Excellent match (very close vectors)
- **0.3-0.6**: Very good match (close vectors)
- **0.6-0.9**: Good match (moderately close vectors)
- **0.9-1.2**: Moderate match (somewhat distant vectors)
- **1.2+**: Poor match (distant vectors)

**Remember**: Lower = Better (opposite of similarity scores!)

## Query Tips

### Natural Language Queries

ShokoBot uses intelligent title extraction, so you can ask naturally:

```bash
# All of these work:
"Tell me about Cowboy Bebop"
"What is Cowboy Bebop about?"
"I want to know more about the anime Cowboy Bebop"
"Tell me about the anime called 'Cowboy Bebop'"
"That space cowboy show"  # LLM will extract the title
```

### Getting Better Results

**1. Be specific:**
```bash
# ✅ Good
"Tell me about Neon Genesis Evangelion"

# ❌ Too vague
"Tell me about mecha anime"
```

**2. Use exact titles when possible:**
```bash
# ✅ Best
"Cowboy Bebop"

# ✅ Also good
"Tell me about Cowboy Bebop"
```

**3. Adjust k for more results:**
```bash
# Get more Gundam shows
poetry run shokobot query -q "Gundam" --k 20 --show-context
```

**4. Check similarity scores:**
- If all scores are > 0.9 (red), try a more specific query
- If you see "MCP" results, the data was fetched from AniDB

## Configuration

### Setting Your API Key

```bash
# Temporary (current session)
export OPENAI_API_KEY="your-api-key"

# Permanent (add to ~/.zshrc or ~/.bashrc)
echo 'export OPENAI_API_KEY="your-api-key"' >> ~/.zshrc
```

### Adjusting MCP Thresholds

Edit `resources/config.json`:

```json
{
  "mcp": {
    "enabled": true,
    "fallback_score_threshold": 0.5,
    "fallback_count_threshold": 3
  }
}
```

- **fallback_score_threshold**: Maximum distance for "good" results (lower = stricter)
- **fallback_count_threshold**: Minimum number of results required

**How it works:**
- MCP is **skipped** if: `best_distance <= 0.5 AND count >= 3`
- MCP is **triggered** if: `best_distance > 0.5 OR count < 3`

### Adjusting Model Settings

Edit `resources/config.json`:

```json
{
  "openai": {
    "model": "gpt-5-nano",
    "embedding_model": "text-embedding-3-small"
  },
  "responses_api": {
    "reasoning_effort": "medium",
    "output_verbosity": "medium",
    "max_output_tokens": 1000
  }
}
```

## Output Formats

### Text Format (Default)

Human-readable output with rich formatting:

```bash
poetry run shokobot query -q "Cowboy Bebop"
```

```
Q: Cowboy Bebop

A: Cowboy Bebop is a space western anime series that follows...
```

### JSON Format

Machine-readable output for scripting:

```bash
poetry run shokobot query -q "Cowboy Bebop" --output-format json
```

```json
{
  "question": "Cowboy Bebop",
  "answer": "Cowboy Bebop is a space western anime series...",
  "context": [
    {
      "title": "Cowboy Bebop",
      "anime_id": 1,
      "year": 1998,
      "episodes": 26
    }
  ]
}
```

## Troubleshooting

### No Results Found

**Problem**: Query returns no results or very poor matches

**Solutions:**
1. Check your vector store has data: `poetry run shokobot info`
2. Try a more specific query
3. Lower the MCP threshold to trigger fallback more easily
4. Check if MCP is enabled in config

### MCP Always Triggers

**Problem**: Every query shows "MCP" results

**Solutions:**
1. Your vector store might be empty - run ingest
2. MCP thresholds might be too strict - increase `fallback_score_threshold`
3. Check your queries match your data

### High Similarity Scores (Red)

**Problem**: Most scores are > 0.9 (red/poor matches)

**Solutions:**
1. Try more specific or descriptive queries
2. Verify your vector store has relevant data
3. Check embedding quality
4. Consider adjusting MCP thresholds

### API Key Errors

**Problem**: "The api_key client option must be set"

**Solution:**
```bash
export OPENAI_API_KEY="your-api-key"
```

### Config File Not Found

**Problem**: "Config file not found"

**Solution**: Run from the project root directory where `resources/config.json` exists.

## Advanced Usage

### Batch Processing

Process multiple questions from a file:

```bash
# Create questions file
cat > questions.txt << EOF
What is Cowboy Bebop about?
Tell me about mecha anime
What are the best space opera anime?
EOF

# Process batch
poetry run shokobot query -f questions.txt --show-context
```

### Piping and Scripting

```bash
# Pipe from another command
cat anime_list.txt | poetry run shokobot query --stdin

# Use in scripts
for anime in "Cowboy Bebop" "Trigun" "Outlaw Star"; do
    poetry run shokobot query -q "Tell me about $anime" --output-format json
done
```

### Filtering by Metadata

The vector store supports metadata filtering (advanced):

```python
from services.app_context import AppContext

ctx = AppContext.create()
vs = ctx.vectorstore

# Only anime from 2020+
results = vs.similarity_search(
    "romance anime",
    k=10,
    where={"begin_year": {"$gte": 2020}}
)
```

## See Also

- [MCP Integration Guide](MCP_INTEGRATION.md) - MCP server setup and configuration
- [CLI Architecture](MODULAR_CLI_ARCHITECTURE.md) - CLI design and patterns
- [AppContext Usage](APPCONTEXT_USAGE.md) - Dependency injection guide
- [Testing Strategy](TESTING_STRATEGY.md) - Testing approach and best practices
- [Debug Scripts](../debug/README.md) - Debugging tools and utilities
