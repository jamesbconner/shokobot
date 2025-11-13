#!/usr/bin/env python3
"""Test MCP integration with RAG chain.

This example demonstrates how the RAG chain now uses MCP fallback
for queries that have poor vector store results.

Usage:
    export OPENAI_API_KEY="your-api-key"
    python examples/test_mcp_integration.py
"""

import asyncio
import logging
import os
import sys


async def test_good_query():
    """Test with a query that should have good vector store results."""
    from services.app_context import AppContext

    print("\n" + "=" * 80)
    print("TEST 1: Query with GOOD vector store results")
    print("=" * 80)
    print("Query: 'What is Cowboy Bebop about?'")
    print("Expected: Should use vector store results (no MCP fallback)")
    print()

    ctx = AppContext.create()
    chain = ctx.rag_chain

    # This should find good matches in vector store (distance < 0.7)
    answer, docs = await chain("What is Cowboy Bebop about?")

    print(f"Answer: {answer[:200]}...")
    print(f"\nUsed {len(docs)} documents")
    print("Document titles:")
    for i, doc in enumerate(docs[:3], 1):
        title = doc.metadata.get("title_main", "Unknown")
        print(f"  {i}. {title}")


async def test_poor_query():
    """Test with a query that should trigger MCP fallback."""
    from services.app_context import AppContext

    print("\n" + "=" * 80)
    print("TEST 2: Query with POOR vector store results")
    print("=" * 80)
    print("Query: 'Tell me about an obscure anime that probably isn't in the database'")
    print("Expected: Should trigger MCP fallback (poor results or not enough)")
    print()

    ctx = AppContext.create()
    chain = ctx.rag_chain

    # This should trigger MCP fallback due to poor matches
    answer, docs = await chain("Tell me about Atelier Ryza anime that was released in 2024")

    print(f"Answer: {answer[:200]}...")
    print(f"\nUsed {len(docs)} documents")
    print("Document titles:")
    for i, doc in enumerate(docs[:3], 1):
        title = doc.metadata.get("title_main", "Unknown")
        anime_id = doc.metadata.get("anime_id", "N/A")
        print(f"  {i}. {title} (ID: {anime_id})")


async def test_with_debug_logging():
    """Test with debug logging to see MCP fallback in action."""
    from services.app_context import AppContext

    print("\n" + "=" * 80)
    print("TEST 3: With DEBUG logging to see MCP fallback")
    print("=" * 80)
    print("Query: 'What is Evangelion about?'")
    print("Watch the logs to see if MCP is triggered...")
    print()

    # Enable debug logging
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(levelname)s - %(name)s - %(message)s",
    )

    ctx = AppContext.create()
    chain = ctx.rag_chain

    answer, docs = await chain("What is Evangelion about?")

    print(f"\nAnswer: {answer[:200]}...")
    print(f"Used {len(docs)} documents")


async def main():
    """Run all tests."""
    if not os.environ.get("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY environment variable not set!")
        print("Set it with: export OPENAI_API_KEY='your-key'")
        sys.exit(1)

    print("\n" + "=" * 80)
    print("MCP INTEGRATION TEST")
    print("=" * 80)
    print()
    print("This test demonstrates the MCP fallback integration.")
    print("The RAG chain now automatically uses MCP when:")
    print("  1. Vector store returns < 3 results (count threshold)")
    print("  2. Best result has distance > 0.7 (score threshold)")
    print()
    print("MCP Configuration:")
    print("  - fallback_count_threshold: 3")
    print("  - fallback_score_threshold: 0.7 (distance, lower=better)")
    print("  - enabled: true")
    print()

    try:
        # Test 1: Good query (should not trigger MCP)
        await test_good_query()

        # Test 2: Poor query (should trigger MCP)
        if input("\nRun test 2 (may trigger MCP)? [y/N]: ").lower() == "y":
            await test_poor_query()

        # Test 3: With debug logging
        if input("\nRun test 3 with debug logging? [y/N]: ").lower() == "y":
            await test_with_debug_logging()

        print("\n" + "=" * 80)
        print("TESTS COMPLETE")
        print("=" * 80)
        print()
        print("The RAG chain is now integrated with MCP fallback!")
        print("It will automatically use MCP when vector store results are poor.")

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
