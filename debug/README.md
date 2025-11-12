# Debug Scripts

This directory contains diagnostic and debugging scripts for troubleshooting the application.

## Available Scripts

### check_chromadb_config.py

Validates ChromaDB configuration and verifies the distance function setup.

**Usage:**
```bash
python debug/check_chromadb_config.py
```

**What it checks:**
- ChromaDB connection and collection existence
- Distance function configuration (should be `cosine`)
- Embedding dimensions and normalization
- Document count and sample data

**When to use:**
- After setting up ChromaDB for the first time
- When experiencing unexpected similarity scores
- To verify migration to cosine distance was successful
- When troubleshooting vector store issues

**Expected output:**
```
✅ Using cosine distance (correct)
   Your ChromaDB configuration is optimal for semantic search!
```

## See Also

- [ChromaDB Distance Fix Documentation](../docs/chromadb_distance_fix.md)
- [MCP Configuration Guide](../docs/mcp_configuration.md)
