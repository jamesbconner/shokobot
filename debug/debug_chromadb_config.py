#!/usr/bin/env python3
"""Check ChromaDB collection configuration and distance function.

This diagnostic script validates ChromaDB configuration and verifies
that the correct distance function (cosine) is being used.

Usage:
    python debug/check_chromadb_config.py
"""

import os
import sys
from pathlib import Path


def main() -> None:
    """Check ChromaDB configuration."""
    if not os.environ.get("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY environment variable is not set!")
        sys.exit(1)

    try:
        import chromadb
        import numpy as np

        from services.app_context import AppContext

        print("🔍 ChromaDB Configuration Check")
        print("=" * 50)

        # Initialize context
        ctx = AppContext.create()
        config = ctx.config

        # Get configuration
        persist_dir = config.get("chroma.persist_directory")
        collection_name = config.get("chroma.collection_name")

        print("\n📁 Configuration:")
        print(f"  Persist directory: {persist_dir}")
        print(f"  Collection name: {collection_name}")
        print(f"  Directory exists: {Path(persist_dir).exists()}")

        # Connect to ChromaDB directly
        print("\n🔌 Connecting to ChromaDB...")
        client = chromadb.PersistentClient(path=persist_dir)

        # List collections
        collections = client.list_collections()
        print("\n📚 Available Collections:")
        for collection in collections:
            print(f"  - {collection.name}")

        # Check our specific collection
        if collection_name in [c.name for c in collections]:
            print(f"\n🎯 Analyzing Collection: {collection_name}")
            collection = client.get_collection(collection_name)

            # Get collection info
            count = collection.count()
            print(f"  Document count: {count}")

            # Check metadata
            metadata = collection.metadata
            print(f"  Collection metadata: {metadata}")

            # Check distance function
            if metadata and "hnsw:space" in metadata:
                distance_func = metadata["hnsw:space"]
                print(f"\n  🎯 Distance function: {distance_func}")

                if distance_func == "cosine":
                    print("     ✅ Using cosine distance")
                elif distance_func == "l2":
                    print("     ⚠️  Using L2/Euclidean distance")
                elif distance_func == "ip":
                    print("     ⚠️  Using inner product")
            else:
                print("\n  ❌ NO DISTANCE FUNCTION SPECIFIED!")
                print("     ChromaDB is using DEFAULT (likely L2/Euclidean)")

            # Sample documents
            if count > 0:
                print("\n🔬 Sampling Documents:")
                results = collection.get(limit=2, include=["embeddings", "metadatas"])

                embeddings = results["embeddings"]
                metadatas = results["metadatas"]
                if embeddings is not None and metadatas is not None and len(embeddings) > 0:
                    for i, (embedding, metadata) in enumerate(
                        zip(embeddings[:2], metadatas[:2], strict=False)
                    ):
                        title = metadata.get("title_main", "Unknown") if metadata else "Unknown"
                        norm = np.linalg.norm(embedding)
                        print(f"  {i + 1}. {title}")
                        print(f"     Dimension: {len(embedding)}")
                        print(f"     Norm: {norm:.6f}")
                        print(f"     Normalized: {'Yes' if abs(norm - 1.0) < 0.01 else 'No'}")

        else:
            print(f"\n❌ Collection '{collection_name}' not found!")

        # Summary
        print("\n" + "=" * 50)
        print("📊 DIAGNOSIS:")

        if collection_name in [c.name for c in collections]:
            collection = client.get_collection(collection_name)
            metadata = collection.metadata

            if not metadata or "hnsw:space" not in metadata:
                print("\n❌ PROBLEM FOUND: No distance function specified!")
                print("   ChromaDB is using default L2 (Euclidean) distance.")
                print("   For normalized embeddings, this gives different results than cosine.")
                print("\n💡 SOLUTION:")
                print("   The vectorstore service now automatically uses cosine distance.")
                print("   You need to recreate the collection:")
                print("   1. Backup your data")
                print("   2. Delete the collection")
                print("   3. Re-run ingest (will create with cosine distance)")
                print("\n📚 For more information:")
                print("   See docs/chromadb_distance_fix.md")
            elif metadata["hnsw:space"] != "cosine":
                print(f"\n⚠️  Using {metadata['hnsw:space']} distance")
                print("   For embeddings, cosine distance is usually better")
            else:
                print("\n✅ Using cosine distance (correct)")
                print("   Your ChromaDB configuration is optimal for semantic search!")
                print("\n📊 Score Interpretation Guide:")
                print("   0.0-0.3: Excellent match")
                print("   0.3-0.6: Very good match")
                print("   0.6-0.9: Good match")
                print("   0.9-1.2: Moderate match")
                print("   1.2+:    Poor match")

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
