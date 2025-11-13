"""Tests for AppContext dependency injection and lifecycle management.

This module tests AppContext initialization, lazy loading of services,
caching behavior, and cache management operations.
"""

from unittest.mock import Mock, patch

from services.app_context import AppContext


class TestAppContextCreation:
    """Tests for AppContext initialization."""

    def test_app_context_creation(self, mock_config: Mock) -> None:
        """Test AppContext initialization with ConfigService."""
        # Act
        ctx = AppContext(config=mock_config)

        # Assert
        assert ctx.config is mock_config
        assert ctx._vectorstore is None
        assert ctx._rag_chain is None

    @patch("services.app_context.ConfigService")
    def test_app_context_create_classmethod(self, mock_config_class: Mock) -> None:
        """Test AppContext.create() classmethod."""
        # Arrange
        mock_config_instance = Mock()
        mock_config_class.return_value = mock_config_instance

        # Act
        ctx = AppContext.create(config_path="test_config.json")

        # Assert
        mock_config_class.assert_called_once_with("test_config.json")
        assert ctx.config is mock_config_instance

    @patch("services.app_context.ConfigService")
    def test_app_context_create_default_path(self, mock_config_class: Mock) -> None:
        """Test AppContext.create() with default config path."""
        # Arrange
        mock_config_instance = Mock()
        mock_config_class.return_value = mock_config_instance

        # Act
        ctx = AppContext.create()

        # Assert
        mock_config_class.assert_called_once_with("resources/config.json")


class TestVectorstoreLazyLoading:
    """Tests for vectorstore lazy loading and caching."""

    @patch("services.vectorstore_service.get_chroma_vectorstore")
    def test_vectorstore_lazy_loading(self, mock_get_vectorstore: Mock, mock_config: Mock) -> None:
        """Test that vectorstore is created on first access."""
        # Arrange
        mock_vectorstore = Mock()
        mock_get_vectorstore.return_value = mock_vectorstore
        ctx = AppContext(config=mock_config)

        # Verify not created yet
        assert ctx._vectorstore is None

        # Act: Access vectorstore first time
        result = ctx.vectorstore

        # Assert
        assert result is mock_vectorstore
        mock_get_vectorstore.assert_called_once_with(mock_config)

    @patch("services.vectorstore_service.get_chroma_vectorstore")
    def test_vectorstore_caching(self, mock_get_vectorstore: Mock, mock_config: Mock) -> None:
        """Test that vectorstore instance is reused (cached)."""
        # Arrange
        mock_vectorstore = Mock()
        mock_get_vectorstore.return_value = mock_vectorstore
        ctx = AppContext(config=mock_config)

        # Act: Access vectorstore multiple times
        result1 = ctx.vectorstore
        result2 = ctx.vectorstore
        result3 = ctx.vectorstore

        # Assert: Same instance returned
        assert result1 is result2
        assert result2 is result3
        # Verify get_chroma_vectorstore called only once
        mock_get_vectorstore.assert_called_once_with(mock_config)


class TestRagChainLazyLoading:
    """Tests for RAG chain lazy loading and caching."""

    @patch("services.rag_service.build_rag_chain")
    def test_rag_chain_lazy_loading(self, mock_build_chain: Mock, mock_config: Mock) -> None:
        """Test that RAG chain is created on first access."""
        # Arrange
        mock_chain = Mock()
        mock_build_chain.return_value = mock_chain
        ctx = AppContext(config=mock_config)

        # Verify not created yet
        assert ctx._rag_chain is None

        # Act: Access rag_chain first time
        result = ctx.rag_chain

        # Assert
        assert result is mock_chain
        mock_build_chain.assert_called_once_with(ctx, output_format="text")

    @patch("services.rag_service.build_rag_chain")
    def test_rag_chain_caching(self, mock_build_chain: Mock, mock_config: Mock) -> None:
        """Test that RAG chain instance is reused (cached)."""
        # Arrange
        mock_chain = Mock()
        mock_build_chain.return_value = mock_chain
        ctx = AppContext(config=mock_config)

        # Act: Access rag_chain multiple times
        result1 = ctx.rag_chain
        result2 = ctx.rag_chain
        result3 = ctx.rag_chain

        # Assert: Same instance returned
        assert result1 is result2
        assert result2 is result3
        # Verify build_rag_chain called only once
        mock_build_chain.assert_called_once_with(ctx, output_format="text")


