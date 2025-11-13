"""Shared pytest fixtures for ShokoBot testing infrastructure.

This module provides reusable fixtures for testing all components of the
ShokoBot anime recommendation system. Fixtures include mock services,
sample data, and temporary file utilities.
"""

import json
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest


@pytest.fixture
def mock_config() -> Mock:
    """Mock ConfigService with predefined configuration values.

    Provides a Mock object that simulates ConfigService behavior with
    test-appropriate configuration values. The mock's get() method
    returns values from a predefined configuration dictionary.

    Returns:
        Mock object with get() method returning test configuration values.

    Examples:
        >>> def test_example(mock_config: Mock) -> None:
        ...     assert mock_config.get("chroma.persist_directory") == "./.test_chroma"
    """
    mock = Mock()
    test_config = {
        "chroma": {
            "persist_directory": "./.test_chroma",
            "collection_name": "test_collection",
        },
        "data": {
            "shows_json": "test_data.json",
        },
        "openai": {
            "model": "gpt-5-nano",
            "embedding_model": "text-embedding-3-small",
            "reasoning_effort": "medium",
            "output_verbosity": "medium",
            "max_output_tokens": 4096,
        },
        "ingest": {
            "batch_size": 10,
        },
        "logging": {
            "level": "INFO",
        },
    }

    def mock_get(path: str, default: Any = None) -> Any:
        """Mock implementation of ConfigService.get() method.

        Args:
            path: Dot-separated path to config value.
            default: Default value if path doesn't exist.

        Returns:
            Configuration value at the specified path, or default if not found.
        """
        parts = path.split(".")
        ref = test_config

        for part in parts:
            if not isinstance(ref, dict) or part not in ref:
                return default
            ref = ref[part]  # type: ignore[assignment]

        return ref

    mock.get.side_effect = mock_get
    mock.as_dict.return_value = test_config
    return mock


@pytest.fixture
def mock_context(mock_config: Mock) -> Mock:
    """Mock AppContext with mocked dependencies.

    Provides a Mock object that simulates AppContext behavior with
    mocked vectorstore and rag_chain properties. Useful for testing
    services that depend on AppContext without initializing real
    external dependencies.

    Args:
        mock_config: Mock ConfigService fixture.

    Returns:
        Mock object with config, vectorstore, and rag_chain properties.

    Examples:
        >>> def test_example(mock_context: Mock) -> None:
        ...     assert mock_context.config is not None
        ...     assert mock_context.vectorstore is not None
    """
    mock = Mock()
    mock.config = mock_config

    # Mock vectorstore with common methods
    mock_vectorstore = Mock()
    mock_vectorstore.add_documents.return_value = ["id1", "id2", "id3"]
    mock_vectorstore.as_retriever.return_value = Mock()
    mock.vectorstore = mock_vectorstore

    # Mock RAG chain
    mock_rag_chain = Mock()
    mock_rag_chain.return_value = ("Test answer", [])
    mock.rag_chain = mock_rag_chain

    # Mock reset methods
    mock.reset_vectorstore = Mock()
    mock.reset_rag_chain = Mock()
    mock.reset_all = Mock()

    return mock


@pytest.fixture
def sample_anime_data() -> dict[str, Any]:
    """Sample raw anime data matching JSON input format.

    Provides a dictionary representing a single anime record as it would
    appear in the Shoko JSON export format. Useful for testing data
    parsing and transformation logic.

    Returns:
        Dictionary with anime data in Shoko JSON format.

    Examples:
        >>> def test_example(sample_anime_data: dict[str, Any]) -> None:
        ...     assert sample_anime_data["AnimeID"] == "123"
        ...     assert sample_anime_data["MainTitle"] == "Test Anime"
    """
    return {
        "AnimeID": "123",
        "AniDB_AnimeID": 456,
        "MainTitle": "Test Anime",
        "AllTitles": "Test Anime|テストアニメ|Test Anime Title",
        "Description": "<p>A test anime description with <b>HTML</b> tags.</p>",
        "AllTags": "action|comedy|test|drama",
        "EpisodeCountNormal": 24,
        "EpisodeCountSpecial": 2,
        "AirDate": "2020-01-15 00:00:00",
        "EndDate": "2020-06-30 00:00:00",
        "BeginYear": 2020,
        "EndYear": 2020,
        "Rating": 850,
        "VoteCount": 1000,
        "AvgReviewRating": 800,
        "ReviewCount": 50,
        "ANNID": 12345,
        "CrunchyrollID": "test-anime",
        "Wikipedia_ID": "Test_Anime",
        "relations": "[]",
        "similar": "[]",
    }


