"""Tests for vectorstore service functions.

This module tests vectorstore initialization, document operations,
and metadata filtering.
"""

from unittest.mock import Mock, patch

import pytest
from langchain_core.documents import Document

from services.vectorstore_service import (
    _create_embeddings,
    delete_by_anime_ids,
    get_chroma_vectorstore,
    upsert_documents,
)


class TestCreateEmbeddings:
    """Tests for _create_embeddings function."""

    @patch("services.vectorstore_service.OpenAIEmbeddings")
    def test_create_embeddings_with_valid_config(
        self, mock_embeddings_class: Mock, mock_config: Mock
    ) -> None:
        """Test embeddings creation with valid configuration."""
        # Arrange
        mock_config.get.side_effect = lambda key, default=None: {
            "openai.embedding_model": "text-embedding-3-small",
            "openai.request_timeout_s": 60,
        }.get(key, default)

        mock_embeddings = Mock()
        mock_embeddings_class.return_value = mock_embeddings

        # Act
        result = _create_embeddings(mock_config)

        # Assert
        assert result is mock_embeddings
        mock_embeddings_class.assert_called_once_with(
            model="text-embedding-3-small", timeout=60.0
        )

    @patch("services.vectorstore_service.OpenAIEmbeddings")
    def test_create_embeddings_with_custom_timeout(
        self, mock_embeddings_class: Mock, mock_config: Mock
    ) -> None:
        """Test embeddings creation with custom timeout."""
        # Arrange
        mock_config.get.side_effect = lambda key, default=None: {
            "openai.embedding_model": "text-embedding-3-large",
            "openai.request_timeout_s": 120,
        }.get(key, default)

        mock_embeddings = Mock()
        mock_embeddings_class.return_value = mock_embeddings

        # Act
        result = _create_embeddings(mock_config)

        # Assert
        mock_embeddings_class.assert_called_once_with(
            model="text-embedding-3-large", timeout=120.0
        )

    def test_create_embeddings_missing_model(self, mock_config: Mock) -> None:
        """Test that missing embedding model raises ValueError."""
        # Arrange
        mock_config.get.side_effect = lambda key, default=None: {
            "openai.embedding_model": None,
        }.get(key, default)

        # Act & Assert
        with pytest.raises(ValueError, match="openai.embedding_model not configured"):
            _create_embeddings(mock_config)


class TestGetChromaVectorstore:
    """Tests for get_chroma_vectorstore function."""

    @patch("services.vectorstore_service.Chroma")
    @patch("services.vectorstore_service._create_embeddings")
    def test_get_chroma_vectorstore_valid_config(
        self, mock_create_embeddings: Mock, mock_chroma_class: Mock, mock_config: Mock
    ) -> None:
        """Test vectorstore creation with valid configuration."""
        # Arrange
        mock_config.get.side_effect = lambda key, default=None: {
            "chroma.persist_directory": "./.chroma",
            "chroma.collection_name": "test_collection",
        }.get(key, default)

        mock_embeddings = Mock()
        mock_create_embeddings.return_value = mock_embeddings
        mock_vectorstore = Mock()
        mock_chroma_class.return_value = mock_vectorstore

        # Act
        result = get_chroma_vectorstore(mock_config)

        # Assert
        assert result is mock_vectorstore
        mock_chroma_class.assert_called_once_with(
            collection_name="test_collection",
            embedding_function=mock_embeddings,
            persist_directory="./.chroma",
        )

    def test_get_chroma_vectorstore_missing_persist_dir(
        self, mock_config: Mock
    ) -> None:
        """Test that missing persist_directory raises ValueError."""
        # Arrange
        mock_config.get.side_effect = lambda key, default=None: {
            "chroma.persist_directory": None,
            "chroma.collection_name": "test_collection",
        }.get(key, default)

        # Act & Assert
        with pytest.raises(ValueError, match="Chroma configuration incomplete"):
            get_chroma_vectorstore(mock_config)

    def test_get_chroma_vectorstore_missing_collection_name(
        self, mock_config: Mock
    ) -> None:
        """Test that missing collection_name raises ValueError."""
        # Arrange
        mock_config.get.side_effect = lambda key, default=None: {
            "chroma.persist_directory": "./.chroma",
            "chroma.collection_name": None,
        }.get(key, default)

        # Act & Assert
        with pytest.raises(ValueError, match="Chroma configuration incomplete"):
            get_chroma_vectorstore(mock_config)


