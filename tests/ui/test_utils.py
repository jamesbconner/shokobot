"""Unit tests for UI utility functions."""

import os
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from ui.utils import format_error_message, initialize_rag_chain, validate_environment


class TestValidateEnvironment:
    """Tests for validate_environment function."""

    def test_validate_environment_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test successful environment validation."""
        # Set required environment variable
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")

        # Mock the Path.exists to return True (vector store exists)
        with patch("pathlib.Path.exists", return_value=True):
            # Should not raise any exception
            validate_environment()

    def test_validate_environment_missing_api_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test validation fails when API key is missing."""
        # Ensure API key is not set
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        with pytest.raises(EnvironmentError, match="OPENAI_API_KEY"):
            validate_environment()

    def test_validate_environment_missing_vector_store(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test validation fails when vector store is missing."""
        # Set API key
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")

        # Ensure .chroma doesn't exist
        with patch("pathlib.Path.exists", return_value=False):
            with pytest.raises(EnvironmentError, match="Vector store not found"):
                validate_environment()


class TestInitializeRagChain:
    """Tests for initialize_rag_chain function."""

    def test_initialize_rag_chain_success(self, mock_context: Mock) -> None:
        """Test successful RAG chain initialization."""
        # Mock the rag_chain property
        mock_chain = Mock()
        mock_context.rag_chain = mock_chain

        result = initialize_rag_chain(mock_context)

        assert result == mock_chain

    def test_initialize_rag_chain_failure(self, mock_context: Mock) -> None:
        """Test RAG chain initialization failure."""
        # Make rag_chain property raise an exception
        type(mock_context).rag_chain = property(
            lambda self: (_ for _ in ()).throw(ValueError("Test error"))
        )

        with pytest.raises(RuntimeError, match="Failed to initialize RAG chain"):
            initialize_rag_chain(mock_context)


class TestFormatErrorMessage:
    """Tests for format_error_message function."""

    def test_format_environment_error(self) -> None:
        """Test formatting of EnvironmentError (OSError in Python 3.3+)."""
        error = OSError("API key not set")
        message = format_error_message(error)

        # OSError is not in the error_messages dict, so it returns generic message
        assert "unexpected error" in message.lower()

    def test_format_runtime_error(self) -> None:
        """Test formatting of RuntimeError."""
        error = RuntimeError("Initialization failed")
        message = format_error_message(error)

        assert message == "Initialization failed"

    def test_format_value_error(self) -> None:
        """Test formatting of ValueError."""
        error = ValueError("Invalid input")
        message = format_error_message(error)

        assert message == "Invalid input. Please check your query and try again."

    def test_format_connection_error(self) -> None:
        """Test formatting of ConnectionError."""
        error = ConnectionError("Connection failed")
        message = format_error_message(error)

        assert message == "Unable to connect to required services. Please check your connection."

    def test_format_timeout_error(self) -> None:
        """Test formatting of TimeoutError."""
        error = TimeoutError("Request timed out")
        message = format_error_message(error)

        assert message == "Request timed out. Please try again."

    def test_format_unknown_error(self) -> None:
        """Test formatting of unknown error type."""
        error = KeyError("Unknown key")
        message = format_error_message(error)

        assert message == "An unexpected error occurred. Please try again."

    def test_format_error_logs_details(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test that error details are logged."""
        error = ValueError("Test error")

        with caplog.at_level("ERROR"):
            format_error_message(error)

        assert "ValueError" in caplog.text
        assert "Test error" in caplog.text
