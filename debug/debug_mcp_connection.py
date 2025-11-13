#!/usr/bin/env python3
"""Quick test to verify MCP client connection works."""

import asyncio
import logging
import sys

# Enable debug logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


async def main():
    """Test MCP client connection and search."""
    from services.app_context import AppContext
    from services.mcp_client_service import create_mcp_client

    print("=" * 80)
    print("MCP CLIENT CONNECTION TEST")
    print("=" * 80)
    
    ctx = AppContext.create()
    
    try:
        print("\n1. Creating MCP client...")
        async with await create_mcp_client(ctx) as mcp:
            print("✅ Connected to MCP server\n")
            
            # List available tools
            print("2. Listing available MCP tools...")
            try:
                tools = await mcp.list_tools()
                print(f"   Found {len(tools)} tools:")
                for tool in tools:
                    print(f"\n   Tool: {tool.name}")
                    print(f"   Description: {tool.description}")
                    if hasattr(tool, 'inputSchema'):
                        print(f"   Input Schema: {tool.inputSchema}")
                print()
            except Exception as e:
                print(f"   ⚠️  Could not list tools: {e}\n")
            
            # Test search (Step 1: anidb_search)
            query = "Voltron"
            print(f"3. Searching for anime: '{query}'")
            print(f"   Tool: anidb_search")
            print(f"   Parameters: {{'query': '{query}'}}")
            
            results = await mcp.search_anime(query)
            
            print(f"\n   Results: {len(results)} found")
            for i, result in enumerate(results, 1):
                print(f"\n   Result {i}:")
                if isinstance(result, dict):
                    for key, value in result.items():
                        print(f"     {key}: {value}")
                else:
                    print(f"     {result}")
            
            if not results:
                print("\n⚠️  No results found")
                print("   This might mean:")
                print("   - The anime doesn't exist in AniDB")
                print("   - The search query needs to be more specific")
                print("   - There's an issue with the MCP server")
                return
            
            # Test details fetch (Step 2: anidb_details)
            if results and isinstance(results[0], dict) and 'aid' in results[0]:
                aid = results[0]['aid']
                print(f"\n4. Fetching anime details for AID: {aid}")
                print(f"   Tool: anidb_details")
                print(f"   Parameters: {{'aid': {aid}}}")
                
                xml_data = await mcp.get_anime_details(aid)
                
                if xml_data:
                    print(f"\n   ✅ Received XML data ({len(xml_data)} characters)")
                    print(f"   First 200 chars: {xml_data[:200]}...")
                    print("\n✅ MCP TWO-STEP SEQUENCE SUCCESSFUL!")
                    print("   Step 1: anidb_search → Got AID")
                    print("   Step 2: anidb_details → Got XML")
                else:
                    print("\n   ❌ No XML data received")
            else:
                print("\n⚠️  Could not extract AID from search results")
                print(f"   Result structure: {type(results[0]) if results else 'N/A'}")
                
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
