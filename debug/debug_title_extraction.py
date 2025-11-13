#!/usr/bin/env python3
"""Test anime title extraction from natural language queries."""

import asyncio

from services.app_context import AppContext
from services.rag_service import _extract_anime_title


async def test_title_extraction():
    """Test various query patterns."""
    test_cases = [
        # (input_query, expected_title, should_use_llm)
        ("Tell me about the anime called 'Ryza no Atelier'.", "ryza no atelier", False),
        ("Tell me about Cowboy Bebop", "cowboy bebop", False),
        ("What is Voltron about?", "voltron", False),
        ("Tell me about the anime Neon Genesis Evangelion", "neon genesis evangelion", False),
        ("Search for Trigun", "trigun", False),
        ("Anime called 'Full Metal Alchemist'", "full metal alchemist", False),
        ("Steins;Gate", "steins;gate", False),  # Direct title
        ("What are the best episodes of Attack on Titan", "attack on titan", False),
        # LLM fallback cases (patterns regex won't match)
        ("I'm looking for that space cowboy show", "cowboy bebop", True),  # LLM should extract
        ("Can you help me find info on the mecha anime with the giant robots", "mecha anime", True),  # Generic
    ]
    
    print("=" * 80)
    print("ANIME TITLE EXTRACTION TEST")
    print("=" * 80)
    
    ctx = AppContext.create()
    
    passed = 0
    failed = 0
    
    for query, expected, should_use_llm in test_cases:
        result = await _extract_anime_title(query, ctx)
        match = result.lower() == expected.lower()
        
        status = "✅ PASS" if match else "❌ FAIL"
        method = "LLM" if should_use_llm else "Regex"
        print(f"\n{status} [{method}]")
        print(f"  Query:    {query}")
        print(f"  Expected: {expected}")
        print(f"  Got:      {result}")
        
        if match:
            passed += 1
        else:
            failed += 1
    
    print("\n" + "=" * 80)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 80)
    
    return failed == 0


if __name__ == "__main__":
    import sys
    success = asyncio.run(test_title_extraction())
    sys.exit(0 if success else 1)
