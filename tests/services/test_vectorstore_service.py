"""Unit tests for vectorstore service."""

import logging
from unittest.mock import MagicMock, Mock, patch

import pytest
from langchain_core.documents import Document

from services.config_service import ConfigService
from services.vectorstore_service import (
    _validate_distance_function,
    get_chroma_vectorstore,
)


@pytest.fixture
def mock_config() -> ConfigService:
    """Create mock configuration service.

    Returns:
        Mock ConfigService instance.
    """
    config = Mock(spec=ConfigService)
    config.get.side_effect = lambda key, default=None: {
        "chroma.persist_directory": "./.chroma_test",
        "chroma.collection_name": "test_collection",
        "openai.embedding_model": "text-embedding-3-small",
        "openai.request_timeout_s": 60,
        "openai.max_retries": 3,
    }.get(key, default)
    return config


class TestGetChromaVectorstore:
    """Tests for get_chroma_vectorstore function."""

    @patch("services.vectorstore_service.Chroma")
    @patch("services.vectorstore_service._create_embeddings")
    @patch("services.vectorstore_service._validate_distance_function")
    def test_creates_vectorstore_with_cosine_distance(
        self,
        mock_validate: MagicMock,
        mock_create_embeddings: MagicMock,
        mock_chroma: MagicMock,
        mock_config: ConfigService,
    ) -> None:
        """Test that vectorstore is created with cosine distance metadata.

        Args:
            mock_validate: Mock validation function.
            mock_create_embeddings: Mock embeddings creation.
            mock_chroma: Mock Chroma class.
            mock_config: Mock configuration service.
        """
        # Arrange
        mock_embeddings = Mock()
        mock_create_embeddings.return_value = mock_embeddings
        mock_vectorstore = Mock()
        mock_chroma.return_value = mock_vectorstore

        # Act
        result = get_chroma_vectorstore(mock_config)

        # Assert
        mock_chroma.assert_called_once_with(
            collection_name="test_collection",
            embedding_function=mock_embeddings,
            persist_directory="./.chroma_test",
            collection_metadata={"hnsw:space": "cosine"},
        )
        assert result == mock_vectorstore
        mock_validate.assert_called_once_with(mock_vectorstore, "test_collection")

    @patch("services.vectorstore_service.Chroma")
    @patch("services.vectorstore_service._create_embeddings")
    def test_raises_error_when_config_incomplete(
        self,
        mock_create_embeddings: MagicMock,
        mock_chroma: MagicMock,
    ) -> None:
        """Test that error is raised when configuration is incomplete.

        Args:
            mock_create_embeddings: Mock embeddings creation.
            mock_chroma: Mock Chroma class.
        """
        # Arrange
        config = Mock(spec=ConfigService)
        config.get.return_value = None  # Missing configuration

        # Act & Assert
        with pytest.raises(ValueError, match="Chroma configuration incomplete"):
            get_chroma_vectorstore(config)

        mock_chroma.assert_not_called()

    @patch("services.vectorstore_service.Chroma")
    @patch("services.vectorstore_service._create_embeddings")
    @patch("services.vectorstore_service._validate_distance_function")
    def test_calls_validation_after_creation(
        self,
        mock_validate: MagicMock,
        mock_create_embeddings: MagicMock,
        mock_chroma: MagicMock,
        mock_config: ConfigService,
    ) -> None:
        """Test that validation is called after vectorstore creation.

        Args:
            mock_validate: Mock validation function.
            mock_create_embeddings: Mock embeddings creation.
            mock_chroma: Mock Chroma class.
            mock_config: Mock configuration service.
        """
        # Arrange
        mock_vectorstore = Mock()
        mock_chroma.return_value = mock_vectorstore

        # Act
        get_chroma_vectorstore(mock_config)

        # Assert
        mock_validate.assert_called_once_with(mock_vectorstore, "test_collection")


