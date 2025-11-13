"""Tests for MCP anime JSON parser.

This module tests the parse_anidb_json function which converts JSON responses
from the MCP anime server into ShowDoc instances.
"""

import json
from datetime import datetime

import pytest

from models.show_doc import ShowDoc
from services.mcp_anime_json_parser import parse_anidb_json

# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def valid_complete_anime_json() -> dict:
    """Complete valid anime JSON from MCP server with all fields."""
    return {
        "aid": 12345,
        "title": "Test Anime",
        "titles": [
            {"title": "Test Anime", "type": "main"},
            {"title": "テストアニメ", "type": "official"},
            {"title": "Test Anime Alt", "type": "synonym"},
        ],
        "synopsis": "Test description for anime",
        "tags": [
            {"name": "action", "weight": 600},
            {"name": "sci-fi", "weight": 400},
            {"name": "mecha", "weight": 300},
        ],
        "episode_count_normal": 12,
        "episode_count_special": 2,
        "start_date": "2023-01-15",
        "end_date": "2023-03-31",
        "begin_year": 2023,
        "end_year": 2023,
        "ratings": {
            "permanent": 8.5,
            "permanent_count": 1000,
            "review": 8.0,
            "review_count": 50,
        },
        "ann_id": 98765,
        "crunchyroll_id": "test-anime",
        "wikipedia_id": "Test_Anime",
        "related_anime": [
            {"id": 123, "type": "sequel", "title": "Test Anime 2"},
            {"id": 124, "type": "prequel", "title": "Test Anime 0"},
        ],
        "similar_anime": [
            {"id": 456, "approval": 85, "total": 100},
            {"id": 789, "approval": 92, "total": 120},
        ],
    }


@pytest.fixture
def minimal_anime_json() -> dict:
    """Minimal valid JSON with only required fields."""
    return {"aid": 12345, "title": "Test Anime"}


# ============================================================================
# Test Classes
# ============================================================================


class TestParseAnidbJson:
    """Tests for main parsing functionality."""

    def test_parse_valid_complete_json_as_dict(self, valid_complete_anime_json: dict) -> None:
        """Test parsing valid complete JSON passed as dict."""
        # Act
        result = parse_anidb_json(valid_complete_anime_json)

        # Assert
        assert isinstance(result, ShowDoc)
        assert result.anime_id == "12345"
        assert result.anidb_anime_id == 12345
        assert result.title_main == "Test Anime"
        assert result.description == "Test description for anime"
        assert result.episode_count_normal == 12
        assert result.episode_count_special == 2
        assert result.begin_year == 2023
        assert result.end_year == 2023
        assert result.rating == 850  # 8.5 * 100
        assert result.vote_count == 1000

    def test_parse_valid_complete_json_as_string(self, valid_complete_anime_json: dict) -> None:
        """Test parsing valid complete JSON passed as string."""
        # Arrange
        json_string = json.dumps(valid_complete_anime_json)

        # Act
        result = parse_anidb_json(json_string)

        # Assert
        assert isinstance(result, ShowDoc)
        assert result.anime_id == "12345"
        assert result.title_main == "Test Anime"

    def test_parse_minimal_json(self, minimal_anime_json: dict) -> None:
        """Test parsing minimal JSON with only required fields."""
        # Act
        result = parse_anidb_json(minimal_anime_json)

        # Assert
        assert isinstance(result, ShowDoc)
        assert result.anime_id == "12345"
        assert result.anidb_anime_id == 12345
        assert result.title_main == "Test Anime"
        # Check defaults are applied
        assert result.description == ""
        assert result.episode_count_normal == 0
        assert result.episode_count_special == 0
        assert result.title_alts == []
        assert result.tags == []


class TestParseAnidbJsonValidation:
    """Tests for required field validation."""

    def test_parse_json_missing_aid_raises_error(self) -> None:
        """Test that missing 'aid' field raises ValueError."""
        # Arrange
        json_data = {"title": "Test Anime"}

        # Act & Assert
        with pytest.raises(ValueError, match="Missing 'aid' field"):
            parse_anidb_json(json_data)

    def test_parse_json_missing_title_raises_error(self) -> None:
        """Test that missing 'title' field raises ValueError."""
        # Arrange
        json_data = {"aid": 12345}

        # Act & Assert
        with pytest.raises(ValueError, match="Missing 'title' field"):
            parse_anidb_json(json_data)

    def test_parse_json_aid_none_raises_error(self) -> None:
        """Test that None 'aid' field raises ValueError."""
        # Arrange
        json_data = {"aid": None, "title": "Test Anime"}

        # Act & Assert
        with pytest.raises(ValueError, match="Missing 'aid' field"):
            parse_anidb_json(json_data)

    def test_parse_json_title_empty_raises_error(self) -> None:
        """Test that empty 'title' field raises ValueError."""
        # Arrange
        json_data = {"aid": 12345, "title": ""}

        # Act & Assert
        with pytest.raises(ValueError, match="Missing 'title' field"):
            parse_anidb_json(json_data)


class TestParseAnidbJsonEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.mark.parametrize(
        "invalid_json,expected_error",
        [
            ("{invalid json", "Invalid JSON"),
            ("", "Invalid JSON"),
            ("not json at all", "Invalid JSON"),
        ],
    )
    def test_parse_invalid_json_string_raises_error(
        self, invalid_json: str, expected_error: str
    ) -> None:
        """Test that invalid JSON strings raise ValueError with descriptive message."""
        # Act & Assert
        with pytest.raises(ValueError, match=expected_error):
            parse_anidb_json(invalid_json)

    def test_parse_json_with_null_values_uses_defaults(self) -> None:
        """Test that null values in optional fields use defaults."""
        # Arrange
        json_data = {
            "aid": 12345,
            "title": "Test Anime",
            "synopsis": None,
            "episode_count_normal": None,
            "episode_count_special": None,
        }

        # Act
        result = parse_anidb_json(json_data)

        # Assert
        assert result.description == ""
        assert result.episode_count_normal == 0
        assert result.episode_count_special == 0

    def test_parse_json_with_empty_arrays(self) -> None:
        """Test that empty arrays are handled correctly."""
        # Arrange
        json_data = {
            "aid": 12345,
            "title": "Test Anime",
            "titles": [],
            "tags": [],
            "related_anime": [],
            "similar_anime": [],
        }

        # Act
        result = parse_anidb_json(json_data)

        # Assert
        assert result.title_alts == []
        assert result.tags == []
        assert result.relations == "[]"
        assert result.similar == "[]"


class TestParseAnidbJsonDateParsing:
    """Tests for date parsing scenarios."""

    def test_parse_valid_dates(self) -> None:
        """Test parsing valid date formats."""
        # Arrange
        json_data = {
            "aid": 12345,
            "title": "Test Anime",
            "start_date": "2023-01-15",
            "end_date": "2023-03-31",
        }

        # Act
        result = parse_anidb_json(json_data)

        # Assert
        assert result.air_date is not None
        assert result.end_date is not None
        assert isinstance(result.air_date, datetime)
        assert isinstance(result.end_date, datetime)

    @pytest.mark.parametrize(
        "invalid_date",
        [
            "invalid-date",
            "2023-13-01",  # Invalid month
            "2023-01-32",  # Invalid day
            "",
            "not-a-date",
        ],
    )
    def test_parse_invalid_dates_handled_gracefully(self, invalid_date: str) -> None:
        """Test that invalid date formats are handled gracefully."""
        # Arrange
        json_data = {
            "aid": 12345,
            "title": "Test Anime",
            "start_date": invalid_date,
            "end_date": invalid_date,
        }

        # Act - Should not raise exception
        result = parse_anidb_json(json_data)

        # Assert - Invalid dates should result in None
        assert result.air_date is None
        assert result.end_date is None

    def test_parse_dates_with_timezone(self) -> None:
        """Test parsing dates with timezone information."""
        # Arrange
        json_data = {
            "aid": 12345,
            "title": "Test Anime",
            "start_date": "2023-01-15T00:00:00Z",
            "end_date": "2023-03-31T23:59:59Z",
        }

        # Act
        result = parse_anidb_json(json_data)

        # Assert
        assert result.air_date is not None
        assert result.end_date is not None


