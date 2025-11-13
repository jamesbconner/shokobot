"""Tests for similarity_utils module."""

from typing import Any
from unittest.mock import Mock

import pytest
from langchain_core.documents import Document

from utils.similarity_utils import (
    filter_by_score,
    get_score_statistics,
    print_score_table,
    search_with_scores,
)


@pytest.fixture
def mock_context() -> Any:
    """Create mock application context.

    Returns:
        Mock context with vectorstore.
    """
    ctx = Mock()
    ctx.vectorstore = Mock()
    return ctx


@pytest.fixture
def sample_results() -> Any:
    """Create sample search results with distance scores.

    Returns:
        List of (Document, distance) tuples.
    """
    return [
        (
            Document(page_content="Content 1", metadata={"title_main": "Anime 1", "anime_id": "1"}),
            0.2,
        ),
        (
            Document(page_content="Content 2", metadata={"title_main": "Anime 2", "anime_id": "2"}),
            0.4,
        ),
        (
            Document(page_content="Content 3", metadata={"title_main": "Anime 3", "anime_id": "3"}),
            0.6,
        ),
        (
            Document(page_content="Content 4", metadata={"title_main": "Anime 4", "anime_id": "4"}),
            0.8,
        ),
        (
            Document(page_content="Content 5", metadata={"title_main": "Anime 5", "anime_id": "5"}),
            1.0,
        ),
    ]


class TestSearchWithScores:
    """Tests for search_with_scores function."""

    def test_search_with_scores_returns_results(self, mock_context) -> None:
        """Test that search_with_scores returns results from vectorstore.

        Args:
            mock_context: Mock application context.
        """
        # Arrange
        expected_results = [
            (Document(page_content="Test", metadata={"title_main": "Test Anime"}), 0.3)
        ]
        mock_context.vectorstore.similarity_search_with_score.return_value = expected_results

        # Act
        results = search_with_scores("test query", mock_context, k=5, log_results=False)

        # Assert
        assert results == expected_results
        mock_context.vectorstore.similarity_search_with_score.assert_called_once_with(
            "test query", k=5
        )

    def test_search_with_scores_with_logging(self, mock_context, caplog) -> None:
        """Test that search_with_scores logs results when enabled.

        Args:
            mock_context: Mock application context.
            caplog: Pytest log capture fixture.
        """
        # Arrange
        results = [
            (
                Document(
                    page_content="Test", metadata={"title_main": "Test Anime", "anime_id": "123"}
                ),
                0.3,
            )
        ]
        mock_context.vectorstore.similarity_search_with_score.return_value = results

        # Act
        import logging

        with caplog.at_level(logging.INFO):
            search_with_scores("test query", mock_context, k=5, log_results=True)

        # Assert
        assert "test query" in caplog.text
        assert "Test Anime" in caplog.text
        assert "0.3" in caplog.text

    def test_search_with_scores_respects_k_parameter(self, mock_context) -> None:
        """Test that search_with_scores passes k parameter correctly.

        Args:
            mock_context: Mock application context.
        """
        # Arrange
        mock_context.vectorstore.similarity_search_with_score.return_value = []

        # Act
        search_with_scores("test", mock_context, k=20, log_results=False)

        # Assert
        mock_context.vectorstore.similarity_search_with_score.assert_called_once_with("test", k=20)


class TestGetScoreStatistics:
    """Tests for get_score_statistics function."""

    def test_get_score_statistics_with_results(self, sample_results) -> None:
        """Test statistics calculation with valid results.

        Args:
            sample_results: Sample search results.
        """
        # Act
        stats = get_score_statistics(sample_results)

        # Assert
        assert stats["min"] == 0.2  # Best (lowest)
        assert stats["max"] == 1.0  # Worst (highest)
        assert stats["avg"] == 0.6  # Average
        assert stats["median"] == 0.6  # Median

    def test_get_score_statistics_empty_results(self) -> None:
        """Test statistics calculation with empty results."""
        # Act
        stats = get_score_statistics([])

        # Assert
        assert stats["min"] == 0.0
        assert stats["max"] == 0.0
        assert stats["avg"] == 0.0
        assert stats["median"] == 0.0

    def test_get_score_statistics_single_result(self) -> None:
        """Test statistics calculation with single result."""
        # Arrange
        results = [(Document(page_content="Test"), 0.5)]

        # Act
        stats = get_score_statistics(results)

        # Assert
        assert stats["min"] == 0.5
        assert stats["max"] == 0.5
        assert stats["avg"] == 0.5
        assert stats["median"] == 0.5

    def test_get_score_statistics_median_calculation(self) -> None:
        """Test median calculation with even number of results."""
        # Arrange
        results = [
            (Document(page_content="Test 1"), 0.2),
            (Document(page_content="Test 2"), 0.4),
            (Document(page_content="Test 3"), 0.6),
            (Document(page_content="Test 4"), 0.8),
        ]

        # Act
        stats = get_score_statistics(results)

        # Assert
        # Median of sorted [0.2, 0.4, 0.6, 0.8] is 0.6 (element at index 2)
        assert stats["median"] == 0.6


