#!/usr/bin/env python3
"""Example script showing how to view similarity scores from ChromaDB queries.

This script demonstrates different ways to query ChromaDB and view the
similarity scores for each result.

Requirements:
    - OPENAI_API_KEY environment variable must be set
    - ChromaDB vector store must be initialized with data

Usage:
    export OPENAI_API_KEY="your-api-key-here"
    python examples/view_similarity_scores.py
"""

import logging
import os
import sys

from services.app_context import AppContext

# Set up logging to see debug messages
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


def check_prerequisites() -> bool:
    """Check if all prerequisites are met.

    Returns:
        True if all prerequisites are met, False otherwise.
    """
    # Check for OpenAI API key
    if not os.environ.get("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY environment variable is not set!")
        print()
        print("Please set your OpenAI API key:")
        print("  export OPENAI_API_KEY='your-api-key-here'")
        print()
        print("Or add it to your shell profile (~/.bashrc, ~/.zshrc, etc.):")
        print("  echo 'export OPENAI_API_KEY=\"your-api-key-here\"' >> ~/.zshrc")
        print()
        return False

    # Check if config file exists
    try:
        _ = AppContext.create()
        logger.info("Successfully initialized AppContext")
        return True
    except FileNotFoundError as e:
        print(f"ERROR: Configuration file not found: {e}")
        print()
        print("Please ensure resources/config.json exists.")
        return False
    except Exception as e:
        print(f"ERROR: Failed to initialize AppContext: {e}")
        return False


def view_scores_basic(query: str) -> None:
    """Basic example: View similarity scores for a query.

    Args:
        query: Search query string.
    """
    # Initialize context
    ctx = AppContext.create()

    # Get vector store
    vs = ctx.vectorstore

    # Query with scores (returns list of (Document, score) tuples)
    results = vs.similarity_search_with_score(query, k=5)

    print(f"\n{'=' * 80}")
    print(f"Query: '{query}'")
    print(f"Found {len(results)} results")
    print(f"{'=' * 80}\n")

    for i, (doc, score) in enumerate(results, 1):
        print(f"Result {i}:")
        print(f"  Score: {score:.4f}")
        print(f"  Title: {doc.metadata.get('title_main', 'N/A')}")
        print(f"  Anime ID: {doc.metadata.get('anime_id', 'N/A')}")
        print(f"  Content preview: {doc.page_content[:100]}...")
        print()


def view_scores_with_threshold(query: str, threshold: float = 0.5) -> None:
    """Example: Filter results by distance score threshold.

    Args:
        query: Search query string.
        threshold: Maximum distance score (lower = better match).
                  Results with scores <= threshold are kept.
    """
    ctx = AppContext.create()
    vs = ctx.vectorstore

    # Query with scores
    results = vs.similarity_search_with_score(query, k=10)

    # Filter by threshold (keep scores <= threshold, since lower = better)
    filtered_results = [(doc, score) for doc, score in results if score <= threshold]

    print(f"\n{'=' * 80}")
    print(f"Query: '{query}'")
    print(f"Threshold: {threshold}")
    print(f"Total results: {len(results)}")
    print(f"Results above threshold: {len(filtered_results)}")
    print(f"{'=' * 80}\n")

    if filtered_results:
        best_score = min(score for _, score in filtered_results)
        worst_score = max(score for _, score in filtered_results)
        avg_score = sum(score for _, score in filtered_results) / len(filtered_results)

        print("Score Statistics (lower = better match):")
        print(f"  Best (lowest):  {best_score:.4f}")
        print(f"  Worst (highest): {worst_score:.4f}")
        print(f"  Average:        {avg_score:.4f}")
        print()

        for i, (doc, score) in enumerate(filtered_results, 1):
            print(f"{i}. [{score:.4f}] {doc.metadata.get('title_main', 'N/A')}")
    else:
        print("No results above threshold!")


def view_scores_comparison(queries: list[str]) -> None:
    """Example: Compare similarity scores across multiple queries.

    Args:
        queries: List of search query strings.
    """
    ctx = AppContext.create()
    vs = ctx.vectorstore

    print(f"\n{'=' * 80}")
    print("Query Comparison")
    print(f"{'=' * 80}\n")

    for query in queries:
        results = vs.similarity_search_with_score(query, k=3)

        if results:
            best_score = min(score for _, score in results)
            avg_score = sum(score for _, score in results) / len(results)

            print(f"Query: '{query}'")
            print(f"  Results: {len(results)}")
            print(f"  Best score (lowest): {best_score:.4f}")
            print(f"  Avg score:           {avg_score:.4f}")

            if results:
                top_result = results[0]
                print(
                    f"  Top match: {top_result[0].metadata.get('title_main', 'N/A')} ({top_result[1]:.4f})"
                )
            print()


def view_scores_with_mcp_fallback(query: str) -> None:
    """Example: View scores using the MCP fallback function.

    This shows how the MCP fallback evaluates scores.

    Args:
        query: Search query string.
    """
    import asyncio

    from services.rag_service import search_with_mcp_fallback

    ctx = AppContext.create()

    print(f"\n{'=' * 80}")
    print(f"MCP Fallback Analysis for: '{query}'")
    print(f"{'=' * 80}\n")

    # Get thresholds from config
    count_threshold = ctx.config.get_mcp_fallback_count_threshold()
    score_threshold = ctx.config.get_mcp_fallback_score_threshold()

    print("Configured Thresholds:")
    print(f"  Count threshold: {count_threshold}")
    print(f"  Score threshold: {score_threshold}")
    print()

    # Run the search (this will log scores)
    results = asyncio.run(search_with_mcp_fallback(query, ctx))

    print(f"\nReturned {len(results)} documents")


if __name__ == "__main__":
    # Check prerequisites before running examples
    if not check_prerequisites():
        sys.exit(1)

    print("\n" + "=" * 80)
    print("ChromaDB Similarity Score Examples")
    print("=" * 80)
    print()
    print("This script demonstrates how to view and analyze similarity scores")
    print("from ChromaDB queries. Each example shows different techniques.")
    print()

    try:
        # Example 1: Basic score viewing
        print("\n" + "=" * 80)
        print("EXAMPLE 1: Basic Similarity Scores")
        print("=" * 80)
        view_scores_basic("action anime with robots")

        # Example 2: Filter by threshold
        print("\n" + "=" * 80)
        print("EXAMPLE 2: Filter by Threshold")
        print("=" * 80)
        view_scores_with_threshold("romance anime", threshold=0.5)

        # Example 3: Compare queries
        print("\n" + "=" * 80)
        print("EXAMPLE 3: Compare Multiple Queries")
        print("=" * 80)
        view_scores_comparison(["Evangelion", "mecha anime", "psychological thriller"])

        # Example 4: MCP fallback analysis
        print("\n" + "=" * 80)
        print("EXAMPLE 4: MCP Fallback Analysis")
        print("=" * 80)
        view_scores_with_mcp_fallback("obscure anime title")

        print("\n" + "=" * 80)
        print("All examples completed successfully!")
        print("=" * 80)

    except Exception as e:
        logger.error(f"Error running examples: {e}", exc_info=True)
        print(f"\nERROR: {e}")
        print("\nPlease check:")
        print("  1. Your OpenAI API key is valid")
        print("  2. Your vector store is initialized with data")
        print("  3. Your config.json is properly configured")
        sys.exit(1)
