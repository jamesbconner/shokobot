"""Tests for IngestService data parsing and ingestion functionality.

This module tests ID extraction, title processing, tag parsing, description
cleaning, datetime parsing, and batch ingestion workflows.
"""

import json
from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest

from services.ingest_service import (
    _parse_datetime,
    _pick_id,
    _safe_int,
    _safe_str,
    _tags,
    _titles,
    ingest_showdocs_streaming,
    iter_showdocs_from_json,
)


class TestPickId:
    """Tests for _pick_id function."""

    def test_pick_id_with_anime_id(self) -> None:
        """Test ID extraction using AnimeID field."""
        # Arrange
        record = {"AnimeID": "12345", "AniDB_AnimeID": 67890}

        # Act
        result = _pick_id(record, id_field="AnimeID")

        # Assert
        assert result == "12345"

    def test_pick_id_with_anidb_id(self) -> None:
        """Test ID extraction using AniDB_AnimeID field when AnimeID is absent."""
        # Arrange
        record = {"AniDB_AnimeID": 67890}

        # Act
        result = _pick_id(record, id_field="AnimeID")

        # Assert
        assert result == "67890"

    def test_pick_id_fallback_to_anidb(self) -> None:
        """Test fallback to AniDB_AnimeID when specified field is None."""
        # Arrange
        record = {"AnimeID": None, "AniDB_AnimeID": 67890}

        # Act
        result = _pick_id(record, id_field="AnimeID")

        # Assert
        assert result == "67890"

    def test_pick_id_missing_both(self) -> None:
        """Test that error is raised when both IDs are missing."""
        # Arrange
        record = {"MainTitle": "Test Anime"}

        # Act & Assert
        with pytest.raises(ValueError, match="Record missing both AnimeID and AniDB_AnimeID"):
            _pick_id(record, id_field="AnimeID")

    def test_pick_id_both_none(self) -> None:
        """Test that error is raised when both IDs are None."""
        # Arrange
        record = {"AnimeID": None, "AniDB_AnimeID": None}

        # Act & Assert
        with pytest.raises(ValueError, match="Record missing both AnimeID and AniDB_AnimeID"):
            _pick_id(record, id_field="AnimeID")

    def test_pick_id_prefers_specified_field(self) -> None:
        """Test that specified field is preferred when both exist."""
        # Arrange
        record = {"AnimeID": "12345", "AniDB_AnimeID": 67890}

        # Act
        result = _pick_id(record, id_field="AniDB_AnimeID")

        # Assert
        assert result == "67890"


class TestTitles:
    """Tests for _titles function."""

    def test_titles_extraction(self) -> None:
        """Test main title and alternates extraction."""
        # Arrange
        record = {
            "MainTitle": "Test Anime",
            "AllTitles": "Test Anime|テストアニメ|Test Anime Title",
        }

        # Act
        main, alts = _titles(record)

        # Assert
        assert main == "Test Anime"
        assert "Test Anime" in alts
        assert "テストアニメ" in alts
        assert "Test Anime Title" in alts

    def test_titles_deduplication(self) -> None:
        """Test duplicate title removal (case-insensitive)."""
        # Arrange
        record = {
            "MainTitle": "Test Anime",
            "AllTitles": "Test Anime|test anime|TEST ANIME|Other Title",
        }

        # Act
        main, alts = _titles(record)

        # Assert
        assert main == "Test Anime"
        # Should only have Test Anime once (case-insensitive dedup)
        assert alts.count("Test Anime") == 1
        assert "Other Title" in alts
        # Verify no duplicate variations
        assert len([t for t in alts if t.lower() == "test anime"]) == 1

    def test_titles_missing_main_title(self) -> None:
        """Test handling when MainTitle is missing."""
        # Arrange
        record = {"AllTitles": "Title 1|Title 2"}

        # Act
        main, alts = _titles(record)

        # Assert
        assert main == "Unknown Title"
        assert "Unknown Title" in alts

    def test_titles_empty_main_title(self) -> None:
        """Test handling when MainTitle is empty string."""
        # Arrange
        record = {"MainTitle": "   ", "AllTitles": "Title 1|Title 2"}

        # Act
        main, alts = _titles(record)

        # Assert
        assert main == "Unknown Title"

    def test_titles_whitespace_trimming(self) -> None:
        """Test that whitespace is trimmed from titles."""
        # Arrange
        record = {
            "MainTitle": "  Test Anime  ",
            "AllTitles": "  Test Anime  |  Other Title  ",
        }

        # Act
        main, alts = _titles(record)

        # Assert
        assert main == "Test Anime"
        assert "Test Anime" in alts
        assert "Other Title" in alts

    def test_titles_main_included_in_alts(self) -> None:
        """Test that main title is always included in alternates list."""
        # Arrange
        record = {"MainTitle": "Main Title", "AllTitles": "Other Title|Another Title"}

        # Act
        main, alts = _titles(record)

        # Assert
        assert main == "Main Title"
        assert "Main Title" in alts
        assert alts[0] == "Main Title"  # Should be first


