# ShowDoc JSON Persistence Example

## Overview

When anime data is fetched from AniDB via the MCP server, it's persisted to JSON files in the `data/mcp_cache/` directory. This allows for vector store rebuilding without re-fetching from the API.

## Directory Structure

```
data/mcp_cache/
├── index.json              # Master index of all cached anime
├── 18290.json             # Dan Da Dan (Season 1)
├── 19060.json             # Dan Da Dan (Season 2)
├── 22.json                # Neon Genesis Evangelion
└── 17550.json             # Kaiju No. 8
```

## Index File Format

**File**: `data/mcp_cache/index.json`

```json
{
  "version": "1.0",
  "created": "2024-11-10T15:30:00.000000",
  "anime": {
    "18290": {
      "title": "Dan Da Dan",
      "anime_id": "18290",
      "file": "18290.json",
      "updated": "2024-11-10T15:30:00.000000"
    },
    "19060": {
      "title": "Dan Da Dan (2025)",
      "anime_id": "19060",
      "file": "19060.json",
      "updated": "2024-11-10T15:35:00.000000"
    },
    "22": {
      "title": "Shinseiki Evangelion",
      "anime_id": "22",
      "file": "22.json",
      "updated": "2024-11-10T15:40:00.000000"
    }
  }
}
```

## Individual Anime File Format

**File**: `data/mcp_cache/18290.json`

```json
{
  "anime_id": "18290",
  "anidb_anime_id": 18290,
  "title_main": "Dan Da Dan",
  "title_alts": [
    "ダンダダン",
    "Dandadan"
  ],
  "description": "Based on a paranormal mystery battle & romantic comedy manga by Tatsu Yukinobu. High schooler Momo Ayase and her occult-obsessed classmate Okarun find themselves caught up in supernatural events involving aliens and yokai.",
  "tags": [
    "action",
    "comedy",
    "paranormal",
    "romance",
    "supernatural"
  ],
  "episode_count_normal": 12,
  "episode_count_special": 0,
  "air_date": "2024-10-04T00:00:00",
  "end_date": "2024-12-20T00:00:00",
  "begin_year": 2024,
  "end_year": 2024,
  "rating": 845,
  "vote_count": 1250,
  "avg_review_rating": 0,
  "review_count": 0,
  "ann_id": 26176,
  "crunchyroll_id": "GG5H5XQ7D",
  "wikipedia_id": "Dan_Da_Dan",
  "relations": "[{\"id\": \"19060\", \"type\": \"Sequel\", \"title\": \"Dan Da Dan (2025)\"}]",
  "similar": "[{\"id\": \"14662\", \"approval\": \"1\", \"total\": \"4\", \"title\": \"Katsute Kami Datta Kemono-tachi e\"}]",
  "_metadata": {
    "fetched_at": "2024-11-10T15:30:00.000000",
    "source": "mcp_anidb"
  }
}
```

## Field Descriptions

### Core Fields

| Field | Type | Description |
|-------|------|-------------|
| `anime_id` | string | Unique Shoko anime identifier |
| `anidb_anime_id` | integer | AniDB anime identifier (used as filename) |
| `title_main` | string | Primary title of the anime |
| `title_alts` | array | List of alternate titles and aliases |
| `description` | string | Full description/synopsis |
| `tags` | array | List of genre tags |

### Episode Information

| Field | Type | Description |
|-------|------|-------------|
| `episode_count_normal` | integer | Number of regular episodes |
| `episode_count_special` | integer | Number of special episodes |

### Date Information

| Field | Type | Description |
|-------|------|-------------|
| `air_date` | string (ISO 8601) | Initial air date |
| `end_date` | string (ISO 8601) | Final air date |
| `begin_year` | integer | Year began airing |
| `end_year` | integer | Year finished airing |

### Rating Information

| Field | Type | Description |
|-------|------|-------------|
| `rating` | integer | AniDB rating (0-1000 scale) |
| `vote_count` | integer | Number of votes |
| `avg_review_rating` | integer | Average review rating |
| `review_count` | integer | Number of reviews |

### External IDs

