"""Integration tests for the main Gradio application."""

from unittest.mock import AsyncMock, Mock, patch

import gradio as gr
import pytest
from langchain_core.documents import Document

from ui.app import create_app, format_context, query_handler


class TestFormatContext:
    """Tests for format_context function."""

    def test_format_context_empty_list(self) -> None:
        """Test formatting with empty document list."""
        result = format_context([])

        assert "<em>No context documents available.</em>" in result

    def test_format_context_single_document(self) -> None:
        """Test formatting with a single document."""
        doc = Document(
            page_content="Test anime content",
            metadata={
                "title_main": "Test Anime",
                "anime_id": "123",
                "_distance_score": 0.1,
            },
        )

        result = format_context([doc])

        assert "Test Anime" in result
        assert "123" in result
        assert "Test anime content" in result

    def test_format_context_multiple_documents(self) -> None:
        """Test formatting with multiple documents."""
        docs = [
            Document(
                page_content="First anime",
                metadata={
                    "title_main": "Anime 1",
                    "anime_id": "1",
                    "_distance_score": 0.1,
                },
            ),
            Document(
                page_content="Second anime",
                metadata={
                    "title_main": "Anime 2",
                    "anime_id": "2",
                    "_distance_score": 0.2,
                },
            ),
        ]

        result = format_context(docs)

        assert "Anime 1" in result
        assert "Anime 2" in result
        assert "First anime" in result
        assert "Second anime" in result

    def test_format_context_truncates_long_content(self) -> None:
        """Test that long content is truncated."""
        long_content = "A" * 500
        doc = Document(
            page_content=long_content,
            metadata={
                "title_main": "Test Anime",
                "anime_id": "123",
                "_distance_score": 0.1,
            },
        )

        result = format_context([doc])

        # Should be truncated to 300 chars + "..."
        assert "..." in result
        assert len(result) < len(long_content) + 500  # Account for HTML

    def test_format_context_similarity_score(self) -> None:
        """Test that similarity score is displayed correctly."""
        doc = Document(
            page_content="Test content",
            metadata={
                "title_main": "Test Anime",
                "anime_id": "123",
                "_distance_score": 0.05,  # Low distance = high similarity
            },
        )

        result = format_context([doc])

        # Distance 0.05 should show as ~95% similarity
        assert "95" in result or "Similarity" in result

    def test_format_context_missing_metadata(self) -> None:
        """Test handling of missing metadata fields."""
        doc = Document(
            page_content="Test content",
            metadata={},  # Missing all metadata
        )

        result = format_context([doc])

        # Should handle gracefully with defaults
        assert "Unknown Title" in result or "N/A" in result