@pytest.fixture
def sample_show_doc_dict() -> dict[str, Any]:
    """Sample ShowDoc data as dictionary.

    Provides a dictionary representing a ShowDoc instance in dictionary
    form. Useful for testing ShowDoc model validation and creation.

    Returns:
        Dictionary with ShowDoc fields and values.

    Examples:
        >>> def test_example(sample_show_doc_dict: dict[str, Any]) -> None:
        ...     doc = ShowDoc(**sample_show_doc_dict)
        ...     assert doc.anime_id == "123"
    """
    return {
        "anime_id": "123",
        "anidb_anime_id": 456,
        "title_main": "Test Anime",
        "title_alts": ["Test Anime", "テストアニメ", "Test Anime Title"],
        "description": "A test anime description with HTML tags.",
        "tags": ["action", "comedy", "test", "drama"],
        "episode_count_normal": 24,
        "episode_count_special": 2,
        "air_date": datetime(2020, 1, 15, 0, 0, 0),
        "end_date": datetime(2020, 6, 30, 0, 0, 0),
        "begin_year": 2020,
        "end_year": 2020,
        "rating": 850,
        "vote_count": 1000,
        "avg_review_rating": 800,
        "review_count": 50,
        "ann_id": 12345,
        "crunchyroll_id": "test-anime",
        "wikipedia_id": "Test_Anime",
        "relations": "[]",
        "similar": "[]",
    }


@pytest.fixture
def temp_config_file(tmp_path: Path) -> Path:
    """Create temporary config file for testing.

    Creates a temporary JSON configuration file with test-appropriate
    values. The file is automatically cleaned up after the test completes.

    Args:
        tmp_path: pytest's temporary directory fixture.

    Returns:
        Path to the temporary config.json file.

    Examples:
        >>> def test_example(temp_config_file: Path) -> None:
        ...     config = ConfigService(str(temp_config_file))
        ...     assert config.get("chroma.persist_directory") == "./.test_chroma"
    """
    config_data = {
        "chroma": {
            "persist_directory": "./.test_chroma",
            "collection_name": "test_collection",
        },
        "data": {
            "shows_json": "test_data.json",
        },
        "openai": {
            "model": "gpt-5-nano",
            "embedding_model": "text-embedding-3-small",
            "reasoning_effort": "medium",
            "output_verbosity": "medium",
            "max_output_tokens": 4096,
        },
        "ingest": {
            "batch_size": 10,
        },
        "logging": {
            "level": "INFO",
        },
    }

    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps(config_data, indent=2), encoding="utf-8")
    return config_file


@pytest.fixture
def sample_json_file(tmp_path: Path, sample_anime_data: dict[str, Any]) -> Path:
    """Create temporary JSON file with sample anime data.

    Creates a temporary JSON file containing sample anime data in the
    Shoko export format. Useful for testing ingestion workflows.

    Args:
        tmp_path: pytest's temporary directory fixture.
        sample_anime_data: Sample anime data fixture.

    Returns:
        Path to the temporary JSON file.

    Examples:
        >>> def test_example(sample_json_file: Path) -> None:
        ...     with sample_json_file.open() as f:
        ...         data = json.load(f)
        ...     assert "AniDB_Anime" in data
    """
    json_data = {"AniDB_Anime": [sample_anime_data]}
    json_file = tmp_path / "test_anime.json"
    json_file.write_text(json.dumps(json_data, indent=2), encoding="utf-8")
    return json_file


@pytest.fixture
def mock_vectorstore() -> Mock:
    """Mock Chroma vectorstore instance.

    Provides a Mock object that simulates Chroma vectorstore behavior
    with common methods like add_documents, as_retriever, etc.

    Returns:
        Mock object simulating Chroma vectorstore.

    Examples:
        >>> def test_example(mock_vectorstore: Mock) -> None:
        ...     ids = mock_vectorstore.add_documents([doc1, doc2])
        ...     assert len(ids) == 2
    """
    mock = Mock()
    mock.add_documents.return_value = ["id1", "id2", "id3"]
    mock.as_retriever.return_value = Mock()
    mock.similarity_search.return_value = []
    mock.similarity_search_with_score.return_value = []
    return mock


@pytest.fixture
def mock_rag_chain() -> Callable[[str], tuple[str, list]]:
    """Mock RAG chain callable.

    Provides a Mock callable that simulates RAG chain behavior,
    returning a test answer and empty context list.

    Returns:
        Mock callable that takes a question and returns (answer, context).

    Examples:
        >>> def test_example(mock_rag_chain: Callable) -> None:
        ...     answer, context = mock_rag_chain("What is this anime about?")
        ...     assert isinstance(answer, str)
        ...     assert isinstance(context, list)
    """
    mock = Mock()
    mock.return_value = ("This is a test answer about anime.", [])
    return mock
