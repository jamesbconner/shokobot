"""Prompt templates for anime RAG queries.

This module contains all prompt templates used for querying the anime database.
Prompts are versioned and can be easily modified without changing service code.
"""

from langchain_core.prompts import ChatPromptTemplate

# Version: 1.0
# Last Updated: 2025-11-10
# Purpose: Answer questions about anime using retrieved context
ANIME_RAG_SYSTEM_PROMPT = """You answer questions about anime TV shows using only the provided context.

Guidelines:
- Use ONLY information from the provided context
- Map aliases and alternate titles to the same show when present
- If multiple shows match, mention all relevant ones
- If no data is available, clearly state what information is missing
- Be concise but informative
- Include relevant details like episode count, year, and ratings when available

Context Format:
Each anime entry includes: title, alternate titles, description, tags, episodes, year, and ratings.
"""


def build_anime_rag_prompt() -> ChatPromptTemplate:
    """Build the anime RAG prompt template.

    Returns:
        ChatPromptTemplate configured for anime queries with context.

    Examples:
        >>> prompt = build_anime_rag_prompt()
        >>> messages = prompt.format_messages(
        ...     question="What is Cowboy Bebop about?",
        ...     context="Cowboy Bebop: A space western anime..."
        ... )
    """
    return ChatPromptTemplate.from_messages(
        [
            ("system", ANIME_RAG_SYSTEM_PROMPT),
            ("human", "{question}\n\nContext:\n{context}"),
        ]
    )


# Alternative prompts for different use cases

# Version: 1.0
# Purpose: More detailed responses with reasoning
ANIME_RAG_DETAILED_PROMPT = """You are an expert anime consultant helping users discover and understand anime.

Using the provided context, answer questions with:
1. Direct answer to the question
2. Supporting details from the context
3. Relevant comparisons or connections to other anime in the context
4. Any caveats or additional information that might be helpful

Guidelines:
- Use ONLY information from the provided context
- Map aliases and alternate titles to the same show
- Cite specific details (episode counts, years, ratings) when relevant
- If information is missing, explain what would be needed to answer fully

Context Format:
Each anime entry includes: title, alternate titles, description, tags, episodes, year, and ratings.
"""


def build_detailed_anime_prompt() -> ChatPromptTemplate:
    """Build a detailed anime RAG prompt for comprehensive responses.

    Returns:
        ChatPromptTemplate configured for detailed anime analysis.
    """
    return ChatPromptTemplate.from_messages(
        [
            ("system", ANIME_RAG_DETAILED_PROMPT),
            ("human", "{question}\n\nContext:\n{context}"),
        ]
    )


# Version: 1.0
# Purpose: Concise, recommendation-focused responses
ANIME_RAG_RECOMMENDATION_PROMPT = """You are an anime recommendation assistant.

Using the provided context, give concise recommendations that match the user's request.

Format your response as:
- List recommended anime titles
- Brief reason for each recommendation (1-2 sentences)
- Key details: year, episodes, rating

Guidelines:
- Use ONLY anime from the provided context
- Match user preferences to anime characteristics
- Prioritize highly-rated anime when relevant
- If no good matches exist, explain why

Context Format:
Each anime entry includes: title, alternate titles, description, tags, episodes, year, and ratings.
"""


def build_recommendation_prompt() -> ChatPromptTemplate:
    """Build a recommendation-focused prompt for anime suggestions.

    Returns:
        ChatPromptTemplate configured for anime recommendations.
    """
    return ChatPromptTemplate.from_messages(
        [
            ("system", ANIME_RAG_RECOMMENDATION_PROMPT),
            ("human", "{question}\n\nContext:\n{context}"),
        ]
    )