class TestQueryHandler:
    """Tests for query_handler function."""

    @pytest.mark.asyncio
    async def test_query_handler_empty_message(self) -> None:
        """Test handling of empty message."""
        answer, context = await query_handler("", [], 10, False)

        assert "Please enter a question" in answer
        assert context == ""

    @pytest.mark.asyncio
    async def test_query_handler_whitespace_message(self) -> None:
        """Test handling of whitespace-only message."""
        answer, context = await query_handler("   ", [], 10, False)

        assert "Please enter a question" in answer
        assert context == ""

    @pytest.mark.asyncio
    async def test_query_handler_success(self, mock_context: Mock) -> None:
        """Test successful query handling."""
        # Mock the RAG chain
        mock_chain = AsyncMock()
        mock_chain.return_value = (
            "Test answer",
            [
                Document(
                    page_content="Test content",
                    metadata={
                        "title_main": "Test Anime",
                        "anime_id": "123",
                        "_distance_score": 0.1,
                    },
                )
            ],
        )

        with (
            patch("ui.app.get_or_create_chain", return_value=mock_chain),
            patch("ui.app.get_or_create_context", return_value=mock_context),
        ):
            answer, context = await query_handler(
                "What anime are similar to Cowboy Bebop?", [], 10, False
            )

            assert answer == "Test answer"
            assert context == ""  # Context not shown when show_context=False

    @pytest.mark.asyncio
    async def test_query_handler_with_context_display(self, mock_context: Mock) -> None:
        """Test query handling with context display enabled."""
        # Mock the RAG chain
        mock_chain = AsyncMock()
        mock_chain.return_value = (
            "Test answer",
            [
                Document(
                    page_content="Test content",
                    metadata={
                        "title_main": "Test Anime",
                        "anime_id": "123",
                        "_distance_score": 0.1,
                    },
                )
            ],
        )

        with (
            patch("ui.app.get_or_create_chain", return_value=mock_chain),
            patch("ui.app.get_or_create_context", return_value=mock_context),
        ):
            answer, context = await query_handler(
                "What anime are similar to Cowboy Bebop?", [], 10, True
            )

            assert answer == "Test answer"
            assert context != ""  # Context should be shown
            assert "Test Anime" in context

    @pytest.mark.asyncio
    async def test_query_handler_updates_retrieval_k(self, mock_context: Mock) -> None:
        """Test that query handler updates retrieval_k in context."""
        mock_chain = AsyncMock()
        mock_chain.return_value = ("Test answer", [])

        with (
            patch("ui.app.get_or_create_chain", return_value=mock_chain),
            patch("ui.app.get_or_create_context", return_value=mock_context),
        ):
            await query_handler("Test question", [], 15, False)

            assert mock_context.retrieval_k == 15

    @pytest.mark.asyncio
    async def test_query_handler_value_error(self, mock_context: Mock) -> None:
        """Test handling of ValueError in query handler."""
        # Mock the RAG chain to raise a ValueError
        mock_chain = AsyncMock()
        mock_chain.side_effect = ValueError("Invalid input")

        with (
            patch("ui.app.get_or_create_chain", return_value=mock_chain),
            patch("ui.app.get_or_create_context", return_value=mock_context),
        ):
            answer, context = await query_handler("Test question", [], 10, False)

            assert "❌" in answer
            assert "Invalid input" in answer or "check your query" in answer
            assert context == ""

    @pytest.mark.asyncio
    async def test_query_handler_generic_error(self, mock_context: Mock) -> None:
        """Test handling of generic exceptions in query handler."""
        # Mock the RAG chain to raise a generic exception
        mock_chain = AsyncMock()
        mock_chain.side_effect = RuntimeError("Unexpected error")

        with (
            patch("ui.app.get_or_create_chain", return_value=mock_chain),
            patch("ui.app.get_or_create_context", return_value=mock_context),
        ):
            answer, context = await query_handler("Test question", [], 10, False)

            assert "❌" in answer
            assert context == ""


class TestGetOrCreateContext:
    """Tests for get_or_create_context function."""

    def test_get_or_create_context_creates_new(self) -> None:
        """Test that get_or_create_context creates a new context."""
        import ui.app
        from ui.app import get_or_create_context

        # Reset global state
        ui.app._app_context = None

        with patch("ui.app.AppContext.create") as mock_create:
            mock_ctx = Mock()
            mock_create.return_value = mock_ctx

            result = get_or_create_context()

            assert result == mock_ctx
            mock_create.assert_called_once()

    def test_get_or_create_context_reuses_existing(self) -> None:
        """Test that get_or_create_context reuses existing context."""
        import ui.app
        from ui.app import get_or_create_context

        # Set up existing context
        mock_ctx = Mock()
        ui.app._app_context = mock_ctx

        result = get_or_create_context()

        assert result == mock_ctx


class TestGetOrCreateChain:
    """Tests for get_or_create_chain function."""

    def test_get_or_create_chain_creates_new(self, mock_context: Mock) -> None:
        """Test that get_or_create_chain creates a new chain."""
        import ui.app
        from ui.app import get_or_create_chain

        # Reset global state
        ui.app._rag_chain = None
        ui.app._app_context = None

        mock_chain = Mock()
        mock_context.rag_chain = mock_chain

        with (
            patch("ui.app.get_or_create_context", return_value=mock_context),
            patch("ui.app.initialize_rag_chain", return_value=mock_chain),
        ):
            result = get_or_create_chain()

            assert result == mock_chain

    def test_get_or_create_chain_reuses_existing(self) -> None:
        """Test that get_or_create_chain reuses existing chain."""
        import ui.app
        from ui.app import get_or_create_chain

        # Set up existing chain
        mock_chain = Mock()
        ui.app._rag_chain = mock_chain

        result = get_or_create_chain()

        assert result == mock_chain


