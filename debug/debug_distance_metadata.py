#!/usr/bin/env python3
"""Quick test to verify distance scores are in metadata."""

import asyncio
import os
import sys


async def main():
    """Test that distance scores are stored in document metadata."""
    if not os.environ.get("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY not set")
        sys.exit(1)

    from services.app_context import AppContext

    print("Testing distance score metadata...")
    
    ctx = AppContext.create()
    rag = ctx.get_rag_chain()
    
    question = "Tell me about Cowboy Bebop"
    print(f"Question: {question}")
    
    answer, docs = await rag(question)
    
    print(f"\nFound {len(docs)} documents:")
    for i, doc in enumerate(docs, 1):
        title = doc.metadata.get("title_main", "Unknown")
        distance = doc.metadata.get("_distance_score")
        print(f"  {i}. {title}")
        print(f"     Distance: {distance}")
        print(f"     Has _distance_score: {'_distance_score' in doc.metadata}")
    
    # Check if any have distance scores
    has_scores = any(doc.metadata.get("_distance_score") is not None for doc in docs)
    
    if has_scores:
        print("\n✅ SUCCESS: Distance scores are present in metadata!")
    else:
        print("\n❌ FAIL: No distance scores found in metadata")
        print("\nDocument metadata keys:")
        for doc in docs[:1]:
            print(f"  {list(doc.metadata.keys())}")


if __name__ == "__main__":
    asyncio.run(main())