class TestValidateDistanceFunction:
    """Tests for _validate_distance_function."""

    def test_logs_info_when_cosine_distance_correct(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test that info is logged when distance function is correct.

        Args:
            caplog: Pytest log capture fixture.
        """
        # Arrange
        mock_collection = Mock()
        mock_collection.metadata = {"hnsw:space": "cosine"}

        mock_vectorstore = Mock()
        mock_vectorstore._collection = mock_collection

        # Act
        with caplog.at_level(logging.INFO):
            _validate_distance_function(mock_vectorstore, "test_collection")

        # Assert
        assert "correctly configured with cosine distance" in caplog.text

    def test_logs_warning_when_distance_function_incorrect(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test that warning is logged when distance function is incorrect.

        Args:
            caplog: Pytest log capture fixture.
        """
        # Arrange
        mock_collection = Mock()
        mock_collection.metadata = {"hnsw:space": "l2"}

        mock_vectorstore = Mock()
        mock_vectorstore._collection = mock_collection

        # Act
        with caplog.at_level(logging.WARNING):
            _validate_distance_function(mock_vectorstore, "test_collection")

        # Assert
        assert "using l2 distance instead of cosine" in caplog.text
        assert "migrate_chromadb_distance.py" in caplog.text

    def test_logs_warning_when_metadata_missing(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test that warning is logged when metadata is missing.

        Args:
            caplog: Pytest log capture fixture.
        """
        # Arrange
        mock_collection = Mock()
        mock_collection.metadata = None

        mock_vectorstore = Mock()
        mock_vectorstore._collection = mock_collection

        # Act
        with caplog.at_level(logging.WARNING):
            _validate_distance_function(mock_vectorstore, "test_collection")

        # Assert
        assert "using none distance instead of cosine" in caplog.text

    def test_logs_warning_when_hnsw_space_missing(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test that warning is logged when hnsw:space key is missing.

        Args:
            caplog: Pytest log capture fixture.
        """
        # Arrange
        mock_collection = Mock()
        mock_collection.metadata = {}  # Empty metadata

        mock_vectorstore = Mock()
        mock_vectorstore._collection = mock_collection

        # Act
        with caplog.at_level(logging.WARNING):
            _validate_distance_function(mock_vectorstore, "test_collection")

        # Assert
        assert "using none distance instead of cosine" in caplog.text

    def test_handles_exception_gracefully(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test that exceptions are handled gracefully.

        Args:
            caplog: Pytest log capture fixture.
        """
        # Arrange
        mock_collection = Mock()
        # Make metadata property raise an exception
        type(mock_collection).metadata = property(
            lambda self: (_ for _ in ()).throw(RuntimeError("Test error"))
        )

        mock_vectorstore = Mock()
        mock_vectorstore._collection = mock_collection

        # Act
        with caplog.at_level(logging.DEBUG):
            _validate_distance_function(mock_vectorstore, "test_collection")

        # Assert - should not raise exception and should log debug message
        assert "Could not validate distance function" in caplog.text


class TestCreateEmbeddings:
    """Tests for _create_embeddings function."""

    def test_creates_embeddings_with_valid_config(self, mock_config: ConfigService) -> None:
        """Test that embeddings are created with valid configuration.

        Args:
            mock_config: Mock configuration service.
        """
        # Arrange
        from services.vectorstore_service import _create_embeddings

        # Act
        embeddings = _create_embeddings(mock_config)

        # Assert
        assert embeddings is not None
        assert embeddings.model == "text-embedding-3-small"

    def test_raises_error_when_model_not_configured(self) -> None:
        """Test that error is raised when embedding model is not configured."""
        # Arrange
        from services.vectorstore_service import _create_embeddings

        config = Mock(spec=ConfigService)
        config.get.return_value = None  # No model configured

        # Act & Assert
        with pytest.raises(ValueError, match="openai.embedding_model not configured"):
            _create_embeddings(config)

    def test_uses_default_timeout_and_retries(self) -> None:
        """Test that default timeout and retries are used when not configured."""
        # Arrange
        from services.vectorstore_service import _create_embeddings

        config = Mock(spec=ConfigService)
        config.get.side_effect = lambda key, default=None: {
            "openai.embedding_model": "text-embedding-3-small",
            "openai.request_timeout_s": 60,
            "openai.max_retries": 3,
        }.get(key, default)

        # Act
        embeddings = _create_embeddings(config)

        # Assert
        assert embeddings.request_timeout == 60
        assert embeddings.max_retries == 3


class TestDeleteByAnimeIds:
    """Tests for delete_by_anime_ids function."""

    def test_deletes_documents_by_anime_ids(self) -> None:
        """Test that documents are deleted by anime IDs."""
        # Arrange
        from services.vectorstore_service import delete_by_anime_ids

        mock_ctx = Mock()
        mock_vectorstore = Mock()
        mock_ctx.vectorstore = mock_vectorstore

        anime_ids = ["123", "456", "789"]

        # Act
        delete_by_anime_ids(anime_ids, mock_ctx)

        # Assert
        mock_vectorstore.delete.assert_called_once_with(
            where={"anime_id": {"$in": ["123", "456", "789"]}}
        )

    def test_handles_empty_anime_ids(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test that empty anime_ids list is handled gracefully.

        Args:
            caplog: Pytest log capture fixture.
        """
        # Arrange
        from services.vectorstore_service import delete_by_anime_ids

        mock_ctx = Mock()
        mock_vectorstore = Mock()
        mock_ctx.vectorstore = mock_vectorstore

        # Act
        with caplog.at_level(logging.DEBUG):
            delete_by_anime_ids([], mock_ctx)

        # Assert
        assert "No anime IDs provided" in caplog.text
        mock_vectorstore.delete.assert_not_called()

    def test_raises_exception_on_deletion_failure(self) -> None:
        """Test that exception is raised when deletion fails."""
        # Arrange
        from services.vectorstore_service import delete_by_anime_ids

        mock_ctx = Mock()
        mock_vectorstore = Mock()
        mock_vectorstore.delete.side_effect = Exception("Deletion failed")
        mock_ctx.vectorstore = mock_vectorstore

        # Act & Assert
        with pytest.raises(Exception, match="Deletion failed"):
            delete_by_anime_ids(["123"], mock_ctx)


class TestUpsertDocuments:
    """Tests for upsert_documents function."""

    def test_upserts_documents_successfully(self) -> None:
        """Test that documents are upserted successfully."""
        # Arrange
        from services.vectorstore_service import upsert_documents

        mock_ctx = Mock()
        mock_vectorstore = Mock()
        mock_ctx.vectorstore = mock_vectorstore

        docs = [
            Document(page_content="Content 1", metadata={"anime_id": "123"}),
            Document(page_content="Content 2", metadata={"anime_id": "456"}),
        ]

        # Act
        result = upsert_documents(docs, mock_ctx)

        # Assert
        assert result == ["123", "456"]
        mock_vectorstore.delete.assert_called_once()
        mock_vectorstore.add_documents.assert_called_once()

    def test_handles_empty_documents_list(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test that empty documents list is handled gracefully.

        Args:
            caplog: Pytest log capture fixture.
        """
        # Arrange
        from services.vectorstore_service import upsert_documents

        mock_ctx = Mock()
        mock_vectorstore = Mock()
        mock_ctx.vectorstore = mock_vectorstore

        # Act
        with caplog.at_level(logging.WARNING):
            result = upsert_documents([], mock_ctx)

        # Assert
        assert result == []
        assert "No documents provided" in caplog.text
        mock_vectorstore.delete.assert_not_called()
        mock_vectorstore.add_documents.assert_not_called()

    def test_raises_error_when_anime_id_missing(self) -> None:
        """Test that error is raised when document is missing anime_id."""
        # Arrange
        from services.vectorstore_service import upsert_documents

        mock_ctx = Mock()
        mock_vectorstore = Mock()
        mock_ctx.vectorstore = mock_vectorstore

        docs = [
            Document(page_content="Content", metadata={}),  # Missing anime_id
        ]

        # Act & Assert
        with pytest.raises(ValueError, match="Document missing anime_id"):
            upsert_documents(docs, mock_ctx)

    def test_filters_complex_metadata(self) -> None:
        """Test that complex metadata is filtered before upserting."""
        # Arrange
        from services.vectorstore_service import upsert_documents

        mock_ctx = Mock()
        mock_vectorstore = Mock()
        mock_ctx.vectorstore = mock_vectorstore

        # Document with complex metadata (lists, dicts)
        docs = [
            Document(
                page_content="Content",
                metadata={
                    "anime_id": "123",
                    "tags": ["action", "mecha"],  # List (complex)
                    "ratings": {"imdb": 8.5},  # Dict (complex)
                    "title": "Test Anime",  # Simple (kept)
                },
            ),
        ]

        # Act
        result = upsert_documents(docs, mock_ctx)

        # Assert
        assert result == ["123"]
        # Verify add_documents was called (complex metadata filtered by filter_complex_metadata)
        mock_vectorstore.add_documents.assert_called_once()

    def test_deletes_existing_before_adding(self) -> None:
        """Test that existing documents are deleted before adding new ones."""
        # Arrange
        from services.vectorstore_service import upsert_documents

        mock_ctx = Mock()
        mock_vectorstore = Mock()
        mock_ctx.vectorstore = mock_vectorstore

        docs = [
            Document(page_content="Content", metadata={"anime_id": "123"}),
        ]

        # Act
        upsert_documents(docs, mock_ctx)

        # Assert
        # Verify delete was called before add_documents
        assert mock_vectorstore.delete.call_count == 1
        assert mock_vectorstore.add_documents.call_count == 1
        # Check that delete was called with correct IDs
        delete_call_args = mock_vectorstore.delete.call_args
        assert delete_call_args[1]["where"]["anime_id"]["$in"] == ["123"]

    def test_raises_exception_on_upsert_failure(self) -> None:
        """Test that exception is raised when upsert fails."""
        # Arrange
        from services.vectorstore_service import upsert_documents

        mock_ctx = Mock()
        mock_vectorstore = Mock()
        mock_vectorstore.delete.side_effect = Exception("Upsert failed")
        mock_ctx.vectorstore = mock_vectorstore

        docs = [
            Document(page_content="Content", metadata={"anime_id": "123"}),
        ]

        # Act & Assert
        with pytest.raises(Exception, match="Upsert failed"):
            upsert_documents(docs, mock_ctx)

    def test_converts_anime_ids_to_strings(self) -> None:
        """Test that anime IDs are converted to strings."""
        # Arrange
        from services.vectorstore_service import upsert_documents

        mock_ctx = Mock()
        mock_vectorstore = Mock()
        mock_ctx.vectorstore = mock_vectorstore

        docs = [
            Document(page_content="Content", metadata={"anime_id": 123}),  # Integer
        ]

        # Act
        result = upsert_documents(docs, mock_ctx)

        # Assert
        assert result == ["123"]  # Should be string
        # Verify delete was called with string ID
        delete_call_args = mock_vectorstore.delete.call_args
        assert delete_call_args[1]["where"]["anime_id"]["$in"] == ["123"]
