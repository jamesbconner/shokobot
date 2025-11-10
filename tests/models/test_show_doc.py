"""Tests for ShowDoc Pydantic model validation and behavior.

This module tests the ShowDoc model's validation logic, field constraints,
data cleaning, and conversion to LangChain Document format.
"""

from datetime import datetime
from typing import Any

import pytest
from langchain_core.documents import Document
from pydantic import ValidationError

from models.show_doc import ShowDoc


def test_show_doc_creation_valid(sample_show_doc_dict: dict[str, Any]) -> None:
    """Test creating ShowDoc with valid data.

    Verifies that the ShowDoc model accepts valid data with all fields
    properly populated and returns a valid instance.
    """
    # Act
    doc = ShowDoc(**sample_show_doc_dict)

    # Assert
    assert doc.anime_id == "123"
    assert doc.anidb_anime_id == 456
    assert doc.title_main == "Test Anime"
    assert len(doc.title_alts) == 3
    assert doc.description == "A test anime description with HTML tags."
    assert len(doc.tags) == 4
    assert doc.episode_count_normal == 24
    assert doc.episode_count_special == 2
    assert doc.begin_year == 2020
    assert doc.end_year == 2020
    assert doc.rating == 850
    assert doc.vote_count == 1000


def test_show_doc_required_fields() -> None:
    """Test that required fields are enforced.

    Verifies that ShowDoc raises ValidationError when required fields
    (anime_id, anidb_anime_id, title_main) are missing.
    """
    # Arrange: data missing anime_id
    invalid_data = {
        "anidb_anime_id": 456,
        "title_main": "Test Anime",
    }

    # Act & Assert: missing anime_id
    with pytest.raises(ValidationError, match="anime_id"):
        ShowDoc(**invalid_data)

    # Arrange: data missing anidb_anime_id
    invalid_data = {
        "anime_id": "123",
        "title_main": "Test Anime",
    }

    # Act & Assert: missing anidb_anime_id
    with pytest.raises(ValidationError, match="anidb_anime_id"):
        ShowDoc(**invalid_data)

    # Arrange: data missing title_main
    invalid_data = {
        "anime_id": "123",
        "anidb_anime_id": 456,
    }

    # Act & Assert: missing title_main
    with pytest.raises(ValidationError, match="title_main"):
        ShowDoc(**invalid_data)


def test_show_doc_title_alts_cleaning() -> None:
    """Test empty string removal from title_alts.

    Verifies that the ShowDoc model removes empty strings and
    whitespace-only strings from the title_alts list.
    """
    # Arrange: data with empty strings in title_alts
    data = {
        "anime_id": "123",
        "anidb_anime_id": 456,
        "title_main": "Test Anime",
        "title_alts": ["Valid Title", "", "  ", "Another Title", "   "],
    }

    # Act
    doc = ShowDoc(**data)

    # Assert: empty strings removed, whitespace trimmed
    assert len(doc.title_alts) == 2
    assert "Valid Title" in doc.title_alts
    assert "Another Title" in doc.title_alts
    assert "" not in doc.title_alts
    assert "  " not in doc.title_alts


def test_show_doc_tags_cleaning() -> None:
    """Test empty string removal from tags.

    Verifies that the ShowDoc model removes empty strings and
    whitespace-only strings from the tags list.
    """
    # Arrange: data with empty strings in tags
    data = {
        "anime_id": "123",
        "anidb_anime_id": 456,
        "title_main": "Test Anime",
        "tags": ["action", "", "  ", "comedy", "   ", "drama"],
    }

    # Act
    doc = ShowDoc(**data)

    # Assert: empty strings removed, whitespace trimmed
    assert len(doc.tags) == 3
    assert "action" in doc.tags
    assert "comedy" in doc.tags
    assert "drama" in doc.tags
    assert "" not in doc.tags
    assert "  " not in doc.tags