class TestDeleteByAnimeIds:
    """Tests for delete_by_anime_ids function."""

    def test_delete_by_anime_ids_with_ids(self, mock_context: Mock) -> None:
        """Test deletion with valid anime IDs."""
        # Arrange
        anime_ids = ["123", "456", "789"]
        mock_vectorstore = Mock()
        mock_context.vectorstore = mock_vectorstore

        # Act
        delete_by_anime_ids(anime_ids, mock_context)

        # Assert
        mock_vectorstore.delete.assert_called_once_with(
            where={"anime_id": {"$in": ["123", "456", "789"]}}
        )

    def test_delete_by_anime_ids_empty_list(self, mock_context: Mock) -> None:
        """Test deletion with empty list does nothing."""
        # Arrange
        anime_ids: list[str] = []
        mock_vectorstore = Mock()
        mock_context.vectorstore = mock_vectorstore

        # Act
        delete_by_anime_ids(anime_ids, mock_context)

        # Assert
        mock_vectorstore.delete.assert_not_called()

    def test_delete_by_anime_ids_single_id(self, mock_context: Mock) -> None:
        """Test deletion with single anime ID."""
        # Arrange
        anime_ids = ["123"]
        mock_vectorstore = Mock()
        mock_context.vectorstore = mock_vectorstore

        # Act
        delete_by_anime_ids(anime_ids, mock_context)

        # Assert
        mock_vectorstore.delete.assert_called_once_with(
            where={"anime_id": {"$in": ["123"]}}
        )

    def test_delete_by_anime_ids_failure(self, mock_context: Mock) -> None:
        """Test that deletion failures raise exception."""
        # Arrange
        anime_ids = ["123"]
        mock_vectorstore = Mock()
        mock_vectorstore.delete.side_effect = Exception("Delete failed")
        mock_context.vectorstore = mock_vectorstore

        # Act & Assert
        with pytest.raises(Exception, match="Delete failed"):
            delete_by_anime_ids(anime_ids, mock_context)


class TestUpsertDocuments:
    """Tests for upsert_documents function."""

    @patch("services.vectorstore_service.filter_complex_metadata")
    def test_upsert_documents_valid(
        self, mock_filter: Mock, mock_context: Mock
    ) -> None:
        """Test upserting valid documents."""
        # Arrange
        docs = [
            Document(page_content="Test 1", metadata={"anime_id": "123"}),
            Document(page_content="Test 2", metadata={"anime_id": "456"}),
        ]
        mock_filter.return_value = docs

        mock_vectorstore = Mock()
        mock_context.vectorstore = mock_vectorstore

        # Act
        result = upsert_documents(docs, mock_context)

        # Assert
        assert result == ["123", "456"]
        mock_vectorstore.delete.assert_called_once_with(
            where={"anime_id": {"$in": ["123", "456"]}}
        )
        mock_vectorstore.add_documents.assert_called_once_with(
            docs, ids=["123", "456"]
        )

    def test_upsert_documents_empty_list(self, mock_context: Mock) -> None:
        """Test upserting empty list returns empty list."""
        # Arrange
        docs: list[Document] = []

        # Act
        result = upsert_documents(docs, mock_context)

        # Assert
        assert result == []

    @patch("services.vectorstore_service.filter_complex_metadata")
    def test_upsert_documents_missing_anime_id(
        self, mock_filter: Mock, mock_context: Mock
    ) -> None:
        """Test that documents missing anime_id raise ValueError."""
        # Arrange
        docs = [
            Document(page_content="Test", metadata={"title": "No ID"}),
        ]
        mock_filter.return_value = docs

        mock_vectorstore = Mock()
        mock_context.vectorstore = mock_vectorstore

        # Act & Assert
        with pytest.raises(ValueError, match="Document missing anime_id"):
            upsert_documents(docs, mock_context)

    @patch("services.vectorstore_service.filter_complex_metadata")
    def test_upsert_documents_filters_complex_metadata(
        self, mock_filter: Mock, mock_context: Mock
    ) -> None:
        """Test that complex metadata is filtered."""
        # Arrange
        original_docs = [
            Document(
                page_content="Test",
                metadata={"anime_id": "123", "tags": ["action", "comedy"]},
            ),
        ]
        filtered_docs = [
            Document(page_content="Test", metadata={"anime_id": "123"}),
        ]
        mock_filter.return_value = filtered_docs

        mock_vectorstore = Mock()
        mock_context.vectorstore = mock_vectorstore

        # Act
        result = upsert_documents(original_docs, mock_context)

        # Assert
        mock_filter.assert_called_once_with(original_docs)
        assert result == ["123"]

    @patch("services.vectorstore_service.filter_complex_metadata")
    def test_upsert_documents_failure(
        self, mock_filter: Mock, mock_context: Mock
    ) -> None:
        """Test that upsert failures raise exception."""
        # Arrange
        docs = [
            Document(page_content="Test", metadata={"anime_id": "123"}),
        ]
        mock_filter.return_value = docs

        mock_vectorstore = Mock()
        mock_vectorstore.add_documents.side_effect = Exception("Upsert failed")
        mock_context.vectorstore = mock_vectorstore

        # Act & Assert
        with pytest.raises(Exception, match="Upsert failed"):
            upsert_documents(docs, mock_context)