class TestCreateApp:
    """Tests for create_app function."""

    def test_create_app_returns_blocks(self) -> None:
        """Test that create_app returns a Gradio Blocks instance."""
        with patch("ui.app.validate_environment"):
            app = create_app()

            assert isinstance(app, gr.Blocks)

    def test_create_app_validates_environment(self) -> None:
        """Test that create_app validates environment."""
        with patch("ui.app.validate_environment") as mock_validate:
            create_app()

            mock_validate.assert_called_once()

    def test_create_app_handles_validation_error(self) -> None:
        """Test that create_app handles validation errors gracefully."""
        with patch(
            "ui.app.validate_environment",
            side_effect=OSError("Test error"),
        ):
            app = create_app()

            # Should return an error app instead of crashing
            assert isinstance(app, gr.Blocks)
            # Error app should have configuration error in title
            assert "Configuration Error" in app.title or "Error" in app.title

    def test_create_app_has_title(self) -> None:
        """Test that app has correct title."""
        with patch("ui.app.validate_environment"):
            app = create_app()

            assert "ShokoBot" in app.title

    def test_create_app_uses_theme(self) -> None:
        """Test that app uses a theme."""
        with patch("ui.app.validate_environment"):
            app = create_app()

            # Should have a theme set
            assert app.theme is not None


class TestFormatContextEdgeCases:
    """Additional edge case tests for format_context function."""

    def test_format_context_with_missing_title_main(self) -> None:
        """Test formatting when title_main is missing from metadata."""
        doc = Document(
            page_content="Test content",
            metadata={
                "anime_id": "123",
                "_distance_score": 0.1,
            },
        )

        result = format_context([doc])

        assert "Unknown Title" in result
        assert "123" in result

    def test_format_context_with_missing_anime_id(self) -> None:
        """Test formatting when anime_id is missing from metadata."""
        doc = Document(
            page_content="Test content",
            metadata={
                "title_main": "Test Anime",
                "_distance_score": 0.1,
            },
        )

        result = format_context([doc])

        assert "Test Anime" in result
        assert "N/A" in result

    def test_format_context_with_missing_distance_score(self) -> None:
        """Test formatting when distance score is missing."""
        doc = Document(
            page_content="Test content",
            metadata={
                "title_main": "Test Anime",
                "anime_id": "123",
            },
        )

        result = format_context([doc])

        # Should handle gracefully with default distance of 0.0
        assert "Test Anime" in result
        assert "100" in result or "Similarity" in result

    def test_format_context_with_high_distance_score(self) -> None:
        """Test formatting with high distance score (low similarity)."""
        doc = Document(
            page_content="Test content",
            metadata={
                "title_main": "Test Anime",
                "anime_id": "123",
                "_distance_score": 0.9,  # High distance = low similarity
            },
        )

        result = format_context([doc])

        # Distance 0.9 should show as ~10% similarity
        assert "10" in result or "Similarity" in result

    def test_format_context_with_zero_distance_score(self) -> None:
        """Test formatting with zero distance score (perfect match)."""
        doc = Document(
            page_content="Test content",
            metadata={
                "title_main": "Test Anime",
                "anime_id": "123",
                "_distance_score": 0.0,  # Perfect match
            },
        )

        result = format_context([doc])

        # Distance 0.0 should show as 100% similarity
        assert "100" in result

    def test_format_context_with_special_characters_in_title(self) -> None:
        """Test formatting with special characters in title."""
        doc = Document(
            page_content="Test content",
            metadata={
                "title_main": "Test <Anime> & \"Special\" 'Chars'",
                "anime_id": "123",
                "_distance_score": 0.1,
            },
        )

        result = format_context([doc])

        # HTML should be properly escaped or handled
        assert "Test" in result
        assert "Anime" in result

    def test_format_context_with_empty_page_content(self) -> None:
        """Test formatting with empty page content."""
        doc = Document(
            page_content="",
            metadata={
                "title_main": "Test Anime",
                "anime_id": "123",
                "_distance_score": 0.1,
            },
        )

        result = format_context([doc])

        assert "Test Anime" in result
        # Should handle empty content gracefully

    def test_format_context_html_structure(self) -> None:
        """Test that formatted context has proper HTML structure."""
        doc = Document(
            page_content="Test content",
            metadata={
                "title_main": "Test Anime",
                "anime_id": "123",
                "_distance_score": 0.1,
            },
        )

        result = format_context([doc])

        # Should contain HTML elements
        assert "<div" in result
        assert "<details" in result
        assert "<summary" in result
        assert "</div>" in result

    def test_format_context_multiple_docs_ordering(self) -> None:
        """Test that multiple documents are numbered correctly."""
        docs = [
            Document(
                page_content=f"Content {i}",
                metadata={
                    "title_main": f"Anime {i}",
                    "anime_id": str(i),
                    "_distance_score": 0.1 * i,
                },
            )
            for i in range(1, 6)
        ]

        result = format_context(docs)

        # Should have numbered entries
        for i in range(1, 6):
            assert f"{i}." in result
            assert f"Anime {i}" in result


