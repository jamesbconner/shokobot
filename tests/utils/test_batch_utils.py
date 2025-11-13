"""Tests for batch processing utility functions.

This module tests chunking functionality for splitting iterables into
fixed-size batches.
"""

import pytest

from utils.batch_utils import chunked


class TestChunked:
    """Tests for chunked function."""

    def test_chunked_basic(self) -> None:
        """Test basic chunking functionality with simple list."""
        # Arrange
        input_data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        chunk_size = 3
        expected = [[1, 2, 3], [4, 5, 6], [7, 8, 9], [10]]

        # Act
        result = list(chunked(input_data, chunk_size))

        # Assert
        assert result == expected

    def test_chunked_exact_size(self) -> None:
        """Test chunking when input size is exact multiple of chunk size."""
        # Arrange
        input_data = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        chunk_size = 3
        expected = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]

        # Act
        result = list(chunked(input_data, chunk_size))

        # Assert
        assert result == expected
        # Verify all chunks are same size
        assert all(len(chunk) == chunk_size for chunk in result)

    def test_chunked_remainder(self) -> None:
        """Test chunking when input has remainder elements."""
        # Arrange
        input_data = [1, 2, 3, 4, 5, 6, 7]
        chunk_size = 3
        expected = [[1, 2, 3], [4, 5, 6], [7]]

        # Act
        result = list(chunked(input_data, chunk_size))

        # Assert
        assert result == expected
        # Verify last chunk has remainder
        assert len(result[-1]) == 1

    def test_chunked_empty(self) -> None:
        """Test chunking empty input returns no chunks."""
        # Arrange
        input_data: list[int] = []
        chunk_size = 3

        # Act
        result = list(chunked(input_data, chunk_size))

        # Assert
        assert result == []

    def test_chunked_invalid_size(self) -> None:
        """Test that invalid chunk size raises ValueError."""
        # Arrange
        input_data = [1, 2, 3, 4, 5]

        # Act & Assert: Test zero chunk size
        with pytest.raises(ValueError, match="Chunk size must be positive"):
            list(chunked(input_data, 0))

        # Act & Assert: Test negative chunk size
        with pytest.raises(ValueError, match="Chunk size must be positive"):
            list(chunked(input_data, -1))

    def test_chunked_generator(self) -> None:
        """Test chunking with generator input."""

        # Arrange
        def number_generator() -> int:
            """Generate numbers 1 through 10."""
            for i in range(1, 11):
                yield i

        chunk_size = 4
        expected = [[1, 2, 3, 4], [5, 6, 7, 8], [9, 10]]

        # Act
        result = list(chunked(number_generator(), chunk_size))

        # Assert
        assert result == expected

    def test_chunked_single_element(self) -> None:
        """Test chunking with single element."""
        # Arrange
        input_data = [42]
        chunk_size = 5
        expected = [[42]]

        # Act
        result = list(chunked(input_data, chunk_size))

        # Assert
        assert result == expected

    def test_chunked_chunk_size_larger_than_input(self) -> None:
        """Test chunking when chunk size is larger than input."""
        # Arrange
        input_data = [1, 2, 3]
        chunk_size = 10
        expected = [[1, 2, 3]]

        # Act
        result = list(chunked(input_data, chunk_size))

        # Assert
        assert result == expected

    @pytest.mark.parametrize(
        "input_data,chunk_size,expected_chunk_count",
        [
            ([1, 2, 3, 4, 5], 1, 5),
            ([1, 2, 3, 4, 5], 2, 3),
            ([1, 2, 3, 4, 5], 5, 1),
            (list(range(100)), 10, 10),
            (list(range(100)), 7, 15),
        ],
    )
    def test_chunked_various_sizes(
        self, input_data: list[int], chunk_size: int, expected_chunk_count: int
    ) -> None:
        """Test chunking with various input and chunk sizes."""
        # Act
        result = list(chunked(input_data, chunk_size))

        # Assert
        assert len(result) == expected_chunk_count
        # Verify all elements are preserved
        flattened = [item for chunk in result for item in chunk]
        assert flattened == input_data

    def test_chunked_string_elements(self) -> None:
        """Test chunking with string elements."""
        # Arrange
        input_data = ["a", "b", "c", "d", "e", "f", "g"]
        chunk_size = 3
        expected = [["a", "b", "c"], ["d", "e", "f"], ["g"]]

        # Act
        result = list(chunked(input_data, chunk_size))

        # Assert
        assert result == expected

    def test_chunked_preserves_order(self) -> None:
        """Test that chunking preserves element order."""
        # Arrange
        input_data = list(range(20))
        chunk_size = 5

        # Act
        result = list(chunked(input_data, chunk_size))

        # Assert
        # Flatten and verify order preserved
        flattened = [item for chunk in result for item in chunk]
        assert flattened == input_data

    def test_chunked_lazy_evaluation(self) -> None:
        """Test that chunked returns iterator (lazy evaluation)."""
        # Arrange
        input_data = [1, 2, 3, 4, 5]
        chunk_size = 2

        # Act
        result = chunked(input_data, chunk_size)

        # Assert
        # Verify it's an iterator
        assert hasattr(result, "__iter__")
        assert hasattr(result, "__next__")
        # Verify we can iterate
        first_chunk = next(result)
        assert first_chunk == [1, 2]
