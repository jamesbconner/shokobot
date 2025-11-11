"""Tests for ShowDoc persistence service."""

import json
from datetime import datetime
from pathlib import Path

import pytest

from models.show_doc import ShowDoc
from services.showdoc_persistence import ShowDocPersistence


@pytest.fixture
def sample_showdoc() -> ShowDoc:
    """Create a sample ShowDoc for testing."""
    return ShowDoc(
        anime_id="12345",
        anidb_anime_id=12345,
        title_main="Test Anime",
        title_alts=["テストアニメ", "Test"],
        description="A test anime description",
        tags=["action", "comedy"],
        episode_count_normal=24,
        episode_count_special=2,
        air_date=datetime(2020, 1, 15),
        end_date=datetime(2020, 6, 30),
        begin_year=2020,
        end_year=2020,
        rating=850,
        vote_count=1000,
    )


class TestShowDocPersistence:
    """Tests for ShowDocPersistence class."""

    def test_init_creates_directory(self, tmp_path: Path) -> None:
        """Test that initialization creates storage directory."""
        # Arrange
        cache_dir = tmp_path / "test_cache"

        # Act
        persistence = ShowDocPersistence(storage_dir=str(cache_dir))

        # Assert
        assert cache_dir.exists()
        assert cache_dir.is_dir()
        assert persistence.index_file.exists()

    def test_init_creates_index_file(self, tmp_path: Path) -> None:
        """Test that initialization creates index file with correct structure."""
        # Arrange
        cache_dir = tmp_path / "test_cache"

        # Act
        persistence = ShowDocPersistence(storage_dir=str(cache_dir))

        # Assert
        assert persistence.index_file.exists()
        with persistence.index_file.open() as f:
            index = json.load(f)
        assert index["version"] == "1.0"
        assert "created" in index
        assert index["anime"] == {}

    def test_save_showdoc_creates_json_file(
        self, tmp_path: Path, sample_showdoc: ShowDoc
    ) -> None:
        """Test that save_showdoc creates JSON file with correct structure."""
        # Arrange
        persistence = ShowDocPersistence(storage_dir=str(tmp_path))

        # Act
        persistence.save_showdoc(sample_showdoc)

        # Assert
        json_file = tmp_path / "12345.json"
        assert json_file.exists()

        with json_file.open() as f:
            data = json.load(f)

        assert data["anime_id"] == "12345"
        assert data["anidb_anime_id"] == 12345
        assert data["title_main"] == "Test Anime"
        assert "_metadata" in data
        assert data["_metadata"]["source"] == "mcp_anidb"
        assert "fetched_at" in data["_metadata"]

    def test_save_showdoc_updates_index(
        self, tmp_path: Path, sample_showdoc: ShowDoc
    ) -> None:
        """Test that save_showdoc updates the index file."""
        # Arrange
        persistence = ShowDocPersistence(storage_dir=str(tmp_path))

        # Act
        persistence.save_showdoc(sample_showdoc)

        # Assert
        assert "12345" in persistence.index["anime"]
        assert persistence.index["anime"]["12345"]["title"] == "Test Anime"
        assert persistence.index["anime"]["12345"]["anime_id"] == "12345"
        assert persistence.index["anime"]["12345"]["file"] == "12345.json"

    def test_load_showdoc_reconstructs_identical_object(
        self, tmp_path: Path, sample_showdoc: ShowDoc
    ) -> None:
        """Test that load_showdoc reconstructs identical ShowDoc."""
        # Arrange
        persistence = ShowDocPersistence(storage_dir=str(tmp_path))
        persistence.save_showdoc(sample_showdoc)

        # Act
        loaded = persistence.load_showdoc(12345)

        # Assert
        assert loaded is not None
        assert loaded.anime_id == sample_showdoc.anime_id
        assert loaded.anidb_anime_id == sample_showdoc.anidb_anime_id
        assert loaded.title_main == sample_showdoc.title_main
        assert loaded.title_alts == sample_showdoc.title_alts
        assert loaded.description == sample_showdoc.description
        assert loaded.tags == sample_showdoc.tags
        assert loaded.episode_count_normal == sample_showdoc.episode_count_normal
        assert loaded.air_date == sample_showdoc.air_date
        assert loaded.end_date == sample_showdoc.end_date
        assert loaded.rating == sample_showdoc.rating

    def test_load_showdoc_returns_none_for_missing(self, tmp_path: Path) -> None:
        """Test that load_showdoc returns None for missing anime."""
        # Arrange
        persistence = ShowDocPersistence(storage_dir=str(tmp_path))

        # Act
        loaded = persistence.load_showdoc(99999)

        # Assert
        assert loaded is None

    def test_exists_returns_true_for_cached_anime(
        self, tmp_path: Path, sample_showdoc: ShowDoc
    ) -> None:
        """Test that exists returns True for cached anime."""
        # Arrange
        persistence = ShowDocPersistence(storage_dir=str(tmp_path))
        persistence.save_showdoc(sample_showdoc)

        # Act & Assert
        assert persistence.exists(12345) is True

    def test_exists_returns_false_for_missing_anime(self, tmp_path: Path) -> None:
        """Test that exists returns False for missing anime."""
        # Arrange
        persistence = ShowDocPersistence(storage_dir=str(tmp_path))

        # Act & Assert
        assert persistence.exists(99999) is False

    def test_get_all_showdocs_loads_all_cached_anime(
        self, tmp_path: Path, sample_showdoc: ShowDoc
    ) -> None:
        """Test that get_all_showdocs loads all cached anime."""
        # Arrange
        persistence = ShowDocPersistence(storage_dir=str(tmp_path))

        # Create multiple ShowDocs
        showdoc1 = sample_showdoc
        showdoc2 = ShowDoc(
            anime_id="67890",
            anidb_anime_id=67890,
            title_main="Another Anime",
            title_alts=["別のアニメ"],
        )

        persistence.save_showdoc(showdoc1)
        persistence.save_showdoc(showdoc2)

        # Act
        all_showdocs = persistence.get_all_showdocs()

        # Assert
        assert len(all_showdocs) == 2
        anime_ids = {sd.anidb_anime_id for sd in all_showdocs}
        assert 12345 in anime_ids
        assert 67890 in anime_ids

    def test_get_stats_returns_correct_statistics(
        self, tmp_path: Path, sample_showdoc: ShowDoc
    ) -> None:
        """Test that get_stats returns correct statistics."""
        # Arrange
        persistence = ShowDocPersistence(storage_dir=str(tmp_path))
        persistence.save_showdoc(sample_showdoc)

        # Act
        stats = persistence.get_stats()

        # Assert
        assert stats["total_anime"] == 1
        assert stats["storage_dir"] == str(tmp_path)
        assert stats["index_file"] == str(tmp_path / "index.json")
        assert "created" in stats
        assert stats["version"] == "1.0"

    def test_datetime_serialization_round_trip(
        self, tmp_path: Path, sample_showdoc: ShowDoc
    ) -> None:
        """Test that datetime serialization/deserialization works correctly."""
        # Arrange
        persistence = ShowDocPersistence(storage_dir=str(tmp_path))
        original_air_date = sample_showdoc.air_date
        original_end_date = sample_showdoc.end_date

        # Act
        persistence.save_showdoc(sample_showdoc)
        loaded = persistence.load_showdoc(12345)

        # Assert
        assert loaded is not None
        assert loaded.air_date == original_air_date
        assert loaded.end_date == original_end_date

    def test_handles_missing_file_gracefully(self, tmp_path: Path) -> None:
        """Test that load_showdoc handles missing files gracefully."""
        # Arrange
        persistence = ShowDocPersistence(storage_dir=str(tmp_path))

        # Manually add to index but don't create file
        persistence.index["anime"]["99999"] = {
            "title": "Missing",
            "anime_id": "99999",
            "file": "99999.json",
            "updated": datetime.now().isoformat(),
        }

        # Act
        loaded = persistence.load_showdoc(99999)

        # Assert
        assert loaded is None

    def test_handles_corrupt_json_gracefully(
        self, tmp_path: Path, sample_showdoc: ShowDoc
    ) -> None:
        """Test that load_showdoc handles corrupt JSON gracefully."""
        # Arrange
        persistence = ShowDocPersistence(storage_dir=str(tmp_path))
        persistence.save_showdoc(sample_showdoc)

        # Corrupt the JSON file
        json_file = tmp_path / "12345.json"
        json_file.write_text("{ invalid json }", encoding="utf-8")

        # Act & Assert
        with pytest.raises(json.JSONDecodeError):
            persistence.load_showdoc(12345)

    def test_multiple_saves_update_existing(
        self, tmp_path: Path, sample_showdoc: ShowDoc
    ) -> None:
        """Test that saving the same anime multiple times updates it."""
        # Arrange
        persistence = ShowDocPersistence(storage_dir=str(tmp_path))
        persistence.save_showdoc(sample_showdoc)

        # Modify the ShowDoc
        sample_showdoc.description = "Updated description"

        # Act
        persistence.save_showdoc(sample_showdoc)

        # Assert
        loaded = persistence.load_showdoc(12345)
        assert loaded is not None
        assert loaded.description == "Updated description"

        # Verify only one entry in index
        assert len(persistence.index["anime"]) == 1
