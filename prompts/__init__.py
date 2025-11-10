"""Prompt templates for LLM interactions.

This module manages all prompt templates used in the application,
making them easy to version, test, and modify without changing code.
"""

from prompts.anime_rag import (
    ANIME_RAG_SYSTEM_PROMPT,
    build_anime_rag_json_prompt,
    build_anime_rag_prompt,
)

__all__ = [
    "ANIME_RAG_SYSTEM_PROMPT",
    "build_anime_rag_prompt",
    "build_anime_rag_json_prompt",
]
