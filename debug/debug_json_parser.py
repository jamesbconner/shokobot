#!/usr/bin/env python3
"""Test the new JSON parser with the example MCP output."""

import json
from pathlib import Path

from services.mcp_anime_json_parser import parse_anidb_json


def main() -> None:
    """Test parsing the example JSON file."""
    print("=" * 80)
    print("ANIDB JSON PARSER TEST")
    print("=" * 80)

    # Load the example JSON
    json_file = Path("resources/19060.json")
    if not json_file.exists():
        print(f"❌ Example file not found: {json_file}")
        return False

    with json_file.open() as f:
        data = json.load(f)

    print(f"\nLoaded JSON for: {data.get('title')}")
    print(f"AniDB ID: {data.get('aid')}")
    print()

    # Parse to ShowDoc
    try:
        show_doc = parse_anidb_json(data)
        print("✅ Successfully parsed to ShowDoc!")
        print()

        # Display key fields
        print("ShowDoc Fields:")
        print(f"  anime_id: {show_doc.anime_id}")
        print(f"  anidb_anime_id: {show_doc.anidb_anime_id}")
        print(f"  title_main: {show_doc.title_main}")
        print(f"  title_alts: {len(show_doc.title_alts)} alternates")
        if show_doc.title_alts:
            for alt in show_doc.title_alts[:3]:
                print(f"    - {alt}")
        print(f"  description: {show_doc.description[:100]}...")
        print(f"  tags: {len(show_doc.tags)} tags")
        if show_doc.tags:
            print(f"    {', '.join(show_doc.tags[:5])}")
        print(f"  episode_count_normal: {show_doc.episode_count_normal}")
        print(f"  episode_count_special: {show_doc.episode_count_special}")
        print(f"  begin_year: {show_doc.begin_year}")
        print(f"  end_year: {show_doc.end_year}")
        print(f"  rating: {show_doc.rating} (out of 1000)")
        print(f"  vote_count: {show_doc.vote_count}")
        print(f"  crunchyroll_id: {show_doc.crunchyroll_id}")
        print(f"  wikipedia_id: {show_doc.wikipedia_id}")
        print()

        # Test conversion to LangChain Document
        doc = show_doc.to_langchain_doc()
        print("✅ Successfully converted to LangChain Document!")
        print()
        print("Document Content (first 300 chars):")
        print(doc.page_content[:300])
        print("...")
        print()
        print("Document Metadata Keys:")
        print(f"  {', '.join(doc.metadata.keys())}")
        print()

        print("=" * 80)
        print("✅ ALL TESTS PASSED")
        print("=" * 80)
        return True

    except Exception as e:
        print(f"❌ Failed to parse: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    import sys

    success = main()
    sys.exit(0 if success else 1)