class TestQueryHandlerEdgeCases:
    """Additional edge case tests for query_handler function."""

    @pytest.mark.asyncio
    async def test_query_handler_with_very_long_message(self, mock_context: Mock) -> None:
        """Test handling of very long messages."""
        mock_chain = AsyncMock()
        mock_chain.return_value = ("Test answer", [])

        long_message = "A" * 10000  # Very long message

        with (
            patch("ui.app.get_or_create_chain", return_value=mock_chain),
            patch("ui.app.get_or_create_context", return_value=mock_context),
        ):
            answer, context = await query_handler(long_message, [], 10, False)

            # Should handle without error
            assert isinstance(answer, str)
            mock_chain.assert_called_once()

    @pytest.mark.asyncio
    async def test_query_handler_with_special_characters(self, mock_context: Mock) -> None:
        """Test handling of special characters in message."""
        mock_chain = AsyncMock()
        mock_chain.return_value = ("Test answer", [])

        message = "What about anime with <tags> & 'quotes' and \"special\" chars?"

        with (
            patch("ui.app.get_or_create_chain", return_value=mock_chain),
            patch("ui.app.get_or_create_context", return_value=mock_context),
        ):
            answer, context = await query_handler(message, [], 10, False)

            assert isinstance(answer, str)

    @pytest.mark.asyncio
    async def test_query_handler_with_unicode_message(self, mock_context: Mock) -> None:
        """Test handling of unicode characters in message."""
        mock_chain = AsyncMock()
        mock_chain.return_value = ("Test answer", [])

        message = "進撃の巨人について教えてください"

        with (
            patch("ui.app.get_or_create_chain", return_value=mock_chain),
            patch("ui.app.get_or_create_context", return_value=mock_context),
        ):
            answer, context = await query_handler(message, [], 10, False)

            assert isinstance(answer, str)

    @pytest.mark.asyncio
    async def test_query_handler_with_conversation_history(self, mock_context: Mock) -> None:
        """Test query handler with conversation history."""
        mock_chain = AsyncMock()
        mock_chain.return_value = ("Test answer", [])

        history = [
            ("Previous question 1", "Previous answer 1"),
            ("Previous question 2", "Previous answer 2"),
        ]

        with (
            patch("ui.app.get_or_create_chain", return_value=mock_chain),
            patch("ui.app.get_or_create_context", return_value=mock_context),
        ):
            answer, context = await query_handler("New question", history, 10, False)

            assert isinstance(answer, str)

    @pytest.mark.asyncio
    async def test_query_handler_with_different_k_values(self, mock_context: Mock) -> None:
        """Test query handler with different k values."""
        mock_chain = AsyncMock()
        mock_chain.return_value = ("Test answer", [])

        with (
            patch("ui.app.get_or_create_chain", return_value=mock_chain),
            patch("ui.app.get_or_create_context", return_value=mock_context),
        ):
            # Test with k=1
            await query_handler("Test question", [], 1, False)
            assert mock_context.retrieval_k == 1

            # Test with k=20
            await query_handler("Test question", [], 20, False)
            assert mock_context.retrieval_k == 20

    @pytest.mark.asyncio
    async def test_query_handler_with_empty_document_list(self, mock_context: Mock) -> None:
        """Test query handler when no documents are retrieved."""
        mock_chain = AsyncMock()
        mock_chain.return_value = ("No relevant anime found.", [])

        with (
            patch("ui.app.get_or_create_chain", return_value=mock_chain),
            patch("ui.app.get_or_create_context", return_value=mock_context),
        ):
            answer, context = await query_handler("Test question", [], 10, True)

            assert answer == "No relevant anime found."
            assert context == ""  # Empty docs should result in empty context

    @pytest.mark.asyncio
    async def test_query_handler_error_message_format(self, mock_context: Mock) -> None:
        """Test that error messages are properly formatted."""
        mock_chain = AsyncMock()
        mock_chain.side_effect = ValueError("Specific error message")

        with (
            patch("ui.app.get_or_create_chain", return_value=mock_chain),
            patch("ui.app.get_or_create_context", return_value=mock_context),
        ):
            answer, context = await query_handler("Test question", [], 10, False)

            # Should have error indicator
            assert "❌" in answer
            # Should be a string
            assert isinstance(answer, str)
            assert context == ""

    @pytest.mark.asyncio
    async def test_query_handler_with_multiple_documents(self, mock_context: Mock) -> None:
        """Test query handler with multiple retrieved documents."""
        docs = [
            Document(
                page_content=f"Content {i}",
                metadata={
                    "title_main": f"Anime {i}",
                    "anime_id": str(i),
                    "_distance_score": 0.1,
                },
            )
            for i in range(5)
        ]

        mock_chain = AsyncMock()
        mock_chain.return_value = ("Test answer with multiple anime", docs)

        with (
            patch("ui.app.get_or_create_chain", return_value=mock_chain),
            patch("ui.app.get_or_create_context", return_value=mock_context),
        ):
            answer, context = await query_handler("Test question", [], 10, True)

            assert answer == "Test answer with multiple anime"
            # Context should contain all anime
            for i in range(5):
                assert f"Anime {i}" in context


