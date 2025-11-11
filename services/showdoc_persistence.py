"""Persistence layer for ShowDoc objects fetched from MCP."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from models.show_doc import ShowDoc

logger = logging.getLogger(__name__)


class ShowDocPersistence:
    """Handles persistence of ShowDoc objects to JSON files.

    Stores fetched anime data in a structured JSON format that can be
    used to rebuild the vector store without re-fetching from AniDB.
    """

    def __init__(self, storage_dir: str = "data/mcp_cache") -> None:
        """Initialize persistence layer.

        Args:
            storage_dir: Directory to store JSON files.
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.storage_dir / "index.json"
        self._load_index()

    def _load_index(self) -> None:
        """Load or create the index file."""
        if self.index_file.exists():
            with self.index_file.open() as f:
                self.index = json.load(f)
        else:
            self.index = {
                "version": "1.0",
                "created": datetime.now().isoformat(),
                "anime": {},
            }
            self._save_index()

    def _save_index(self) -> None:
        """Save the index file."""
        with self.index_file.open("w") as f:
            json.dump(self.index, f, indent=2)

    def save_showdoc(self, show_doc: ShowDoc) -> None:
        """Save ShowDoc to JSON file.

        Args:
            show_doc: ShowDoc instance to persist.
        """
        # Create filename from anime_id
        filename = f"{show_doc.anidb_anime_id}.json"
        filepath = self.storage_dir / filename

        # Convert ShowDoc to dict
        data = show_doc.model_dump(mode="json")

        # Add metadata
        data["_metadata"] = {
            "fetched_at": datetime.now().isoformat(),
            "source": "mcp_anidb",
        }

        # Save to file
        with filepath.open("w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        # Update index
        self.index["anime"][str(show_doc.anidb_anime_id)] = {
            "title": show_doc.title_main,
            "anime_id": show_doc.anime_id,
            "file": filename,
            "updated": datetime.now().isoformat(),
        }
        self._save_index()

        logger.info(f"Saved ShowDoc to {filepath}")

    def load_showdoc(self, anidb_anime_id: int) -> ShowDoc | None:
        """Load ShowDoc from JSON file.

        Args:
            anidb_anime_id: AniDB anime ID.

        Returns:
            ShowDoc instance or None if not found.
        """
        anime_key = str(anidb_anime_id)
        if anime_key not in self.index["anime"]:
            return None

        filename = self.index["anime"][anime_key]["file"]
        filepath = self.storage_dir / filename

        if not filepath.exists():
            logger.warning(f"Index references missing file: {filepath}")
            return None

        with filepath.open() as f:
            data = json.load(f)

        # Remove metadata before creating ShowDoc
        data.pop("_metadata", None)

        # Convert ISO date strings back to datetime
        if data.get("air_date"):
            data["air_date"] = datetime.fromisoformat(data["air_date"])
        if data.get("end_date"):
            data["end_date"] = datetime.fromisoformat(data["end_date"])

        return ShowDoc(**data)

    def exists(self, anidb_anime_id: int) -> bool:
        """Check if ShowDoc exists in storage.

        Args:
            anidb_anime_id: AniDB anime ID.

        Returns:
            True if ShowDoc is stored.
        """
        return str(anidb_anime_id) in self.index["anime"]

    def get_all_showdocs(self) -> list[ShowDoc]:
        """Load all stored ShowDocs.

        Returns:
            List of all ShowDoc instances.
        """
        showdocs = []
        for anidb_id in self.index["anime"].keys():
            show_doc = self.load_showdoc(int(anidb_id))
            if show_doc:
                showdocs.append(show_doc)
        return showdocs

    def get_stats(self) -> dict[str, Any]:
        """Get statistics about stored data.

        Returns:
            Dictionary with storage statistics.
        """
        return {
            "total_anime": len(self.index["anime"]),
            "storage_dir": str(self.storage_dir),
            "index_file": str(self.index_file),
            "created": self.index.get("created"),
            "version": self.index.get("version"),
        }