class TestTags:
    """Tests for _tags function."""

    def test_tags_extraction(self) -> None:
        """Test pipe-separated tag parsing."""
        # Arrange
        record = {"AllTags": "action|comedy|drama|romance"}

        # Act
        result = _tags(record)

        # Assert
        assert result == ["action", "comedy", "drama", "romance"]

    def test_tags_empty_field(self) -> None:
        """Test handling when AllTags is missing or empty."""
        # Arrange
        record_missing: dict[str, Any] = {}
        record_empty = {"AllTags": ""}

        # Act
        result_missing = _tags(record_missing)
        result_empty = _tags(record_empty)

        # Assert
        assert result_missing == []
        assert result_empty == []

    def test_tags_whitespace_handling(self) -> None:
        """Test that whitespace is trimmed from tags."""
        # Arrange
        record = {"AllTags": "  action  |  comedy  |  drama  "}

        # Act
        result = _tags(record)

        # Assert
        assert result == ["action", "comedy", "drama"]

    def test_tags_empty_elements_removed(self) -> None:
        """Test that empty tag elements are removed."""
        # Arrange
        record = {"AllTags": "action||comedy|||drama"}

        # Act
        result = _tags(record)

        # Assert
        assert result == ["action", "comedy", "drama"]

    def test_tags_deduplication(self) -> None:
        """Test that duplicate tags are removed (case-insensitive)."""
        # Arrange
        record = {"AllTags": "action|Action|ACTION|comedy"}

        # Act
        result = _tags(record)

        # Assert
        assert len(result) == 2
        assert "action" in result
        assert "comedy" in result


class TestParseDatetime:
    """Tests for _parse_datetime function."""

    def test_parse_datetime_valid(self) -> None:
        """Test valid datetime parsing."""
        # Arrange
        date_str = "2020-01-15 12:30:45"

        # Act
        result = _parse_datetime(date_str)

        # Assert
        assert result is not None
        assert result.year == 2020
        assert result.month == 1
        assert result.day == 15
        assert result.hour == 12
        assert result.minute == 30
        assert result.second == 45

    def test_parse_datetime_invalid(self) -> None:
        """Test invalid datetime handling."""
        # Arrange
        invalid_dates = [
            "invalid-date",
            "2020-13-01 00:00:00",  # Invalid month
            "not a date",
            "2020/01/15 00:00:00",  # Wrong format
        ]

        # Act & Assert
        for date_str in invalid_dates:
            result = _parse_datetime(date_str)
            assert result is None

    def test_parse_datetime_none(self) -> None:
        """Test None input returns None."""
        # Act
        result = _parse_datetime(None)

        # Assert
        assert result is None

    def test_parse_datetime_empty_string(self) -> None:
        """Test empty string returns None."""
        # Act
        result = _parse_datetime("")

        # Assert
        assert result is None

    def test_parse_datetime_whitespace(self) -> None:
        """Test whitespace-only string returns None."""
        # Act
        result = _parse_datetime("   ")

        # Assert
        assert result is None

    def test_parse_datetime_with_leading_trailing_whitespace(self) -> None:
        """Test datetime with whitespace is parsed correctly."""
        # Arrange
        date_str = "  2020-01-15 00:00:00  "

        # Act
        result = _parse_datetime(date_str)

        # Assert
        assert result is not None
        assert result.year == 2020


