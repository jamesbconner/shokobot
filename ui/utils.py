"""Helper functions for the UI."""

import logging
import os
from pathlib import Path
from typing import Any

from services.app_context import AppContext

logger = logging.getLogger(__name__)


def validate_environment() -> None:
    """Validate required environment variables are set.

    Raises:
        EnvironmentError: If required variables are missing.
    """
    if not os.getenv("OPENAI_API_KEY"):
        raise EnvironmentError(
            "OPENAI_API_KEY environment variable not set. "
            "Please set it in your .env file or environment."
        )

    # Check if vector store exists
    chroma_path = Path(".chroma")
    if not chroma_path.exists():
        raise EnvironmentError(
            "Vector store not found. Please run 'shokobot ingest' first to initialize the database."
        )


def initialize_rag_chain(ctx: AppContext) -> Any:
    """Initialize the RAG chain with error handling.

    Args:
        ctx: Application context.

    Returns:
        Configured RAG chain.

    Raises:
        RuntimeError: If initialization fails.
    """
    try:
        logger.info("Initializing RAG chain...")
        chain = ctx.rag_chain
        logger.info("RAG chain initialized successfully")
        return chain
    except Exception as e:
        logger.error(f"Failed to initialize RAG chain: {e}")
        raise RuntimeError(f"Failed to initialize RAG chain: {e}") from e


def format_error_message(error: Exception) -> str:
    """Format error messages for user display.

    Args:
        error: Exception that occurred.

    Returns:
        User-friendly error message.
    """
    error_type = type(error).__name__

    # Map exception types to user-friendly messages
    error_messages = {
        "EnvironmentError": str(error),
        "RuntimeError": str(error),
        "ValueError": "Invalid input. Please check your query and try again.",
        "ConnectionError": "Unable to connect to required services. Please check your connection.",
        "TimeoutError": "Request timed out. Please try again.",
    }

    # Get user-friendly message or use generic one
    user_message = error_messages.get(error_type, "An unexpected error occurred. Please try again.")

    # Log the full error for debugging
    logger.error(f"Error ({error_type}): {error}", exc_info=True)

    return user_message