def test_show_doc_year_validation() -> None:
    """Test end_year >= begin_year constraint.

    Verifies that the ShowDoc model raises ValidationError when
    end_year is before begin_year.
    """
    # Arrange: data with end_year before begin_year
    invalid_data = {
        "anime_id": "123",
        "anidb_anime_id": 456,
        "title_main": "Test Anime",
        "begin_year": 2021,
        "end_year": 2020,  # Invalid: before begin_year
    }

    # Act & Assert
    with pytest.raises(ValidationError, match="end_year.*begin_year"):
        ShowDoc(**invalid_data)

    # Arrange: valid data with end_year equal to begin_year
    valid_data = {
        "anime_id": "123",
        "anidb_anime_id": 456,
        "title_main": "Test Anime",
        "begin_year": 2020,
        "end_year": 2020,
    }

    # Act
    doc = ShowDoc(**valid_data)

    # Assert: equal years are valid
    assert doc.begin_year == 2020
    assert doc.end_year == 2020

    # Arrange: valid data with end_year after begin_year
    valid_data["end_year"] = 2021

    # Act
    doc = ShowDoc(**valid_data)

    # Assert: end_year after begin_year is valid
    assert doc.begin_year == 2020
    assert doc.end_year == 2021


def test_show_doc_to_langchain_doc(sample_show_doc_dict: dict[str, Any]) -> None:
    """Test LangChain Document conversion.

    Verifies that ShowDoc.to_langchain_doc() produces a valid
    LangChain Document with proper page_content and metadata.
    """
    # Arrange
    doc = ShowDoc(**sample_show_doc_dict)

    # Act
    langchain_doc = doc.to_langchain_doc()

    # Assert: returns Document instance
    assert isinstance(langchain_doc, Document)

    # Assert: page_content contains key information
    assert "Test Anime" in langchain_doc.page_content
    assert "A test anime description" in langchain_doc.page_content
    assert "action" in langchain_doc.page_content or "Tags:" in langchain_doc.page_content
    assert "Episodes: 24" in langchain_doc.page_content
    assert "2020" in langchain_doc.page_content

    # Assert: metadata contains required fields
    assert langchain_doc.metadata["anime_id"] == "123"
    assert langchain_doc.metadata["anidb_anime_id"] == 456
    assert langchain_doc.metadata["title_main"] == "Test Anime"
    assert langchain_doc.metadata["episode_count_normal"] == 24
    assert langchain_doc.metadata["begin_year"] == 2020


def test_show_doc_with_minimal_data() -> None:
    """Test ShowDoc with minimal required fields.

    Verifies that ShowDoc handles minimal data (only required fields)
    correctly with appropriate defaults for optional fields.
    """
    # Arrange: minimal required data
    minimal_data = {
        "anime_id": "999",
        "anidb_anime_id": 888,
        "title_main": "Minimal Anime",
    }

    # Act
    doc = ShowDoc(**minimal_data)

    # Assert: required fields set
    assert doc.anime_id == "999"
    assert doc.anidb_anime_id == 888
    assert doc.title_main == "Minimal Anime"

    # Assert: optional fields have defaults
    assert doc.title_alts == []
    assert doc.description == ""
    assert doc.tags == []
    assert doc.episode_count_normal == 0
    assert doc.episode_count_special == 0
    assert doc.air_date is None
    assert doc.end_date is None
    assert doc.begin_year is None
    assert doc.end_year is None
    assert doc.rating == 0
    assert doc.vote_count == 0
    assert doc.avg_review_rating == 0
    assert doc.review_count == 0
    assert doc.ann_id is None
    assert doc.crunchyroll_id is None
    assert doc.wikipedia_id is None
    assert doc.relations == "[]"
    assert doc.similar == "[]"


def test_show_doc_with_full_data(sample_show_doc_dict: dict[str, Any]) -> None:
    """Test ShowDoc with all fields populated.

    Verifies that ShowDoc handles complete data with all fields
    populated correctly.
    """
    # Act
    doc = ShowDoc(**sample_show_doc_dict)

    # Assert: all fields properly set
    assert doc.anime_id == "123"
    assert doc.anidb_anime_id == 456
    assert doc.title_main == "Test Anime"
    assert len(doc.title_alts) == 3
    assert doc.description != ""
    assert len(doc.tags) == 4
    assert doc.episode_count_normal == 24
    assert doc.episode_count_special == 2
    assert isinstance(doc.air_date, datetime)
    assert isinstance(doc.end_date, datetime)
    assert doc.begin_year == 2020
    assert doc.end_year == 2020
    assert doc.rating == 850
    assert doc.vote_count == 1000
    assert doc.avg_review_rating == 800
    assert doc.review_count == 50
    assert doc.ann_id == 12345
    assert doc.crunchyroll_id == "test-anime"
    assert doc.wikipedia_id == "Test_Anime"
    assert doc.relations == "[]"
    assert doc.similar == "[]"