class TestCacheManagement:
    """Tests for cache reset operations."""

    @patch("services.vectorstore_service.get_chroma_vectorstore")
    def test_reset_vectorstore(self, mock_get_vectorstore: Mock, mock_config: Mock) -> None:
        """Test that reset_vectorstore() clears vectorstore cache."""
        # Arrange
        mock_vectorstore1 = Mock()
        mock_vectorstore2 = Mock()
        mock_get_vectorstore.side_effect = [mock_vectorstore1, mock_vectorstore2]
        ctx = AppContext(config=mock_config)

        # Act: Access, reset, access again
        first_access = ctx.vectorstore
        ctx.reset_vectorstore()
        second_access = ctx.vectorstore

        # Assert
        assert first_access is mock_vectorstore1
        assert second_access is mock_vectorstore2
        assert first_access is not second_access
        assert mock_get_vectorstore.call_count == 2

    @patch("services.rag_service.build_rag_chain")
    def test_reset_rag_chain(self, mock_build_chain: Mock, mock_config: Mock) -> None:
        """Test that reset_rag_chain() clears RAG chain cache."""
        # Arrange
        mock_chain1 = Mock()
        mock_chain2 = Mock()
        mock_build_chain.side_effect = [mock_chain1, mock_chain2]
        ctx = AppContext(config=mock_config)

        # Act: Access, reset, access again
        first_access = ctx.rag_chain
        ctx.reset_rag_chain()
        second_access = ctx.rag_chain

        # Assert
        assert first_access is mock_chain1
        assert second_access is mock_chain2
        assert first_access is not second_access
        assert mock_build_chain.call_count == 2

    @patch("services.vectorstore_service.get_chroma_vectorstore")
    @patch("services.rag_service.build_rag_chain")
    def test_reset_all(
        self,
        mock_build_chain: Mock,
        mock_get_vectorstore: Mock,
        mock_config: Mock,
    ) -> None:
        """Test that reset_all() clears all caches."""
        # Arrange
        mock_vectorstore1 = Mock()
        mock_vectorstore2 = Mock()
        mock_chain1 = Mock()
        mock_chain2 = Mock()
        mock_get_vectorstore.side_effect = [mock_vectorstore1, mock_vectorstore2]
        mock_build_chain.side_effect = [mock_chain1, mock_chain2]
        ctx = AppContext(config=mock_config)

        # Act: Access both, reset all, access both again
        first_vs = ctx.vectorstore
        first_chain = ctx.rag_chain
        ctx.reset_all()
        second_vs = ctx.vectorstore
        second_chain = ctx.rag_chain

        # Assert: Both services recreated
        assert first_vs is mock_vectorstore1
        assert second_vs is mock_vectorstore2
        assert first_vs is not second_vs
        assert first_chain is mock_chain1
        assert second_chain is mock_chain2
        assert first_chain is not second_chain
        assert mock_get_vectorstore.call_count == 2
        assert mock_build_chain.call_count == 2

    def test_reset_vectorstore_when_not_loaded(self, mock_config: Mock) -> None:
        """Test that reset_vectorstore() works when vectorstore not yet loaded."""
        # Arrange
        ctx = AppContext(config=mock_config)

        # Act: Reset without accessing first
        ctx.reset_vectorstore()

        # Assert: No error, cache still None
        assert ctx._vectorstore is None

    def test_reset_rag_chain_when_not_loaded(self, mock_config: Mock) -> None:
        """Test that reset_rag_chain() works when RAG chain not yet loaded."""
        # Arrange
        ctx = AppContext(config=mock_config)

        # Act: Reset without accessing first
        ctx.reset_rag_chain()

        # Assert: No error, cache still None
        assert ctx._rag_chain is None

    def test_reset_all_when_nothing_loaded(self, mock_config: Mock) -> None:
        """Test that reset_all() works when nothing has been loaded."""
        # Arrange
        ctx = AppContext(config=mock_config)

        # Act: Reset without accessing anything first
        ctx.reset_all()

        # Assert: No error, caches still None
        assert ctx._vectorstore is None
        assert ctx._rag_chain is None