class TestSafeInt:
    """Tests for _safe_int function."""

    def test_safe_int_conversion(self) -> None:
        """Test safe integer conversion with valid inputs."""
        # Arrange & Act & Assert
        assert _safe_int(42) == 42
        assert _safe_int("42") == 42
        assert _safe_int(42.7) == 42
        assert _safe_int("100") == 100

    def test_safe_int_none(self) -> None:
        """Test None returns default value."""
        # Act & Assert
        assert _safe_int(None) == 0
        assert _safe_int(None, default=99) == 99

    def test_safe_int_invalid_string(self) -> None:
        """Test invalid string returns default value."""
        # Act & Assert
        assert _safe_int("not a number") == 0
        assert _safe_int("abc", default=10) == 10

    def test_safe_int_empty_string(self) -> None:
        """Test empty string returns default value."""
        # Act & Assert
        assert _safe_int("") == 0
        assert _safe_int("", default=5) == 5

    def test_safe_int_custom_default(self) -> None:
        """Test custom default value is used."""
        # Act & Assert
        assert _safe_int(None, default=100) == 100
        assert _safe_int("invalid", default=-1) == -1


class TestSafeStr:
    """Tests for _safe_str function."""

    def test_safe_str_valid_string(self) -> None:
        """Test valid string conversion."""
        # Act & Assert
        assert _safe_str("test") == "test"
        assert _safe_str("  test  ") == "test"

    def test_safe_str_none(self) -> None:
        """Test None returns None."""
        # Act
        result = _safe_str(None)

        # Assert
        assert result is None

    def test_safe_str_empty_string(self) -> None:
        """Test empty string returns None."""
        # Act
        result = _safe_str("")

        # Assert
        assert result is None

    def test_safe_str_whitespace_only(self) -> None:
        """Test whitespace-only string returns None."""
        # Act
        result = _safe_str("   ")

        # Assert
        assert result is None

    def test_safe_str_number_conversion(self) -> None:
        """Test number to string conversion."""
        # Act & Assert
        assert _safe_str(42) == "42"
        assert _safe_str(3.14) == "3.14"


