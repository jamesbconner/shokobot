"""Tests for text processing utility functions.

This module tests text cleaning, HTML tag removal, whitespace normalization,
and pipe-separated string splitting functionality.
"""

import pytest

from utils.text_utils import clean_description, split_pipe


class TestCleanDescription:
    """Tests for clean_description function."""

    def test_clean_description_html_removal(self) -> None:
        """Test that BBCode tags are removed from description text."""
        # Arrange
        input_text = "A test anime description with [b]BBCode[/b] tags."
        expected = "A test anime description with BBCode tags."

        # Act
        result = clean_description(input_text)

        # Assert
        assert result == expected

    @pytest.mark.parametrize(
        "input_text,expected",
        [
            ("[i]Italic text[/i]", "Italic text"),
            ("[b]Bold text[/b]", "Bold text"),
            ("[u]Underlined text[/u]", "Underlined text"),
            ("[spoiler]Hidden content[/spoiler]", "Hidden content"),
            ("[quote]Quoted text[/quote]", "Quoted text"),
            ("[code]Code block[/code]", "Code block"),
            ("Mixed [b]bold[/b] and [i]italic[/i]", "Mixed bold and italic"),
            ("[I]Case insensitive[/I]", "Case insensitive"),
        ],
    )
    def test_clean_description_various_tags(self, input_text: str, expected: str) -> None:
        """Test removal of various BBCode tags."""
        # Act
        result = clean_description(input_text)

        # Assert
        assert result == expected

    def test_clean_description_special_chars(self) -> None:
        """Test that special characters are handled correctly."""
        # Arrange
        input_text = "Text with special chars: & < > \" '"
        expected = "Text with special chars: & < > \" '"

        # Act
        result = clean_description(input_text)

        # Assert
        assert result == expected

    def test_clean_description_whitespace(self) -> None:
        """Test that multiple spaces are normalized to single space."""
        # Arrange
        input_text = "Text   with    multiple     spaces"
        expected = "Text with multiple spaces"

        # Act
        result = clean_description(input_text)

        # Assert
        assert result == expected

    @pytest.mark.parametrize(
        "input_text,expected",
        [
            ("  Leading and trailing  ", "Leading and trailing"),
            ("\tTabs\tand\tspaces\t", "Tabs and spaces"),
            ("Text with tabs", "Text with tabs"),
        ],
    )
    def test_clean_description_whitespace_variations(self, input_text: str, expected: str) -> None:
        """Test whitespace normalization with various whitespace types."""
        # Act
        result = clean_description(input_text)

        # Assert
        assert result == expected

    def test_clean_description_empty_string(self) -> None:
        """Test that empty string returns empty string."""
        # Act
        result = clean_description("")

        # Assert
        assert result == ""

    def test_clean_description_none(self) -> None:
        """Test that None input returns empty string."""
        # Act
        result = clean_description(None)

        # Assert
        assert result == ""

    def test_clean_description_only_tags(self) -> None:
        """Test that string with only BBCode tags returns empty string."""
        # Arrange
        input_text = "[i][/i][b][/b][u][/u]"

        # Act
        result = clean_description(input_text)

        # Assert
        assert result == ""

    def test_clean_description_mixed_content(self) -> None:
        """Test cleaning description with BBCode tags and whitespace."""
        # Arrange
        input_text = "  [b]Bold[/b]   text   with   [i]italic[/i]  "
        expected = "Bold text with italic"

        # Act
        result = clean_description(input_text)

        # Assert
        assert result == expected


class TestSplitPipe:
    """Tests for split_pipe function."""

    def test_split_pipe_basic(self) -> None:
        """Test basic pipe-separated string splitting."""
        # Arrange
        input_text = "action|comedy|drama"
        expected = ["action", "comedy", "drama"]

        # Act
        result = split_pipe(input_text)

        # Assert
        assert result == expected

    def test_split_pipe_empty(self) -> None:
        """Test that empty strings are removed from result."""
        # Arrange
        input_text = "action||comedy|||drama"
        expected = ["action", "comedy", "drama"]

        # Act
        result = split_pipe(input_text)

        # Assert
        assert result == expected

    def test_split_pipe_whitespace(self) -> None:
        """Test that whitespace is trimmed from each element."""
        # Arrange
        input_text = "  action  |  comedy  |  drama  "
        expected = ["action", "comedy", "drama"]

        # Act
        result = split_pipe(input_text)

        # Assert
        assert result == expected

    @pytest.mark.parametrize(
        "input_text,expected",
        [
            ("action | comedy | drama", ["action", "comedy", "drama"]),
            ("action|comedy|drama", ["action", "comedy", "drama"]),
            ("  action  |comedy|  drama  ", ["action", "comedy", "drama"]),
            ("action  |  comedy  |  drama", ["action", "comedy", "drama"]),
        ],
    )
    def test_split_pipe_whitespace_variations(self, input_text: str, expected: list[str]) -> None:
        """Test whitespace handling with various spacing patterns."""
        # Act
        result = split_pipe(input_text)

        # Assert
        assert result == expected

    def test_split_pipe_empty_string(self) -> None:
        """Test that empty string returns empty list."""
        # Act
        result = split_pipe("")

        # Assert
        assert result == []

    def test_split_pipe_none(self) -> None:
        """Test that None input returns empty list."""
        # Act
        result = split_pipe(None)

        # Assert
        assert result == []

    def test_split_pipe_single_element(self) -> None:
        """Test splitting string with single element."""
        # Arrange
        input_text = "action"
        expected = ["action"]

        # Act
        result = split_pipe(input_text)

        # Assert
        assert result == expected

    def test_split_pipe_deduplication(self) -> None:
        """Test that duplicate values are removed (case-insensitive)."""
        # Arrange
        input_text = "action|Action|ACTION|comedy|Comedy"
        expected = ["action", "comedy"]

        # Act
        result = split_pipe(input_text)

        # Assert
        assert result == expected

    def test_split_pipe_preserves_case(self) -> None:
        """Test that original case is preserved for first occurrence."""
        # Arrange
        input_text = "Action|action|Comedy|COMEDY"
        expected = ["Action", "Comedy"]

        # Act
        result = split_pipe(input_text)

        # Assert
        assert result == expected

    def test_split_pipe_only_whitespace(self) -> None:
        """Test that string with only whitespace returns empty list."""
        # Arrange
        input_text = "   |   |   "

        # Act
        result = split_pipe(input_text)

        # Assert
        assert result == []