class TestIndependentCaching:
    """Tests to verify vectorstore and rag_chain are cached independently."""

    @patch("services.vectorstore_service.get_chroma_vectorstore")
    @patch("services.rag_service.build_rag_chain")
    def test_vectorstore_and_rag_chain_independent(
        self,
        mock_build_chain: Mock,
        mock_get_vectorstore: Mock,
        mock_config: Mock,
    ) -> None:
        """Test that vectorstore and rag_chain are cached independently."""
        # Arrange
        mock_vectorstore = Mock()
        mock_chain = Mock()
        mock_get_vectorstore.return_value = mock_vectorstore
        mock_build_chain.return_value = mock_chain
        ctx = AppContext(config=mock_config)

        # Act: Access vectorstore first
        vs = ctx.vectorstore
        assert mock_get_vectorstore.call_count == 1
        assert mock_build_chain.call_count == 0

        # Act: Access rag_chain
        chain = ctx.rag_chain
        assert mock_get_vectorstore.call_count == 1
        assert mock_build_chain.call_count == 1

        # Act: Access both again
        vs2 = ctx.vectorstore
        chain2 = ctx.rag_chain

        # Assert: Same instances, no additional calls
        assert vs is vs2
        assert chain is chain2
        assert mock_get_vectorstore.call_count == 1
        assert mock_build_chain.call_count == 1

    @patch("services.vectorstore_service.get_chroma_vectorstore")
    @patch("services.rag_service.build_rag_chain")
    def test_reset_vectorstore_does_not_affect_rag_chain(
        self,
        mock_build_chain: Mock,
        mock_get_vectorstore: Mock,
        mock_config: Mock,
    ) -> None:
        """Test that resetting vectorstore doesn't affect RAG chain cache."""
        # Arrange
        mock_vectorstore1 = Mock()
        mock_vectorstore2 = Mock()
        mock_chain = Mock()
        mock_get_vectorstore.side_effect = [mock_vectorstore1, mock_vectorstore2]
        mock_build_chain.return_value = mock_chain
        ctx = AppContext(config=mock_config)

        # Act: Access both
        vs1 = ctx.vectorstore
        chain1 = ctx.rag_chain

        # Act: Reset only vectorstore
        ctx.reset_vectorstore()

        # Act: Access both again
        vs2 = ctx.vectorstore
        chain2 = ctx.rag_chain

        # Assert: Vectorstore recreated, RAG chain still cached
        assert vs1 is not vs2
        assert chain1 is chain2
        assert mock_get_vectorstore.call_count == 2
        assert mock_build_chain.call_count == 1


class TestGetRagChainMethod:
    """Tests for get_rag_chain method with different output formats."""

    @patch("services.rag_service.build_rag_chain")
    def test_get_rag_chain_text_format_uses_cache(
        self, mock_build_chain: Mock, mock_config: Mock
    ) -> None:
        """Test that get_rag_chain with text format uses cached rag_chain."""
        # Arrange
        mock_chain = Mock()
        mock_build_chain.return_value = mock_chain
        ctx = AppContext(config=mock_config)

        # Act
        result1 = ctx.get_rag_chain(output_format="text")
        result2 = ctx.get_rag_chain(output_format="text")

        # Assert - should use cached version
        assert result1 is result2
        assert result1 is mock_chain
        # build_rag_chain should only be called once (for caching)
        mock_build_chain.assert_called_once_with(ctx, output_format="text")

    @patch("services.rag_service.build_rag_chain")
    def test_get_rag_chain_json_format_no_cache(
        self, mock_build_chain: Mock, mock_config: Mock
    ) -> None:
        """Test that get_rag_chain with json format doesn't use cache."""
        # Arrange
        mock_chain1 = Mock()
        mock_chain2 = Mock()
        mock_build_chain.side_effect = [mock_chain1, mock_chain2]
        ctx = AppContext(config=mock_config)

        # Act
        result1 = ctx.get_rag_chain(output_format="json")
        result2 = ctx.get_rag_chain(output_format="json")

        # Assert - should create new instance each time
        assert result1 is mock_chain1
        assert result2 is mock_chain2
        assert result1 is not result2
        # build_rag_chain should be called twice (no caching)
        assert mock_build_chain.call_count == 2
        mock_build_chain.assert_any_call(ctx, output_format="json")

    @patch("services.rag_service.build_rag_chain")
    def test_get_rag_chain_default_format_uses_cache(
        self, mock_build_chain: Mock, mock_config: Mock
    ) -> None:
        """Test that get_rag_chain with default format uses cached rag_chain."""
        # Arrange
        mock_chain = Mock()
        mock_build_chain.return_value = mock_chain
        ctx = AppContext(config=mock_config)

        # Act - call without output_format (defaults to "text")
        result1 = ctx.get_rag_chain()
        result2 = ctx.get_rag_chain()

        # Assert - should use cached version
        assert result1 is result2
        assert result1 is mock_chain
        mock_build_chain.assert_called_once_with(ctx, output_format="text")