class TestParseAnidbJsonArrayFields:
    """Tests for array field extraction (titles, tags, relations)."""

    def test_extract_alternate_titles_from_titles_array(self) -> None:
        """Test extraction of alternate titles from titles array."""
        # Arrange
        json_data = {
            "aid": 12345,
            "title": "Test Anime",
            "titles": [
                {"title": "Test Anime", "type": "main"},
                {"title": "テストアニメ", "type": "official"},
                {"title": "Test Anime Alt", "type": "synonym"},
            ],
        }

        # Act
        result = parse_anidb_json(json_data)

        # Assert
        # Should extract non-main titles
        assert "テストアニメ" in result.title_alts
        assert "Test Anime Alt" in result.title_alts
        assert len(result.title_alts) == 2
        # Should not include main title in alts
        assert "Test Anime" not in result.title_alts

    def test_extract_tags_from_tags_array(self) -> None:
        """Test extraction of tag names from tags array."""
        # Arrange
        json_data = {
            "aid": 12345,
            "title": "Test Anime",
            "tags": [
                {"name": "action", "weight": 600},
                {"name": "sci-fi", "weight": 400},
                {"name": "mecha", "weight": 300},
            ],
        }

        # Act
        result = parse_anidb_json(json_data)

        # Assert
        assert "action" in result.tags
        assert "sci-fi" in result.tags
        assert "mecha" in result.tags
        assert len(result.tags) == 3

    def test_serialize_relations_and_similar_arrays(self) -> None:
        """Test serialization of relations and similar arrays to JSON strings."""
        # Arrange
        relations_data = [
            {"id": 123, "type": "sequel", "title": "Test Anime 2"},
            {"id": 124, "type": "prequel", "title": "Test Anime 0"},
        ]
        similar_data = [
            {"id": 456, "approval": 85, "total": 100},
            {"id": 789, "approval": 92, "total": 120},
        ]
        json_data = {
            "aid": 12345,
            "title": "Test Anime",
            "related_anime": relations_data,
            "similar_anime": similar_data,
        }

        # Act
        result = parse_anidb_json(json_data)

        # Assert
        # Should be serialized as JSON strings
        assert isinstance(result.relations, str)
        assert isinstance(result.similar, str)
        # Should be valid JSON
        parsed_relations = json.loads(result.relations)
        parsed_similar = json.loads(result.similar)
        assert len(parsed_relations) == 2
        assert len(parsed_similar) == 2
        assert parsed_relations[0]["id"] == 123
        assert parsed_similar[0]["approval"] == 85


class TestParseAnidbJsonRatings:
    """Tests for ratings extraction and conversion."""

    def test_parse_ratings_dict(self) -> None:
        """Test parsing ratings from ratings dict."""
        # Arrange
        json_data = {
            "aid": 12345,
            "title": "Test Anime",
            "ratings": {
                "permanent": 8.5,
                "permanent_count": 1000,
                "review": 7.5,
                "review_count": 50,
            },
        }

        # Act
        result = parse_anidb_json(json_data)

        # Assert
        assert result.rating == 850  # 8.5 * 100
        assert result.vote_count == 1000
        assert result.avg_review_rating == 750  # 7.5 * 100
        assert result.review_count == 50

    def test_parse_missing_ratings_uses_defaults(self) -> None:
        """Test that missing ratings dict uses default values."""
        # Arrange
        json_data = {
            "aid": 12345,
            "title": "Test Anime",
        }

        # Act
        result = parse_anidb_json(json_data)

        # Assert
        assert result.rating == 0
        assert result.vote_count == 0
        assert result.avg_review_rating == 0
        assert result.review_count == 0

    def test_parse_empty_ratings_dict(self) -> None:
        """Test parsing empty ratings dict."""
        # Arrange
        json_data = {
            "aid": 12345,
            "title": "Test Anime",
            "ratings": {},
        }

        # Act
        result = parse_anidb_json(json_data)

        # Assert
        assert result.rating == 0
        assert result.vote_count == 0


class TestParseAnidbJsonExternalIds:
    """Tests for external ID extraction."""

    def test_parse_external_ids(self) -> None:
        """Test extraction of external IDs."""
        # Arrange
        json_data = {
            "aid": 12345,
            "title": "Test Anime",
            "ann_id": 98765,
            "crunchyroll_id": "test-anime",
            "wikipedia_id": "Test_Anime",
        }

        # Act
        result = parse_anidb_json(json_data)

        # Assert
        assert result.ann_id == 98765
        assert result.crunchyroll_id == "test-anime"
        assert result.wikipedia_id == "Test_Anime"

    def test_parse_missing_external_ids(self) -> None:
        """Test that missing external IDs are None."""
        # Arrange
        json_data = {
            "aid": 12345,
            "title": "Test Anime",
        }

        # Act
        result = parse_anidb_json(json_data)

        # Assert
        assert result.ann_id is None
        assert result.crunchyroll_id is None
        assert result.wikipedia_id is None
