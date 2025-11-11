"""Tests for MCP client service."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from services.mcp_client_service import MCPAnimeClient, create_mcp_client


@pytest.fixture
def sample_server_config() -> dict:
    """Sample MCP server configuration."""
    return {
        "command": "/usr/bin/python",
        "args": ["-m", "mcp_server_anime.server"],
        "env": {"PYTHONPATH": "/path/to/server"},
    }


@pytest.fixture
def mock_session():
    """Mock MCP ClientSession."""
    session = AsyncMock()
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock()
    return session


class TestMCPAnimeClient:
    """Tests for MCPAnimeClient class."""

    def test_init_creates_server_params(self, sample_server_config: dict) -> None:
        """Test that initialization creates server parameters."""
        # Act
        client = MCPAnimeClient(sample_server_config)

        # Assert
        assert client.server_params.command == "/usr/bin/python"
        assert client.server_params.args == ["-m", "mcp_server_anime.server"]
        assert client.server_params.env == {"PYTHONPATH": "/path/to/server"}
        assert client._session is None

    @pytest.mark.asyncio
    @patch("services.mcp_client_service.stdio_client")
    async def test_connect_establishes_connection(
        self, mock_stdio_client: Mock, sample_server_config: dict, mock_session: AsyncMock
    ) -> None:
        """Test that connect establishes MCP server connection."""
        # Arrange
        mock_stdio_client.return_value = mock_session
        client = MCPAnimeClient(sample_server_config)

        # Act
        await client.connect()

        # Assert
        assert client._session is not None
        mock_stdio_client.assert_called_once()
        mock_session.__aenter__.assert_called_once()

    @pytest.mark.asyncio
    @patch("services.mcp_client_service.stdio_client")
    async def test_connect_raises_on_failure(
        self, mock_stdio_client: Mock, sample_server_config: dict
    ) -> None:
        """Test that connect raises RuntimeError on connection failure."""
        # Arrange
        mock_stdio_client.side_effect = Exception("Connection failed")
        client = MCPAnimeClient(sample_server_config)

        # Act & Assert
        with pytest.raises(RuntimeError, match="MCP server connection failed"):
            await client.connect()

    @pytest.mark.asyncio
    async def test_disconnect_closes_session(
        self, sample_server_config: dict, mock_session: AsyncMock
    ) -> None:
        """Test that disconnect closes the session."""
        # Arrange
        client = MCPAnimeClient(sample_server_config)
        client._session = mock_session

        # Act
        await client.disconnect()

        # Assert
        assert client._session is None
        mock_session.__aexit__.assert_called_once_with(None, None, None)

    @pytest.mark.asyncio
    async def test_disconnect_handles_none_session(
        self, sample_server_config: dict
    ) -> None:
        """Test that disconnect handles None session gracefully."""
        # Arrange
        client = MCPAnimeClient(sample_server_config)
        client._session = None

        # Act (should not raise)
        await client.disconnect()

        # Assert
        assert client._session is None

    @pytest.mark.asyncio
    async def test_context_manager_connects_and_disconnects(
        self, sample_server_config: dict, mock_session: AsyncMock
    ) -> None:
        """Test that context manager connects and disconnects properly."""
        # Arrange
        client = MCPAnimeClient(sample_server_config)

        with patch("services.mcp_client_service.stdio_client", return_value=mock_session):
            # Act
            async with client as ctx_client:
                # Assert: Connected
                assert ctx_client is client
                assert client._session is not None

            # Assert: Disconnected
            assert client._session is None

    @pytest.mark.asyncio
    async def test_search_anime_returns_results(
        self, sample_server_config: dict, mock_session: AsyncMock
    ) -> None:
        """Test that search_anime returns search results."""
        # Arrange
        client = MCPAnimeClient(sample_server_config)
        client._session = mock_session

        mock_result = Mock()
        mock_result.content = {"aid": 12345, "title": "Test Anime"}
        mock_session.call_tool = AsyncMock(return_value=mock_result)

        # Act
        results = await client.search_anime("test")

        # Assert
        assert len(results) == 1
        assert results[0]["aid"] == 12345
        assert results[0]["title"] == "Test Anime"
        mock_session.call_tool.assert_called_once_with(
            "anidb_search", {"query": "test"}
        )

    @pytest.mark.asyncio
    async def test_search_anime_raises_when_not_connected(
        self, sample_server_config: dict
    ) -> None:
        """Test that search_anime raises when not connected."""
        # Arrange
        client = MCPAnimeClient(sample_server_config)

        # Act & Assert
        with pytest.raises(RuntimeError, match="Not connected to MCP server"):
            await client.search_anime("test")

    @pytest.mark.asyncio
    async def test_search_anime_raises_on_api_error(
        self, sample_server_config: dict, mock_session: AsyncMock
    ) -> None:
        """Test that search_anime raises on API error."""
        # Arrange
        client = MCPAnimeClient(sample_server_config)
        client._session = mock_session
        mock_session.call_tool = AsyncMock(side_effect=Exception("API error"))

        # Act & Assert
        with pytest.raises(RuntimeError, match="MCP anime search failed"):
            await client.search_anime("test")

    @pytest.mark.asyncio
    async def test_search_anime_handles_empty_results(
        self, sample_server_config: dict, mock_session: AsyncMock
    ) -> None:
        """Test that search_anime handles empty results."""
        # Arrange
        client = MCPAnimeClient(sample_server_config)
        client._session = mock_session

        mock_result = Mock()
        mock_result.content = None
        mock_session.call_tool = AsyncMock(return_value=mock_result)

        # Act
        results = await client.search_anime("nonexistent")

        # Assert
        assert results == []

    @pytest.mark.asyncio
    async def test_get_anime_details_returns_xml(
        self, sample_server_config: dict, mock_session: AsyncMock
    ) -> None:
        """Test that get_anime_details returns XML data."""
        # Arrange
        client = MCPAnimeClient(sample_server_config)
        client._session = mock_session

        mock_result = Mock()
        mock_result.content = '<?xml version="1.0"?><anime id="12345"></anime>'
        mock_session.call_tool = AsyncMock(return_value=mock_result)

        # Act
        xml_data = await client.get_anime_details(12345)

        # Assert
        assert xml_data == '<?xml version="1.0"?><anime id="12345"></anime>'
        mock_session.call_tool.assert_called_once_with(
            "anidb_details", {"aid": 12345}
        )

    @pytest.mark.asyncio
    async def test_get_anime_details_raises_when_not_connected(
        self, sample_server_config: dict
    ) -> None:
        """Test that get_anime_details raises when not connected."""
        # Arrange
        client = MCPAnimeClient(sample_server_config)

        # Act & Assert
        with pytest.raises(RuntimeError, match="Not connected to MCP server"):
            await client.get_anime_details(12345)

    @pytest.mark.asyncio
    async def test_get_anime_details_raises_on_api_error(
        self, sample_server_config: dict, mock_session: AsyncMock
    ) -> None:
        """Test that get_anime_details raises on API error."""
        # Arrange
        client = MCPAnimeClient(sample_server_config)
        client._session = mock_session
        mock_session.call_tool = AsyncMock(side_effect=Exception("API error"))

        # Act & Assert
        with pytest.raises(RuntimeError, match="MCP anime details fetch failed"):
            await client.get_anime_details(12345)

    @pytest.mark.asyncio
    async def test_get_anime_details_handles_empty_response(
        self, sample_server_config: dict, mock_session: AsyncMock
    ) -> None:
        """Test that get_anime_details handles empty response."""
        # Arrange
        client = MCPAnimeClient(sample_server_config)
        client._session = mock_session

        mock_result = Mock()
        mock_result.content = None
        mock_session.call_tool = AsyncMock(return_value=mock_result)

        # Act
        xml_data = await client.get_anime_details(12345)

        # Assert
        assert xml_data == ""


class TestCreateMCPClient:
    """Tests for create_mcp_client factory function."""

    @pytest.mark.asyncio
    async def test_create_mcp_client_with_valid_config(self) -> None:
        """Test creating MCP client with valid configuration."""
        # Arrange
        mock_context = Mock()
        mock_context.config.get_mcp_server_config.return_value = {
            "command": "/usr/bin/python",
            "args": ["-m", "mcp_server_anime.server"],
            "env": {},
        }

        # Act
        client = await create_mcp_client(mock_context, "anime")

        # Assert
        assert isinstance(client, MCPAnimeClient)
        assert client.server_params.command == "/usr/bin/python"
        mock_context.config.get_mcp_server_config.assert_called_once_with("anime")

    @pytest.mark.asyncio
    async def test_create_mcp_client_with_custom_server_name(self) -> None:
        """Test creating MCP client with custom server name."""
        # Arrange
        mock_context = Mock()
        mock_context.config.get_mcp_server_config.return_value = {
            "command": "/usr/bin/python",
            "args": ["-m", "custom_server"],
            "env": {},
        }

        # Act
        client = await create_mcp_client(mock_context, "custom")

        # Assert
        assert isinstance(client, MCPAnimeClient)
        mock_context.config.get_mcp_server_config.assert_called_once_with("custom")

    @pytest.mark.asyncio
    async def test_create_mcp_client_raises_on_missing_server(self) -> None:
        """Test that create_mcp_client raises when server not configured."""
        # Arrange
        mock_context = Mock()
        mock_context.config.get_mcp_server_config.side_effect = ValueError(
            "Server not configured"
        )

        # Act & Assert
        with pytest.raises(ValueError, match="Server not configured"):
            await create_mcp_client(mock_context, "nonexistent")
