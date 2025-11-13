"""MCP client service for fetching anime data from AniDB via MCP server."""

import logging
from typing import TYPE_CHECKING, Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

if TYPE_CHECKING:
    from services.app_context import AppContext

logger = logging.getLogger(__name__)


class MCPAnimeClient:
    """Client for interacting with MCP anime server.

    Provides methods to search and fetch anime data from AniDB
    through the local MCP server with built-in rate limiting and caching.
    """

    def __init__(self, server_config: dict[str, Any]) -> None:
        """Initialize MCP client with server configuration.

        Args:
            server_config: MCP server configuration from config.json.
        """
        self.server_params = StdioServerParameters(
            command=server_config["command"],
            args=server_config.get("args", []),
            env=server_config.get("env", {}),
        )
        self._session: ClientSession | None = None
        self._stdio_context: Any = None

    async def __aenter__(self) -> "MCPAnimeClient":
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.disconnect()

    async def connect(self) -> None:
        """Establish connection to MCP server.

        Raises:
            RuntimeError: If connection fails.
        """
        if self._session is None:
            try:
                logger.info("Connecting to MCP anime server...")
                # stdio_client returns (read, write) streams, we need to wrap in ClientSession
                self._stdio_context = stdio_client(self.server_params)
                read, write = await self._stdio_context.__aenter__()
                self._session = ClientSession(read, write)
                await self._session.__aenter__()

                # Wait for initialization to complete
                logger.debug("Waiting for MCP server initialization...")
                await self._session.initialize()

                # Give the server a moment to fully start up
                import asyncio

                await asyncio.sleep(0.5)

                logger.info("Connected to MCP anime server and initialized")
            except Exception as e:
                logger.error(f"Failed to connect to MCP server: {e}")
                raise RuntimeError(f"MCP server connection failed: {e}") from e

    async def disconnect(self) -> None:
        """Close connection to MCP server."""
        if self._session:
            try:
                await self._session.__aexit__(None, None, None)
                self._session = None
            except Exception as e:
                logger.warning(f"Error during session disconnect: {e}")

        if self._stdio_context:
            try:
                await self._stdio_context.__aexit__(None, None, None)
                self._stdio_context = None
                logger.info("Disconnected from MCP anime server")
            except Exception as e:
                logger.warning(f"Error during stdio disconnect: {e}")

    async def list_tools(self) -> list[Any]:
        """List available MCP tools.

        Returns:
            List of available tool definitions.

        Raises:
            RuntimeError: If not connected.
        """
        if not self._session:
            raise RuntimeError("Not connected to MCP server")

        try:
            tools = await self._session.list_tools()
            logger.debug(f"Available tools: {tools}")
            return tools.tools if hasattr(tools, "tools") else []
        except Exception as e:
            logger.error(f"Failed to list tools: {e}")
            raise RuntimeError(f"MCP list tools failed: {e}") from e

    async def search_anime(self, query: str) -> list[dict[str, Any]]:
        """Search for anime by title.

        The MCP server returns JSON with format:
        {
            "aid": 17920,
            "title": "Ryza no Atelier: ...",
            "type": "Unknown",
            "year": 2023
        }

        Args:
            query: Anime title to search for.

        Returns:
            List of anime search results with basic info (aid, title, type, year).

        Raises:
            RuntimeError: If not connected or search fails.
        """
        if not self._session:
            raise RuntimeError("Not connected to MCP server")

        try:
            logger.debug(f"Searching anime: {query}")
            result = await self._session.call_tool("anidb_search", {"query": query})

            logger.debug(f"MCP search result type: {type(result)}")

            # Parse MCP tool response
            if result and hasattr(result, "content"):
                content = result.content
                logger.debug(f"Result content type: {type(content)}")

                # Content is a list of TextContent items
                if isinstance(content, list) and len(content) > 0:
                    first_content = content[0]
                    if hasattr(first_content, "text"):
                        # Parse JSON from text
                        import json

                        try:
                            data = json.loads(first_content.text)
                            logger.debug(f"Parsed search data: {data}")

                            # MCP server returns a list of search results
                            if isinstance(data, list):
                                logger.info(f"Found {len(data)} search results")
                                return data
                            elif isinstance(data, dict):
                                # Single result, wrap in list
                                logger.info("Found 1 search result")
                                return [data]
                            else:
                                logger.warning(f"Unexpected data type: {type(data)}")
                                return []

                        except json.JSONDecodeError as e:
                            logger.error(f"Failed to parse MCP response as JSON: {e}")
                            logger.error(f"Response text: {first_content.text[:200]}")
                            return []

            logger.warning("No valid content in MCP search result")
            return []
        except Exception as e:
            logger.error(f"Anime search failed: {e}")
            raise RuntimeError(f"MCP anime search failed: {e}") from e

    async def get_anime_details(self, aid: int) -> dict | str:
        """Get detailed anime information by AniDB ID.

        Args:
            aid: AniDB anime ID.

        Returns:
            JSON dict or string with detailed anime information.

        Raises:
            RuntimeError: If not connected or fetch fails.
        """
        if not self._session:
            raise RuntimeError("Not connected to MCP server")

        try:
            logger.debug(f"Fetching anime details: {aid}")
            result = await self._session.call_tool("anidb_details", {"aid": aid})

            logger.debug(f"MCP details result type: {type(result)}")

            # Parse MCP tool response
            if result and hasattr(result, "content"):
                content = result.content
                logger.debug(f"Result content type: {type(content)}")

                # Content is a list of TextContent items
                if isinstance(content, list) and len(content) > 0:
                    first_content = content[0]
                    if hasattr(first_content, "text"):
                        json_text = first_content.text
                        logger.debug(f"Received JSON data length: {len(json_text)}")

                        # Try to parse as JSON
                        try:
                            import json

                            json_data = json.loads(json_text)
                            logger.debug(f"Successfully parsed JSON with {len(json_data)} keys")
                            return json_data
                        except json.JSONDecodeError:
                            # Return as string if not valid JSON
                            logger.warning("Response is not valid JSON, returning as string")
                            return json_text

                # Fallback: try to convert content directly to string
                logger.warning("Unexpected content format, attempting string conversion")
                return str(content)

            logger.warning("No valid content in MCP details result")
            return ""
        except Exception as e:
            logger.error(f"Anime details fetch failed: {e}")
            raise RuntimeError(f"MCP anime details fetch failed: {e}") from e


async def create_mcp_client(ctx: "AppContext", server_name: str = "anime") -> MCPAnimeClient:
    """Factory function to create and configure MCP client.

    Args:
        ctx: Application context with configuration.
        server_name: Name of MCP server to connect to (default: "anime").

    Returns:
        Configured MCPAnimeClient instance.

    Raises:
        ValueError: If server is not configured.
        RuntimeError: If connection fails.
    """
    server_config = ctx.config.get_mcp_server_config(server_name)
    return MCPAnimeClient(server_config)
