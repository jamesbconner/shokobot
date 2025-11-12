#!/usr/bin/env python3
"""Test retrieval with expanded metadata."""

from dotenv import load_dotenv

from services.vectorstore_service import get_chroma_vectorstore

load_dotenv()

vs = get_chroma_vectorstore()
results = vs.similarity_search("anime about time travel", k=3)

if results:
    doc = results[0]
    print("Sample Retrieved Document:")
    print("=" * 80)
    print("Page Content:")
    print(doc.page_content[:40000])
    print("\n" + "=" * 80)
    print("Metadata:")
    for key, value in sorted(doc.metadata.items()):
        if value is not None and value != "" and value != "[]":
            print(f"  {key}: {value}")
