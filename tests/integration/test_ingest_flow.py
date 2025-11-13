"""Integration tests for end-to-end ingestion flow.

This module tests the complete ingestion pipeline from JSON file to vectorstore,
with mocked external dependencies.
"""

import json
from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch

import pytest

from services.ingest_service import ingest_showdocs_streaming, iter_showdocs_from_json


class TestFullIngestFlow:
    """Tests for complete ingestion flow from JSON to vectorstore."""

    @patch("services.ingest_service.upsert_documents")
    def test_full_ingest_flow(
        self,
        mock_upsert: Mock,
        tmp_path: Path,
        mock_context: Mock,
        sample_anime_data: dict[str, Any],
    ) -> None:
        """Test complete ingestion from JSON file to vectorstore."""
        # Arrange: Create JSON file with sample data
        json_file = tmp_path / "anime.json"
        json_data = {"AniDB_Anime": [sample_anime_data]}
        json_file.write_text(json.dumps(json_data), encoding="utf-8")

        mock_upsert.return_value = None

        # Act: Run full ingestion pipeline
        docs = iter_showdocs_from_json(mock_context, path=json_file)
        total = ingest_showdocs_streaming(docs, mock_context, batch_size=10)

        # Assert: Verify documents were processed
        assert total == 1
        assert mock_upsert.call_count == 1
        # Verify the documents passed to upsert
        call_args = mock_upsert.call_args[0]
        assert len(call_args[0]) == 1  # One document in batch

    @patch("services.ingest_service.upsert_documents")
    def test_full_ingest_flow_multiple_records(
        self, mock_upsert: Mock, tmp_path: Path, mock_context: Mock
    ) -> None:
        """Test ingestion with multiple anime records."""
        # Arrange: Create JSON with multiple records
        json_file = tmp_path / "anime.json"
        json_data = {
            "AniDB_Anime": [
                {
                    "AnimeID": str(i),
                    "AniDB_AnimeID": i * 100,
                    "MainTitle": f"Anime {i}",
                    "AllTitles": f"Anime {i}",
                }
                for i in range(1, 26)  # 25 records
            ]
        }
        json_file.write_text(json.dumps(json_data), encoding="utf-8")

        mock_upsert.return_value = None

        # Act: Run ingestion with batch size of 10
        docs = iter_showdocs_from_json(mock_context, path=json_file)
        total = ingest_showdocs_streaming(docs, mock_context, batch_size=10)

        # Assert: Verify all documents processed in batches
        assert total == 25
        # Should be 3 batches: 10, 10, 5
        assert mock_upsert.call_count == 3

    @patch("services.ingest_service.upsert_documents")
    def test_ingest_with_invalid_data(
        self, mock_upsert: Mock, tmp_path: Path, mock_context: Mock
    ) -> None:
        """Test that ingestion handles invalid records gracefully."""
        # Arrange: Create JSON with mix of valid and invalid records
        json_file = tmp_path / "anime.json"
        json_data = {
            "AniDB_Anime": [
                {
                    "AnimeID": "1",
                    "AniDB_AnimeID": 100,
                    "MainTitle": "Valid Anime 1",
                    "AllTitles": "Valid Anime 1",
                },
                {
                    # Missing AniDB_AnimeID - invalid
                    "AnimeID": "2",
                    "MainTitle": "Invalid Anime",
                },
                {
                    "AnimeID": "3",
                    "AniDB_AnimeID": 300,
                    "MainTitle": "Valid Anime 2",
                    "AllTitles": "Valid Anime 2",
                },
                {
                    # Missing both IDs - invalid
                    "MainTitle": "Invalid Anime 2",
                },
                {
                    "AnimeID": "4",
                    "AniDB_AnimeID": 400,
                    "MainTitle": "Valid Anime 3",
                    "AllTitles": "Valid Anime 3",
                },
            ]
        }
        json_file.write_text(json.dumps(json_data), encoding="utf-8")

        mock_upsert.return_value = None

        # Act: Run ingestion
        docs = iter_showdocs_from_json(mock_context, path=json_file)
        total = ingest_showdocs_streaming(docs, mock_context, batch_size=10)

        # Assert: Only valid records processed
        assert total == 3
        assert mock_upsert.call_count == 1

    @patch("services.ingest_service.upsert_documents")
    def test_ingest_empty_file(self, mock_upsert: Mock, tmp_path: Path, mock_context: Mock) -> None:
        """Test that ingestion completes without errors for empty file."""
        # Arrange: Create JSON with empty anime list
        json_file = tmp_path / "anime.json"
        json_data = {"AniDB_Anime": []}
        json_file.write_text(json.dumps(json_data), encoding="utf-8")

        mock_upsert.return_value = None

        # Act: Run ingestion
        docs = iter_showdocs_from_json(mock_context, path=json_file)
        total = ingest_showdocs_streaming(docs, mock_context, batch_size=10)

        # Assert: No documents processed
        assert total == 0
        assert mock_upsert.call_count == 0

    def test_ingest_missing_file(self, mock_context: Mock) -> None:
        """Test that missing file raises appropriate error."""
        # Arrange: Non-existent file path
        json_file = Path("/nonexistent/file.json")

        # Act & Assert: Should raise FileNotFoundError
        with pytest.raises(FileNotFoundError):
            list(iter_showdocs_from_json(mock_context, path=json_file))

    def test_ingest_malformed_json(self, tmp_path: Path, mock_context: Mock) -> None:
        """Test that malformed JSON raises appropriate error."""
        # Arrange: Create file with invalid JSON
        json_file = tmp_path / "invalid.json"
        json_file.write_text("{ invalid json }", encoding="utf-8")

        # Act & Assert: Should raise JSONDecodeError
        with pytest.raises(json.JSONDecodeError):
            list(iter_showdocs_from_json(mock_context, path=json_file))

    @patch("services.ingest_service.upsert_documents")
    def test_ingest_preserves_data_integrity(
        self,
        mock_upsert: Mock,
        tmp_path: Path,
        mock_context: Mock,
        sample_anime_data: dict[str, Any],
    ) -> None:
        """Test that ingestion preserves all data fields correctly."""
        # Arrange: Create JSON with complete data
        json_file = tmp_path / "anime.json"
        json_data = {"AniDB_Anime": [sample_anime_data]}
        json_file.write_text(json.dumps(json_data), encoding="utf-8")

        mock_upsert.return_value = None

        # Act: Run ingestion
        docs = iter_showdocs_from_json(mock_context, path=json_file)
        total = ingest_showdocs_streaming(docs, mock_context, batch_size=10)

        # Assert: Verify data integrity
        assert total == 1
        call_args = mock_upsert.call_args[0]
        langchain_docs = call_args[0]
        assert len(langchain_docs) == 1

        doc = langchain_docs[0]
        # Verify key metadata preserved
        assert doc.metadata["anime_id"] == "123"
        assert doc.metadata["anidb_anime_id"] == 456
        assert doc.metadata["title_main"] == "Test Anime"
        # Verify content includes title
        assert "Test Anime" in doc.page_content

    @patch("services.ingest_service.upsert_documents")
    def test_ingest_batch_processing(
        self, mock_upsert: Mock, tmp_path: Path, mock_context: Mock
    ) -> None:
        """Test that batching works correctly with various sizes."""
        # Arrange: Create JSON with 23 records (to test remainder)
        json_file = tmp_path / "anime.json"
        json_data = {
            "AniDB_Anime": [
                {
                    "AnimeID": str(i),
                    "AniDB_AnimeID": i * 100,
                    "MainTitle": f"Anime {i}",
                    "AllTitles": f"Anime {i}",
                }
                for i in range(1, 24)
            ]
        }
        json_file.write_text(json.dumps(json_data), encoding="utf-8")

        mock_upsert.return_value = None

        # Act: Run ingestion with batch size of 7
        docs = iter_showdocs_from_json(mock_context, path=json_file)
        total = ingest_showdocs_streaming(docs, mock_context, batch_size=7)

        # Assert: Verify batching
        assert total == 23
        # Should be 4 batches: 7, 7, 7, 2
        assert mock_upsert.call_count == 4

        # Verify batch sizes
        call_args_list = mock_upsert.call_args_list
        assert len(call_args_list[0][0][0]) == 7  # First batch
        assert len(call_args_list[1][0][0]) == 7  # Second batch
        assert len(call_args_list[2][0][0]) == 7  # Third batch
        assert len(call_args_list[3][0][0]) == 2  # Fourth batch (remainder)
