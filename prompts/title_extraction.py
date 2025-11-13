"""Prompt templates for extracting anime titles from natural language queries.

This module contains prompts for identifying anime titles in user queries
when regex patterns fail to match.
"""

from langchain_core.prompts import ChatPromptTemplate

# Version: 1.0
# Last Updated: 2025-11-11
# Purpose: Extract anime title from natural language query
TITLE_EXTRACTION_SYSTEM_PROMPT = """You are an anime title extraction assistant.

Your task is to identify and extract the anime title from a user's natural language query.

Guidelines:
- Extract ONLY the anime title, nothing else
- Remove question words and phrases (e.g., "tell me about", "what is", etc.)
- Remove punctuation at the end
- Preserve the original capitalization and special characters in the title
- If multiple anime are mentioned, extract only the primary one
- If no anime title is found, return the original query unchanged

Examples:
- "Tell me about Cowboy Bebop" → "Cowboy Bebop"
- "What's the plot of Neon Genesis Evangelion?" → "Neon Genesis Evangelion"
- "I want to know more about the anime Steins;Gate" → "Steins;Gate"
- "Can you recommend something like Attack on Titan" → "Attack on Titan"
- "mecha anime recommendations" → "mecha anime recommendations" (no specific title)

Return ONLY the extracted title, with no explanation or additional text.
"""


def build_title_extraction_prompt() -> ChatPromptTemplate:
    """Build the title extraction prompt template.

    Returns:
        ChatPromptTemplate configured for extracting anime titles from queries.

    Examples:
        >>> prompt = build_title_extraction_prompt()
        >>> messages = prompt.format_messages(
        ...     query="Tell me about the anime called Cowboy Bebop"
        ... )
    """
    return ChatPromptTemplate.from_messages(
        [
            ("system", TITLE_EXTRACTION_SYSTEM_PROMPT),
            ("human", "Extract the anime title from this query:\n\n{query}"),
        ]
    )