class TestIterShowdocsFromJson:
    """Tests for iter_showdocs_from_json function."""

    def test_iter_showdocs_from_json(
        self, tmp_path: Path, mock_context: Mock, sample_anime_data: dict[str, Any]
    ) -> None:
        """Test JSON file iteration and ShowDoc generation."""
        # Arrange
        json_file = tmp_path / "test_anime.json"
        json_data = {"AniDB_Anime": [sample_anime_data]}
        json_file.write_text(json.dumps(json_data), encoding="utf-8")

        # Act
        result = list(iter_showdocs_from_json(mock_context, path=json_file))

        # Assert
        assert len(result) == 1
        doc = result[0]
        assert doc.anime_id == "123"
        assert doc.anidb_anime_id == 456
        assert doc.title_main == "Test Anime"

    def test_iter_showdocs_from_json_multiple_records(
        self, tmp_path: Path, mock_context: Mock
    ) -> None:
        """Test iteration with multiple anime records."""
        # Arrange
        json_file = tmp_path / "test_anime.json"
        json_data = {
            "AniDB_Anime": [
                {
                    "AnimeID": "1",
                    "AniDB_AnimeID": 100,
                    "MainTitle": "Anime 1",
                    "AllTitles": "Anime 1",
                },
                {
                    "AnimeID": "2",
                    "AniDB_AnimeID": 200,
                    "MainTitle": "Anime 2",
                    "AllTitles": "Anime 2",
                },
                {
                    "AnimeID": "3",
                    "AniDB_AnimeID": 300,
                    "MainTitle": "Anime 3",
                    "AllTitles": "Anime 3",
                },
            ]
        }
        json_file.write_text(json.dumps(json_data), encoding="utf-8")

        # Act
        result = list(iter_showdocs_from_json(mock_context, path=json_file))

        # Assert
        assert len(result) == 3
        assert result[0].anime_id == "1"
        assert result[1].anime_id == "2"
        assert result[2].anime_id == "3"

    def test_iter_showdocs_from_json_missing_file(self, mock_context: Mock) -> None:
        """Test error handling when JSON file doesn't exist."""
        # Arrange
        mock_context.config.get.return_value = "/nonexistent/file.json"

        # Act & Assert
        with pytest.raises(FileNotFoundError):
            list(iter_showdocs_from_json(mock_context))

    def test_iter_showdocs_from_json_invalid_json(self, tmp_path: Path, mock_context: Mock) -> None:
        """Test error handling with malformed JSON."""
        # Arrange
        json_file = tmp_path / "invalid.json"
        json_file.write_text("{ invalid json }", encoding="utf-8")

        # Act & Assert
        with pytest.raises(json.JSONDecodeError):
            list(iter_showdocs_from_json(mock_context, path=json_file))

    def test_iter_showdocs_from_json_empty_list(self, tmp_path: Path, mock_context: Mock) -> None:
        """Test handling of empty anime list."""
        # Arrange
        json_file = tmp_path / "empty.json"
        json_data: dict[str, list[Any]] = {"AniDB_Anime": []}
        json_file.write_text(json.dumps(json_data), encoding="utf-8")

        # Act
        result = list(iter_showdocs_from_json(mock_context, path=json_file))

        # Assert
        assert result == []

    def test_iter_showdocs_from_json_missing_anidb_key(
        self, tmp_path: Path, mock_context: Mock
    ) -> None:
        """Test handling when AniDB_Anime key is missing."""
        # Arrange
        json_file = tmp_path / "no_key.json"
        json_data: dict[str, list[Any]] = {"SomeOtherKey": []}
        json_file.write_text(json.dumps(json_data), encoding="utf-8")

        # Act
        result = list(iter_showdocs_from_json(mock_context, path=json_file))

        # Assert
        assert result == []

    def test_iter_showdocs_from_json_skips_invalid_records(
        self, tmp_path: Path, mock_context: Mock
    ) -> None:
        """Test that invalid records are skipped gracefully."""
        # Arrange
        json_file = tmp_path / "mixed.json"
        json_data = {
            "AniDB_Anime": [
                {
                    "AnimeID": "1",
                    "AniDB_AnimeID": 100,
                    "MainTitle": "Valid Anime",
                    "AllTitles": "Valid Anime",
                },
                {
                    # Missing AniDB_AnimeID - should be skipped
                    "AnimeID": "2",
                    "MainTitle": "Invalid Anime",
                },
                {
                    "AnimeID": "3",
                    "AniDB_AnimeID": 300,
                    "MainTitle": "Another Valid",
                    "AllTitles": "Another Valid",
                },
            ]
        }
        json_file.write_text(json.dumps(json_data), encoding="utf-8")

        # Act
        result = list(iter_showdocs_from_json(mock_context, path=json_file))

        # Assert
        # Should only get 2 valid records
        assert len(result) == 2
        assert result[0].anime_id == "1"
        assert result[1].anime_id == "3"

    def test_iter_showdocs_from_json_anidb_not_list(
        self, tmp_path: Path, mock_context: Mock
    ) -> None:
        """Test error when AniDB_Anime is not a list."""
        # Arrange
        json_file = tmp_path / "invalid_type.json"
        json_data = {"AniDB_Anime": "not a list"}  # Should be a list
        json_file.write_text(json.dumps(json_data), encoding="utf-8")

        # Act & Assert
        with pytest.raises(ValueError, match="Expected 'AniDB_Anime' to be a list"):
            list(iter_showdocs_from_json(mock_context, path=json_file))

    def test_iter_showdocs_from_json_anidb_is_dict(
        self, tmp_path: Path, mock_context: Mock
    ) -> None:
        """Test error when AniDB_Anime is a dict instead of list."""
        # Arrange
        json_file = tmp_path / "dict_type.json"
        json_data = {"AniDB_Anime": {"key": "value"}}  # Should be a list
        json_file.write_text(json.dumps(json_data), encoding="utf-8")

        # Act & Assert
        with pytest.raises(ValueError, match="Expected 'AniDB_Anime' to be a list"):
            list(iter_showdocs_from_json(mock_context, path=json_file))

    def test_iter_showdocs_from_json_record_processing_error(
        self, tmp_path: Path, mock_context: Mock
    ) -> None:
        """Test that records with processing errors are skipped."""
        # Arrange
        json_file = tmp_path / "error_records.json"
        json_data = {
            "AniDB_Anime": [
                {
                    "AnimeID": "1",
                    "AniDB_AnimeID": 100,
                    "MainTitle": "Valid Anime",
                    "AllTitles": "Valid Anime",
                },
                {
                    # This will cause an error - invalid data type for ShowDoc
                    "AnimeID": "2",
                    "AniDB_AnimeID": "not_a_number",  # Should be int
                    "MainTitle": "Invalid Anime",
                    "AllTitles": "Invalid Anime",
                    "EpisodeCountNormal": "invalid",  # Will cause conversion error
                },
                {
                    "AnimeID": "3",
                    "AniDB_AnimeID": 300,
                    "MainTitle": "Another Valid",
                    "AllTitles": "Another Valid",
                },
            ]
        }
        json_file.write_text(json.dumps(json_data), encoding="utf-8")

        # Act
        result = list(iter_showdocs_from_json(mock_context, path=json_file))

        # Assert - should skip the problematic record
        assert len(result) == 2
        assert result[0].anime_id == "1"
        assert result[1].anime_id == "3"


