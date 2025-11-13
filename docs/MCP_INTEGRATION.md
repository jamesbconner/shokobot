# MCP Integration Guide

Complete guide to Model Context Protocol (MCP) integration for anime data fallback.

## Overview

The MCP integration provides automatic fallback to AniDB when the vector store doesn't have sufficient or high-quality results. This ensures comprehensive coverage while maintaining fast local queries.

**Key Features:**
- Automatic fallback based on configurable thresholds
- Smart title extraction (regex + LLM hybrid)
- Persistent caching of fetched data
- Transparent source indicators in results

## Installation

### Prerequisites

1. **mcp-server-anime** - Clone and set up the MCP server:

```bash
# Clone the MCP server repository
git clone https://github.com/jamesbconner/mcp-server-anime.git
cd mcp-server-anime

# Create virtual environment and install
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e .
```

2. **Verify installation**:

```bash
# Test the server starts
python -m mcp_server_anime.server
```

## Configuration

### MCP Settings

Configure MCP in `resources/config.json`:

```json
{
  "mcp": {
    "enabled": true,
    "cache_dir": "data/mcp_cache",
    "fallback_count_threshold": 3,
    "fallback_score_threshold": 0.5,
    "timeout": 30,
    "servers": {
      "anime": {
        "command": "/path/to/mcp-server-anime/.venv/bin/python",
        "args": ["-m", "mcp_server_anime.server"],
        "cwd": "/path/to/mcp-server-anime",
        "env": {
          "PYTHONPATH": "/path/to/mcp-server-anime/src"
        }
      }
    }
  }
}
```

**Note**: Update the paths to match your local mcp-server-anime installation.

### Configuration Options

| Option | Default | Description |
|--------|---------|-------------|
| `enabled` | `true` | Master switch for MCP integration |
| `cache_dir` | `"data/mcp_cache"` | Directory for caching responses |
| `fallback_count_threshold` | `3` | Minimum results required to skip MCP |
| `fallback_score_threshold` | `0.5` | Maximum distance for "good" results |
| `timeout` | `30` | Timeout in seconds for MCP operations |
| `servers.anime.command` | (required) | Path to Python executable in MCP server venv |
| `servers.anime.args` | `["-m", "mcp_server_anime.server"]` | Arguments to run the MCP server |
| `servers.anime.cwd` | (required) | Working directory for MCP server |
| `servers.anime.env.PYTHONPATH` | (required) | Python path to MCP server source directory |
| `servers.anime.env.PYTHONPATH` | (required) | Python path to MCP server source |

### Fallback Logic

MCP fallback triggers when **EITHER** condition is true:
1. **Insufficient results**: `count < fallback_count_threshold`
2. **Poor quality**: `best_distance > fallback_score_threshold`

**Examples:**

```
✅ Skip MCP: 5 results, best distance 0.28
   (count >= 3 AND distance <= 0.5)

❌ Trigger MCP: 5 results, best distance 1.15
   (distance > 0.5)

❌ Trigger MCP: 2 results, best distance 0.35
   (count < 3)
```

### Threshold Tuning

**Strict Quality (prefer MCP):**
```json
{
  "fallback_count_threshold": 5,
  "fallback_score_threshold": 0.3
}
```

**Performance (prefer vector store):**
```json
{
  "fallback_count_threshold": 2,
  "fallback_score_threshold": 0.9
}
```

**Balanced (default):**
```json
{
  "fallback_count_threshold": 3,
  "fallback_score_threshold": 0.5
}
```

## Title Extraction

The system uses a hybrid approach to extract anime titles from natural language queries.

### Regex Patterns (Fast, Free)

Tries these patterns first:

| Pattern | Example | Extracted |
|---------|---------|-----------|
| "Tell me about X" | "Tell me about Cowboy Bebop" | "cowboy bebop" |
| "What is X about?" | "What is Voltron about?" | "voltron" |
| "Search for X" | "Search for Trigun" | "trigun" |
| "Anime called X" | "Anime called 'Full Metal Alchemist'" | "full metal alchemist" |
| Direct title | "Steins;Gate" | "Steins;Gate" |

### LLM Fallback (Flexible, Small Cost)

If regex fails, uses GPT-5 to extract the title:
- Handles any creative query pattern
- Uses low reasoning effort for speed
- Cost: ~$0.0001 per extraction
- Most queries use regex (free)

**Examples handled by LLM:**
- "I'm looking for that space cowboy show" → "Cowboy Bebop"
- "What's the anime with the giant robots?" → extracts relevant title
- "That show about time travel and microwaves" → "Steins;Gate"

## Usage

### Automatic Fallback

MCP works automatically during queries:

```bash
# May trigger MCP if "Voltron" isn't in vector store
poetry run shokobot query -q "Tell me about Voltron"
```

### Viewing MCP Results

MCP results show as "MCP" in the similarity column:

```bash
poetry run shokobot query -q "Tell me about Voltron" --show-context
```

**Output:**
```
┌─────────────────────────────────┬──────────────┐
│ Title                           │ Similarity   │
├─────────────────────────────────┼──────────────┤
│ Voltron                         │ MCP          │  ← From AniDB
│ Some Similar Anime              │ 0.456        │  ← From vector store
└─────────────────────────────────┴──────────────┘
```

## Monitoring

Enable debug logging to see MCP behavior:

```json
{
  "logging": {
    "level": "DEBUG"
  }
}
```

**Log messages:**

```
DEBUG - Vector store returned 5 results, best score: 0.280
DEBUG - Both thresholds met, returning vector store results
```

Or:

```
DEBUG - Vector store returned 2 results, best score: 1.150
DEBUG - Triggering MCP fallback: insufficient results or poor quality
INFO - Searching MCP for anime title: 'voltron'
INFO - Fetched anime from MCP: Voltron (123)
```

## Troubleshooting

### MCP Never Triggers

**Solutions:**
1. Check `enabled: true` in config
2. Lower `fallback_score_threshold` (e.g., to 0.3)
3. Increase `fallback_count_threshold` (e.g., to 5)
4. Enable DEBUG logging

### MCP Always Triggers

**Solutions:**
1. Increase `fallback_score_threshold` (e.g., to 0.9)
2. Decrease `fallback_count_threshold` (e.g., to 2)
3. Check vector store has data: `poetry run shokobot info`
4. Verify queries match your data

### Connection Errors

**Error:** `Connection closed`

**Solutions:**
1. Check MCP server installed: `uvx --help`
2. Test server: `uvx mcp-server-anime`
3. Check server logs for errors

### Title Extraction Issues

**Problem:** Wrong anime returned

**Solutions:**
1. Use more specific queries
2. Include year: "Voltron 1984"
3. Use official title

## Performance

- **Regex extraction**: ~0ms, $0
- **LLM extraction**: ~200ms, ~$0.0001
- **MCP search**: ~500ms, $0
- **MCP details**: ~1000ms, $0

Most queries use regex (fast), only unusual patterns trigger LLM.

## Related Files

- `services/mcp_client_service.py` - MCP client implementation
- `services/mcp_anime_json_parser.py` - JSON response parser
- `services/rag_service.py` - Fallback logic
- `prompts/title_extraction.py` - LLM extraction prompt
- `debug/debug_mcp_connection.py` - Connection testing

## See Also

- [User Guide](USER_GUIDE.md) - Complete usage guide
- [ShowDoc JSON Format](SHOWDOC_JSON_EXAMPLE.md) - Data format reference