class TestFilterByScore:
    """Tests for filter_by_score function."""

    def test_filter_by_score_keeps_good_matches(self, sample_results) -> None:
        """Test that filter keeps results with distance <= threshold.

        Args:
            sample_results: Sample search results.
        """
        # Act
        filtered = filter_by_score(sample_results, max_distance=0.5)

        # Assert
        assert len(filtered) == 2  # Only 0.2 and 0.4 are <= 0.5
        assert filtered[0][1] == 0.2
        assert filtered[1][1] == 0.4

    def test_filter_by_score_strict_threshold(self, sample_results) -> None:
        """Test filtering with strict threshold.

        Args:
            sample_results: Sample search results.
        """
        # Act
        filtered = filter_by_score(sample_results, max_distance=0.3)

        # Assert
        assert len(filtered) == 1  # Only 0.2 is <= 0.3
        assert filtered[0][1] == 0.2

    def test_filter_by_score_lenient_threshold(self, sample_results) -> None:
        """Test filtering with lenient threshold.

        Args:
            sample_results: Sample search results.
        """
        # Act
        filtered = filter_by_score(sample_results, max_distance=1.5)

        # Assert
        assert len(filtered) == 5  # All results are <= 1.5
        assert len(filtered) == len(sample_results)

    def test_filter_by_score_no_matches(self, sample_results) -> None:
        """Test filtering when no results meet threshold.

        Args:
            sample_results: Sample search results.
        """
        # Act
        filtered = filter_by_score(sample_results, max_distance=0.1)

        # Assert
        assert len(filtered) == 0

    def test_filter_by_score_empty_input(self) -> None:
        """Test filtering with empty input."""
        # Act
        filtered = filter_by_score([], max_distance=0.5)

        # Assert
        assert len(filtered) == 0


class TestPrintScoreTable:
    """Tests for print_score_table function."""

    def test_print_score_table_displays_results(self, sample_results, capsys) -> None:
        """Test that print_score_table displays results correctly.

        Args:
            sample_results: Sample search results.
            capsys: Pytest stdout/stderr capture fixture.
        """
        # Act
        print_score_table(sample_results, max_results=3)
        captured = capsys.readouterr()

        # Assert
        assert "Rank" in captured.out
        assert "Distance" in captured.out
        assert "Title" in captured.out
        assert "Lower distance = better match" in captured.out
        assert "Anime 1" in captured.out
        assert "Anime 2" in captured.out
        assert "Anime 3" in captured.out
        assert "0.2000" in captured.out
        assert "0.4000" in captured.out

    def test_print_score_table_respects_max_results(self, sample_results, capsys) -> None:
        """Test that print_score_table respects max_results parameter.

        Args:
            sample_results: Sample search results.
            capsys: Pytest stdout/stderr capture fixture.
        """
        # Act
        print_score_table(sample_results, max_results=2)
        captured = capsys.readouterr()

        # Assert
        assert "Anime 1" in captured.out
        assert "Anime 2" in captured.out
        assert "Anime 3" not in captured.out
        assert "and 3 more results" in captured.out

    def test_print_score_table_shows_statistics(self, sample_results, capsys) -> None:
        """Test that print_score_table shows statistics.

        Args:
            sample_results: Sample search results.
            capsys: Pytest stdout/stderr capture fixture.
        """
        # Act
        print_score_table(sample_results, max_results=5)
        captured = capsys.readouterr()

        # Assert
        assert "Distance Statistics" in captured.out
        assert "Best (lowest)" in captured.out
        assert "Worst (highest)" in captured.out
        assert "Average" in captured.out
        assert "0.2000" in captured.out  # Best
        assert "1.0000" in captured.out  # Worst

    def test_print_score_table_empty_results(self, capsys) -> None:
        """Test print_score_table with empty results."""
        # Act
        print_score_table([], max_results=10)
        captured = capsys.readouterr()

        # Assert
        assert "No results found" in captured.out

    def test_print_score_table_handles_missing_metadata(self, capsys) -> None:
        """Test that print_score_table handles missing metadata gracefully."""
        # Arrange
        results = [(Document(page_content="Test", metadata={}), 0.3)]

        # Act
        print_score_table(results, max_results=10)
        captured = capsys.readouterr()

        # Assert
        assert "Unknown" in captured.out  # Default title
        assert "N/A" in captured.out  # Default anime_id
        assert "0.3000" in captured.out


class TestDistanceScoreLogic:
    """Tests to verify distance score logic (lower = better)."""

    def test_distance_scores_lower_is_better(self) -> None:
        """Test that lower distance scores are treated as better matches."""
        # Arrange
        results = [
            (Document(page_content="Excellent", metadata={"title_main": "Excellent"}), 0.1),
            (Document(page_content="Good", metadata={"title_main": "Good"}), 0.5),
            (Document(page_content="Poor", metadata={"title_main": "Poor"}), 1.2),
        ]

        # Act
        stats = get_score_statistics(results)
        filtered_excellent = filter_by_score(results, max_distance=0.3)
        filtered_good = filter_by_score(results, max_distance=0.7)

        # Assert
        assert stats["min"] == 0.1  # Best score is lowest
        assert stats["max"] == 1.2  # Worst score is highest
        assert len(filtered_excellent) == 1  # Only 0.1 <= 0.3
        assert len(filtered_good) == 2  # 0.1 and 0.5 <= 0.7
        assert filtered_excellent[0][0].metadata["title_main"] == "Excellent"

    def test_threshold_comparison_uses_less_than_or_equal(self) -> None:
        """Test that threshold comparison uses <= (not >=)."""
        # Arrange
        results = [
            (Document(page_content="Test 1"), 0.5),
            (Document(page_content="Test 2"), 0.7),
            (Document(page_content="Test 3"), 0.9),
        ]

        # Act
        # With threshold 0.7, should keep 0.5 and 0.7 (both <= 0.7)
        filtered = filter_by_score(results, max_distance=0.7)

        # Assert
        assert len(filtered) == 2
        assert filtered[0][1] == 0.5
        assert filtered[1][1] == 0.7
        # 0.9 should be excluded because 0.9 > 0.7