| Field | Type | Description |
|-------|------|-------------|
| `ann_id` | integer | Anime News Network ID |
| `crunchyroll_id` | string | Crunchyroll series ID |
| `wikipedia_id` | string | Wikipedia page identifier |

### Relationships

| Field | Type | Description |
|-------|------|-------------|
| `relations` | string (JSON) | Related anime (sequels, prequels, etc.) |
| `similar` | string (JSON) | Similar anime recommendations |

### Metadata

| Field | Type | Description |
|-------|------|-------------|
| `_metadata.fetched_at` | string (ISO 8601) | When the data was fetched |
| `_metadata.source` | string | Data source (always "mcp_anidb") |

## Usage Examples

### Loading a Single Anime

```python
from services.showdoc_persistence import ShowDocPersistence

persistence = ShowDocPersistence()

# Load Dan Da Dan
show_doc = persistence.load_showdoc(18290)
print(f"Title: {show_doc.title_main}")
print(f"Episodes: {show_doc.episode_count_normal}")
```

### Loading All Cached Anime

```python
from services.showdoc_persistence import ShowDocPersistence

persistence = ShowDocPersistence()

# Get all cached anime
all_anime = persistence.get_all_showdocs()
print(f"Total cached: {len(all_anime)}")

for anime in all_anime:
    print(f"- {anime.title_main} ({anime.anidb_anime_id})")
```

### Checking Cache Statistics

```python
from services.showdoc_persistence import ShowDocPersistence

persistence = ShowDocPersistence()

stats = persistence.get_stats()
print(f"Total anime: {stats['total_anime']}")
print(f"Storage dir: {stats['storage_dir']}")
print(f"Created: {stats['created']}")
```

### Rebuilding Vector Store

```bash
# Rebuild from MCP cache using the ingest command
poetry run python -m cli ingest --source=mcp-cache

# Clear existing vector store first
poetry run python -m cli ingest --source=mcp-cache --clear-existing

# Use custom batch size
poetry run python -m cli ingest --source=mcp-cache --batch-size 50

# Use custom cache directory
poetry run python -m cli ingest --source=mcp-cache --cache-dir data/custom_cache
```

## Benefits

1. **Disaster Recovery**: Rebuild vector store if corrupted
2. **Migration**: Move to new vector store without re-fetching
3. **Development**: Work offline with cached data
4. **Audit Trail**: Track when each anime was fetched
5. **Version Control**: Can commit to git for team sharing
6. **Cost Savings**: Avoid redundant API calls

## Maintenance

### Updating Cached Data

To update an anime's data:

```python
from services.mcp_client_service import create_mcp_client
from services.anidb_parser import parse_anidb_xml
from services.showdoc_persistence import ShowDocPersistence

async def update_anime(aid: int):
    persistence = ShowDocPersistence()
    
    async with await create_mcp_client() as mcp:
        xml_data = await mcp.get_anime_details(aid)
        show_doc = parse_anidb_xml(xml_data)
        persistence.save_showdoc(show_doc)  # Overwrites existing
```

### Cleaning Old Cache

```python
from pathlib import Path
import json
from datetime import datetime, timedelta

def clean_old_cache(days: int = 90):
    """Remove anime not updated in X days."""
    cache_dir = Path("data/mcp_cache")
    index_file = cache_dir / "index.json"
    
    with index_file.open() as f:
        index = json.load(f)
    
    cutoff = datetime.now() - timedelta(days=days)
    
    for aid, info in list(index["anime"].items()):
        updated = datetime.fromisoformat(info["updated"])
        if updated < cutoff:
            # Remove file and index entry
            (cache_dir / info["file"]).unlink(missing_ok=True)
            del index["anime"][aid]
    
    # Save updated index
    with index_file.open("w") as f:
        json.dump(index, f, indent=2)
```

## Integration with Existing Workflow

The persistence layer integrates seamlessly:

1. **User queries** → RAG service
2. **Vector store miss** → MCP fallback triggered
3. **MCP fetches** → JSON parsed to ShowDoc
4. **ShowDoc saved** → JSON file in cache
5. **ShowDoc cached** → Vector store for immediate use
6. **Future queries** → Hit vector store cache
7. **Vector store rebuild** → Load from JSON cache

This ensures data is never lost and can always be recovered.