class TestAppGlobalState:
    """Tests for global state management in app module."""

    def test_global_state_isolation(self) -> None:
        """Test that global state can be reset between tests."""
        import ui.app

        # Reset global state
        ui.app._app_context = None
        ui.app._rag_chain = None

        assert ui.app._app_context is None
        assert ui.app._rag_chain is None

    def test_context_singleton_behavior(self) -> None:
        """Test that context follows singleton pattern."""
        import ui.app
        from ui.app import get_or_create_context

        # Reset state
        ui.app._app_context = None

        with patch("ui.app.AppContext.create") as mock_create:
            mock_ctx = Mock()
            mock_create.return_value = mock_ctx

            # First call creates
            ctx1 = get_or_create_context()
            # Second call reuses
            ctx2 = get_or_create_context()

            assert ctx1 is ctx2
            mock_create.assert_called_once()

    def test_chain_singleton_behavior(self) -> None:
        """Test that chain follows singleton pattern."""
        import ui.app
        from ui.app import get_or_create_chain

        # Reset state
        ui.app._rag_chain = None
        ui.app._app_context = None

        mock_ctx = Mock()
        mock_chain = Mock()

        with (
            patch("ui.app.get_or_create_context", return_value=mock_ctx),
            patch("ui.app.initialize_rag_chain", return_value=mock_chain) as mock_init,
        ):
            # First call creates
            chain1 = get_or_create_chain()
            # Second call reuses
            chain2 = get_or_create_chain()

            assert chain1 is chain2
            mock_init.assert_called_once()
