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
                self._session = await stdio_client(self.server_params).__aenter__()
                logger.info("Connected to MCP anime server")
            except Exception as e:
                logger.error(f"Failed to connect to MCP server: {e}")
                raise RuntimeError(f"MCP server connection failed: {e}") from e

    async def disconnect(self) -> None:
        """Close connection to MCP server."""
        if self._session:
            try:
                await self._session.__aexit__(None, None, None)
                self._session = None
                logger.info("Disconnected from MCP anime server")
            except Exception as e:
                logger.warning(f"Error during MCP disconnect: {e}")

    async def search_anime(self, query: str) -> list[dict[str, Any]]:
        """Search for anime by title.

        Args:
            query: Anime title to search for.

        Returns:
            List of anime search results with basic info.

        Raises:
            RuntimeError: If not connected or search fails.
        """
        if not self._session:
            raise RuntimeError("Not connected to MCP server")

        try:
            logger.debug(f"Searching anime: {query}")
            result = await self._session.call_tool("anidb_search", {"query": query})
            
            # MCP returns a single result dict, wrap in list for consistency
            if result and hasattr(result, 'content'):
                return [result.content] if result.content else []
            return []
        except Exception as e:
            logger.error(f"Anime search failed: {e}")
            raise RuntimeError(f"MCP anime search failed: {e}") from e

    async def get_anime_details(self, aid: int) -> str:
        """Get detailed anime information by AniDB ID.

        Args:
            aid: AniDB anime ID.

        Returns:
            XML string with detailed anime information.

        Raises:
            RuntimeError: If not connected or fetch fails.
        """
        if not self._session:
            raise RuntimeError("Not connected to MCP server")

        try:
            logger.debug(f"Fetching anime details: {aid}")
            result = await self._session.call_tool("anidb_details", {"aid": aid})
            
            if result and hasattr(result, 'content'):
                return str(result.content) if result.content else ""
            return ""
        except Exception as e:
            logger.error(f"Anime details fetch failed: {e}")
            raise RuntimeError(f"MCP anime details fetch failed: {e}") from e


async def create_mcp_client(
    ctx: "AppContext", server_name: str = "anime"
) -> MCPAnimeClient:
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