class TestIngestShowdocsStreaming:
    """Tests for ingest_showdocs_streaming function."""

    def test_ingest_showdocs_streaming(
        self, mock_context: Mock, sample_show_doc_dict: dict[str, Any]
    ) -> None:
        """Test batch ingestion with mocked vectorstore."""
        # Arrange
        from models.show_doc import ShowDoc

        docs = [ShowDoc(**sample_show_doc_dict) for _ in range(5)]
        mock_context.config.get.return_value = 2  # batch_size = 2

        # Act
        total = ingest_showdocs_streaming(docs, mock_context, batch_size=2)

        # Assert
        assert total == 5
        # Verify vectorstore.add_documents was called (3 batches: 2, 2, 1)
        assert mock_context.vectorstore.add_documents.call_count == 3

    def test_ingest_showdocs_streaming_custom_batch_size(
        self, mock_context: Mock, sample_show_doc_dict: dict[str, Any]
    ) -> None:
        """Test ingestion with custom batch size."""
        # Arrange
        from models.show_doc import ShowDoc

        docs = [ShowDoc(**sample_show_doc_dict) for _ in range(10)]

        # Act
        total = ingest_showdocs_streaming(docs, mock_context, batch_size=3)

        # Assert
        assert total == 10
        # Verify batching: 3, 3, 3, 1
        assert mock_context.vectorstore.add_documents.call_count == 4

    def test_ingest_showdocs_streaming_empty_list(self, mock_context: Mock) -> None:
        """Test ingestion with empty document list."""
        # Arrange
        docs: list = []

        # Act
        total = ingest_showdocs_streaming(docs, mock_context, batch_size=10)

        # Assert
        assert total == 0
        assert mock_context.vectorstore.add_documents.call_count == 0

    def test_ingest_showdocs_streaming_single_document(
        self, mock_context: Mock, sample_show_doc_dict: dict[str, Any]
    ) -> None:
        """Test ingestion with single document."""
        # Arrange
        from models.show_doc import ShowDoc

        docs = [ShowDoc(**sample_show_doc_dict)]

        # Act
        total = ingest_showdocs_streaming(docs, mock_context, batch_size=10)

        # Assert
        assert total == 1
        assert mock_context.vectorstore.add_documents.call_count == 1

    def test_ingest_showdocs_streaming_invalid_batch_size(
        self, mock_context: Mock, sample_show_doc_dict: dict[str, Any]
    ) -> None:
        """Test that invalid batch size raises ValueError."""
        # Arrange
        from models.show_doc import ShowDoc

        docs = [ShowDoc(**sample_show_doc_dict)]

        # Act & Assert: negative batch size
        with pytest.raises(ValueError, match="batch_size must be positive"):
            ingest_showdocs_streaming(docs, mock_context, batch_size=-1)

        # Note: batch_size=0 falls back to config default due to `or` operator,
        # so we test with explicit negative value instead

    def test_ingest_showdocs_streaming_upsert_failure(
        self, mock_context: Mock, sample_show_doc_dict: dict[str, Any]
    ) -> None:
        """Test that upsert failures are properly raised."""
        # Arrange
        from models.show_doc import ShowDoc

        docs = [ShowDoc(**sample_show_doc_dict) for _ in range(3)]

        # Make vectorstore.add_documents raise an exception
        mock_context.vectorstore.add_documents.side_effect = RuntimeError(
            "Database connection failed"
        )

        # Act & Assert
        with pytest.raises(RuntimeError, match="Database connection failed"):
            ingest_showdocs_streaming(docs, mock_context, batch_size=2)

    def test_ingest_showdocs_streaming_partial_failure(
        self, mock_context: Mock, sample_show_doc_dict: dict[str, Any]
    ) -> None:
        """Test that failures after partial ingestion are handled correctly."""
        # Arrange
        from models.show_doc import ShowDoc

        docs = [ShowDoc(**sample_show_doc_dict) for _ in range(5)]

        # Make vectorstore fail on the second batch
        mock_context.vectorstore.add_documents.side_effect = [
            None,  # First batch succeeds
            RuntimeError("Network error"),  # Second batch fails
        ]

        # Act & Assert
        with pytest.raises(RuntimeError, match="Network error"):
            ingest_showdocs_streaming(docs, mock_context, batch_size=2)


