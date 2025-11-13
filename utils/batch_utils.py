from collections.abc import Iterable, Iterator, Sequence
from typing import TypeVar

T = TypeVar("T")


def chunked(iterable: Iterable[T], size: int) -> Iterator[Sequence[T]]:  # noqa: UP047
    """Split an iterable into fixed-size chunks.

    Args:
        iterable: Input iterable to chunk.
        size: Maximum size of each chunk.

    Yields:
        Lists of items, each containing up to 'size' elements.
        The final chunk may contain fewer elements.

    Raises:
        ValueError: If size is not positive.

    Examples:
        >>> list(chunked([1, 2, 3, 4, 5], 2))
        [[1, 2], [3, 4], [5]]
    """
    if size <= 0:
        raise ValueError(f"Chunk size must be positive, got {size}")

    batch: list[T] = []
    for item in iterable:
        batch.append(item)
        if len(batch) >= size:
            yield batch
            batch = []
    if batch:
        yield batch
