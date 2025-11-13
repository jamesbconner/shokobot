"""Utility functions for working with distance scores from ChromaDB.

Note: ChromaDB returns distance scores where LOWER values indicate BETTER matches.
This is the opposite of similarity scores.
"""

import logging
from typing import TYPE_CHECKING

from langchain_core.documents import Document

if TYPE_CHECKING:
    from services.app_context import AppContext

logger = logging.getLogger(__name__)


def search_with_scores(
    query: str,
    ctx: "AppContext",
    k: int = 10,
    log_results: bool = True,
) -> list[tuple[Document, float]]:
    """Search vector store and return results with distance scores.

    Args:
        query: Search query string.
        ctx: Application context with vectorstore access.
        k: Number of results to return.
        log_results: Whether to log the results with scores.

    Returns:
        List of (Document, distance) tuples sorted by distance (lowest/best first).

    Note:
        Returns DISTANCE scores where LOWER = BETTER match.
        - 0.0-0.3: Excellent match
        - 0.3-0.6: Very good match
        - 0.6-0.9: Good match
        - 0.9+: Moderate to poor match

    Examples:
        >>> ctx = AppContext.create()
        >>> results = search_with_scores("action anime", ctx, k=5)
        >>> for doc, distance in results:
        ...     print(f"{distance:.4f} - {doc.metadata['title_main']}")
    """
    vs = ctx.vectorstore
    results = vs.similarity_search_with_score(query, k=k)

    if log_results:
        logger.info(f"Query: '{query}' returned {len(results)} results")
        for i, (doc, score) in enumerate(results, 1):
            title = doc.metadata.get("title_main", "Unknown")
            anime_id = doc.metadata.get("anime_id", "N/A")
            logger.info(f"  {i}. [{score:.4f}] {title} (ID: {anime_id})")

    return results


def get_score_statistics(results: list[tuple[Document, float]]) -> dict[str, float]:
    """Calculate statistics for distance scores.

    Args:
        results: List of (Document, distance) tuples.

    Returns:
        Dictionary with min (best), max (worst), avg, and median distances.

    Note:
        For distance scores: min = best match, max = worst match

    Examples:
        >>> results = search_with_scores("anime", ctx)
        >>> stats = get_score_statistics(results)
        >>> print(f"Best (lowest): {stats['min']:.4f}")
        >>> print(f"Worst (highest): {stats['max']:.4f}")
    """
    if not results:
        return {"min": 0.0, "max": 0.0, "avg": 0.0, "median": 0.0}

    scores = [score for _, score in results]
    scores_sorted = sorted(scores)  # Sort ascending for distance (low to high)

    stats = {
        "min": min(scores),  # Best (lowest distance)
        "max": max(scores),  # Worst (highest distance)
        "avg": sum(scores) / len(scores),
        "median": scores_sorted[len(scores_sorted) // 2],
    }

    return stats


def filter_by_score(
    results: list[tuple[Document, float]],
    max_distance: float,
) -> list[tuple[Document, float]]:
    """Filter results by maximum distance score (keep good matches).

    Args:
        results: List of (Document, distance) tuples.
        max_distance: Maximum distance threshold (lower = stricter).
                     Only results with distance <= max_distance are kept.

    Returns:
        Filtered list of (Document, distance) tuples with good matches.

    Note:
        For distance scores: LOWER = BETTER, so we keep scores <= threshold.

    Examples:
        >>> results = search_with_scores("anime", ctx, k=20)
        >>> high_quality = filter_by_score(results, max_distance=0.5)
        >>> print(f"Found {len(high_quality)} high-quality matches (distance <= 0.5)")
    """
    return [(doc, score) for doc, score in results if score <= max_distance]


def print_score_table(
    results: list[tuple[Document, float]],
    max_results: int = 10,
) -> None:
    """Print a formatted table of search results with distance scores.

    Args:
        results: List of (Document, distance) tuples.
        max_results: Maximum number of results to display.

    Examples:
        >>> results = search_with_scores("mecha anime", ctx)
        >>> print_score_table(results, max_results=5)
    """
    if not results:
        print("No results found.")
        return

    # Print header
    print(f"\n{'Rank':<6} {'Distance':<10} {'Anime ID':<12} {'Title'}")
    print("-" * 80)
    print("(Lower distance = better match)")

    # Print results
    for i, (doc, score) in enumerate(results[:max_results], 1):
        title = doc.metadata.get("title_main", "Unknown")
        anime_id = doc.metadata.get("anime_id", "N/A")
        print(f"{i:<6} {score:<10.4f} {anime_id:<12} {title}")

    # Print statistics
    if len(results) > max_results:
        print(f"\n... and {len(results) - max_results} more results")

    stats = get_score_statistics(results)
    print("\nDistance Statistics (lower = better):")
    print(f"  Best (lowest):  {stats['min']:.4f}")
    print(f"  Worst (highest): {stats['max']:.4f}")
    print(f"  Average:        {stats['avg']:.4f}")
    print(f"  Median:         {stats['median']:.4f}")
