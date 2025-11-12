# ShokoBot Examples

This directory contains example scripts demonstrating various features of ShokoBot.

## Prerequisites

All examples require:

1. **OpenAI API Key**:
   ```bash
   export OPENAI_API_KEY="your-api-key-here"
   ```

2. **Initialized Vector Store**:
   ```bash
   python -m cli.ingest --source json --file data/anime.json
   ```

3. **Configuration**: Ensure `resources/config.json` is properly set up

## Available Examples

### 1. Simple Similarity Scores (`simple_similarity_scores.py`)

**Purpose**: Quick way to view similarity scores for a search query.

**Usage**:
```bash
python examples/simple_similarity_scores.py "your search query"
```

**Examples**:
```bash
python examples/simple_similarity_scores.py "action anime"
python examples/simple_similarity_scores.py "Evangelion"
python examples/simple_similarity_scores.py "mecha robots"
```

**Output**: Displays top 5 results with similarity scores and statistics.

---

### 2. View Similarity Scores (`view_similarity_scores.py`)

**Purpose**: Comprehensive demonstration of different ways to view and analyze similarity scores.

**Usage**:
```bash
python examples/view_similarity_scores.py
```

**Features**:
- Basic score viewing
- Filtering by threshold
- Comparing multiple queries
- MCP fallback analysis

**Output**: Runs 4 different examples showing various techniques.

---

## Common Issues

### "The api_key client option must be set"

Set your OpenAI API key:
```bash
export OPENAI_API_KEY="your-api-key-here"
```

### "Config file not found"

Run from the project root directory where `resources/config.json` exists.

### "No results found"

Your vector store may be empty. Run the ingest command:
```bash
python -m cli.ingest --source json --file data/anime.json
```

## See Also

- [Viewing Similarity Scores Guide](../docs/viewing_similarity_scores.md) - Comprehensive documentation
- [Similarity Utilities](../utils/similarity_utils.py) - Utility functions for working with scores
- [RAG Service](../services/rag_service.py) - RAG service implementation with MCP fallback