class TestValidateShowdocsDryRun:
    """Tests for validate_showdocs_dry_run function."""

    def test_validate_showdocs_dry_run_basic(self) -> None:
        """Test dry-run validation with basic ShowDocs."""
        from models.show_doc import ShowDoc
        from services.ingest_service import validate_showdocs_dry_run

        # Arrange
        docs = [
            ShowDoc(
                anime_id="1",
                anidb_anime_id=1,
                title_main="Anime 1",
                begin_year=2020,
                episode_count_normal=12,
            ),
            ShowDoc(
                anime_id="2",
                anidb_anime_id=2,
                title_main="Anime 2",
                begin_year=2021,
                episode_count_normal=24,
            ),
            ShowDoc(
                anime_id="3",
                anidb_anime_id=3,
                title_main="Anime 3",
                begin_year=2022,
                episode_count_normal=13,
            ),
        ]

        # Act
        stats = validate_showdocs_dry_run(iter(docs), batch_size=2)

        # Assert
        assert stats["total"] == 3
        assert stats["batch_count"] == 2
        assert len(stats["sample_titles"]) == 3
        assert stats["year_range"] == (2020, 2022)
        assert stats["episode_stats"]["min"] == 12
        assert stats["episode_stats"]["max"] == 24
        assert stats["episode_stats"]["avg"] == (12 + 24 + 13) / 3
        assert stats["errors"] == []

    def test_validate_showdocs_dry_run_sample_titles_limit(self) -> None:
        """Test that sample titles are limited to 10."""
        from models.show_doc import ShowDoc
        from services.ingest_service import validate_showdocs_dry_run

        # Arrange - create 15 docs (start from 1 since anidb_anime_id must be > 0)
        docs = [
            ShowDoc(
                anime_id=str(i),
                anidb_anime_id=i,
                title_main=f"Anime {i}",
            )
            for i in range(1, 16)
        ]

        # Act
        stats = validate_showdocs_dry_run(iter(docs))

        # Assert
        assert stats["total"] == 15
        assert len(stats["sample_titles"]) == 10  # Limited to 10

    def test_validate_showdocs_dry_run_no_years(self) -> None:
        """Test dry-run with docs that have no year data."""
        from models.show_doc import ShowDoc
        from services.ingest_service import validate_showdocs_dry_run

        # Arrange
        docs = [
            ShowDoc(anime_id="1", anidb_anime_id=1, title_main="Anime 1"),
            ShowDoc(anime_id="2", anidb_anime_id=2, title_main="Anime 2"),
        ]

        # Act
        stats = validate_showdocs_dry_run(iter(docs))

        # Assert
        assert stats["total"] == 2
        assert stats["year_range"] is None

    def test_validate_showdocs_dry_run_no_episodes(self) -> None:
        """Test dry-run with docs that have no episode data."""
        from models.show_doc import ShowDoc
        from services.ingest_service import validate_showdocs_dry_run

        # Arrange
        docs = [
            ShowDoc(anime_id="1", anidb_anime_id=1, title_main="Anime 1"),
            ShowDoc(anime_id="2", anidb_anime_id=2, title_main="Anime 2"),
        ]

        # Act
        stats = validate_showdocs_dry_run(iter(docs))

        # Assert
        assert stats["total"] == 2
        assert stats["episode_stats"] == {}

    def test_validate_showdocs_dry_run_invalid_batch_size(self) -> None:
        """Test that invalid batch size raises ValueError."""
        from services.ingest_service import validate_showdocs_dry_run

        # Act & Assert - only negative values raise error (0 becomes 100 due to `or` operator)
        with pytest.raises(ValueError, match="batch_size must be positive"):
            validate_showdocs_dry_run(iter([]), batch_size=-1)

    def test_validate_showdocs_dry_run_conversion_error(self) -> None:
        """Test dry-run captures conversion errors."""
        from unittest.mock import Mock, patch

        from models.show_doc import ShowDoc
        from services.ingest_service import validate_showdocs_dry_run

        # Arrange
        docs = [
            ShowDoc(anime_id="1", anidb_anime_id=1, title_main="Anime 1"),
            ShowDoc(anime_id="2", anidb_anime_id=2, title_main="Anime 2"),
        ]

        # Mock to_langchain_doc to raise error for second doc
        with patch.object(ShowDoc, "to_langchain_doc") as mock_convert:
            mock_convert.side_effect = [
                Mock(),  # First call succeeds
                Exception("Conversion failed"),  # Second call fails
            ]

            # Act
            stats = validate_showdocs_dry_run(iter(docs))

            # Assert
            assert stats["total"] == 2
            assert len(stats["errors"]) == 1
            assert "Failed to convert 2" in stats["errors"][0]
            assert "Conversion failed" in stats["errors"][0]

    def test_validate_showdocs_dry_run_empty_iterator(self) -> None:
        """Test dry-run with empty iterator."""
        from services.ingest_service import validate_showdocs_dry_run

        # Act
        stats = validate_showdocs_dry_run(iter([]))

        # Assert
        assert stats["total"] == 0
        assert stats["batch_count"] == 0
        assert stats["sample_titles"] == []
        assert stats["year_range"] is None
        assert stats["episode_stats"] == {}
        assert stats["errors"] == []

    def test_validate_showdocs_dry_run_custom_batch_size(self) -> None:
        """Test dry-run with custom batch size."""
        from models.show_doc import ShowDoc
        from services.ingest_service import validate_showdocs_dry_run

        # Arrange - create 10 docs (start from 1 since anidb_anime_id must be > 0)
        docs = [
            ShowDoc(anime_id=str(i), anidb_anime_id=i, title_main=f"Anime {i}")
            for i in range(1, 11)
        ]

        # Act
        stats = validate_showdocs_dry_run(iter(docs), batch_size=3)

        # Assert
        assert stats["total"] == 10
        assert stats["batch_count"] == 4  # 3 + 3 + 3 + 1

    def test_validate_showdocs_dry_run_mixed_episode_data(self) -> None:
        """Test dry-run with mixed episode data (some zero, some positive)."""
        from models.show_doc import ShowDoc
        from services.ingest_service import validate_showdocs_dry_run

        # Arrange
        docs = [
            ShowDoc(
                anime_id="1",
                anidb_anime_id=1,
                title_main="Anime 1",
                episode_count_normal=12,
            ),
            ShowDoc(
                anime_id="2",
                anidb_anime_id=2,
                title_main="Anime 2",
                episode_count_normal=0,  # Zero episodes
            ),
            ShowDoc(
                anime_id="3",
                anidb_anime_id=3,
                title_main="Anime 3",
                episode_count_normal=24,
            ),
        ]

        # Act
        stats = validate_showdocs_dry_run(iter(docs))

        # Assert
        assert stats["total"] == 3
        # Only non-zero episodes should be included in stats
        assert stats["episode_stats"]["min"] == 12
        assert stats["episode_stats"]["max"] == 24
