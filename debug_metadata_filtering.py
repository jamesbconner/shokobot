#!/usr/bin/env python3
"""Debug metadata filtering to see what's being removed."""

import json
from pathlib import Path

from langchain_community.vectorstores.utils import filter_complex_metadata
from services.mcp_anime_json_parser import parse_anidb_json


def main():
    """Test metadata filtering with the Ryza example."""
    print("=" * 80)
    print("METADATA FILTERING DEBUG")
    print("=" * 80)
    
    # Load the example JSON
    json_file = Path("resources/19060.json")
    with json_file.open() as f:
        data = json.load(f)
    
    # Parse to ShowDoc
    show_doc = parse_anidb_json(data)
    
    # Convert to LangChain Document
    doc = show_doc.to_langchain_doc()
    
    print("\n📋 ORIGINAL METADATA:")
    print("=" * 80)
    for key, value in doc.metadata.items():
        value_type = type(value).__name__
        value_str = str(value)[:100] if value else "None"
        print(f"  {key:25} ({value_type:10}): {value_str}")
    
    print(f"\nTotal fields: {len(doc.metadata)}")
    
    # Filter metadata
    filtered_docs = filter_complex_metadata([doc])
    filtered_doc = filtered_docs[0]
    
    print("\n✂️  FILTERED METADATA:")
    print("=" * 80)
    for key, value in filtered_doc.metadata.items():
        value_type = type(value).__name__
        value_str = str(value)[:100] if value else "None"
        print(f"  {key:25} ({value_type:10}): {value_str}")
    
    print(f"\nTotal fields: {len(filtered_doc.metadata)}")
    
    # Show what was removed
    removed_keys = set(doc.metadata.keys()) - set(filtered_doc.metadata.keys())
    if removed_keys:
        print("\n❌ REMOVED FIELDS:")
        print("=" * 80)
        for key in sorted(removed_keys):
            value = doc.metadata[key]
            value_type = type(value).__name__
            print(f"  {key:25} ({value_type:10}): {value}")
    
    # Check specific fields we care about
    print("\n🔍 KEY FIELDS CHECK:")
    print("=" * 80)
    important_fields = ["begin_year", "end_year", "episode_count_normal", "episode_count_special"]
    for field in important_fields:
        original = doc.metadata.get(field)
        filtered = filtered_doc.metadata.get(field)
        status = "✅" if original == filtered else "❌"
        print(f"  {status} {field:25}: {original} → {filtered}")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
