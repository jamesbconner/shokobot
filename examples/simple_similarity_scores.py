#!/usr/bin/env python3
"""Simple example for viewing similarity scores without full initialization.

This is a minimal example that shows the core concept of viewing similarity
scores from ChromaDB queries.

Requirements:
    - OPENAI_API_KEY environment variable must be set
    - ChromaDB vector store must exist at ./.chroma
    
Usage:
    export OPENAI_API_KEY="your-api-key-here"
    python examples/simple_similarity_scores.py "your search query"
"""

import os
import sys


def main(query: str) -> None:
    """Run a simple similarity search and display scores.
    
    Args:
        query: Search query string.
    """
    # Check for API key
    if not os.environ.get("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY environment variable is not set!")
        print()
        print("Set it with:")
        print("  export OPENAI_API_KEY='your-api-key-here'")
        sys.exit(1)
    
    try:
        from services.app_context import AppContext
        
        # Initialize context
        print(f"Searching for: '{query}'")
        print("Initializing vector store...")
        ctx = AppContext.create()
        
        # Query with scores
        print("Querying ChromaDB...")
        results = ctx.vectorstore.similarity_search_with_score(query, k=5)
        
        # Display results
        print(f"\nFound {len(results)} results:\n")
        print(f"{'Rank':<6} {'Score':<10} {'Title'}")
        print("-" * 80)
        
        for i, (doc, score) in enumerate(results, 1):
            title = doc.metadata.get('title_main', 'Unknown')
            print(f"{i:<6} {score:<10.4f} {title}")
        
        # Show statistics
        if results:
            scores = [score for _, score in results]
            print(f"\nScore Statistics (lower = better match):")
            print(f"  Best (lowest):  {min(scores):.4f}")
            print(f"  Worst (highest): {max(scores):.4f}")
            print(f"  Average:        {sum(scores)/len(scores):.4f}")
        
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        print("\nMake sure:")
        print("  1. You're running from the project root directory")
        print("  2. resources/config.json exists")
        print("  3. ChromaDB vector store is initialized")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}")
        print("\nTroubleshooting:")
        print("  1. Check your OPENAI_API_KEY is valid")
        print("  2. Ensure vector store has data (run ingest first)")
        print("  3. Verify config.json is properly configured")
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python examples/simple_similarity_scores.py 'search query'")
        print()
        print("Examples:")
        print("  python examples/simple_similarity_scores.py 'action anime'")
        print("  python examples/simple_similarity_scores.py 'Evangelion'")
        print("  python examples/simple_similarity_scores.py 'mecha robots'")
        sys.exit(1)
    
    query = " ".join(sys.argv[1:])
    main(query)
