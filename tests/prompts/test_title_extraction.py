"""Tests for title extraction prompt templates.

This module tests prompt template creation and formatting for extracting
anime titles from natural language queries.
"""

from langchain_core.prompts import ChatPromptTemplate

from prompts.title_extraction import (
    TITLE_EXTRACTION_SYSTEM_PROMPT,
    build_title_extraction_prompt,
)


class TestTitleExtractionSystemPrompt:
    """Tests for TITLE_EXTRACTION_SYSTEM_PROMPT constant."""

    def test_system_prompt_exists(self) -> None:
        """Test that system prompt constant exists and is not empty."""
        assert isinstance(TITLE_EXTRACTION_SYSTEM_PROMPT, str)
        assert len(TITLE_EXTRACTION_SYSTEM_PROMPT) > 0

    def test_system_prompt_contains_key_instructions(self) -> None:
        """Test that system prompt contains key instructions."""
        prompt_lower = TITLE_EXTRACTION_SYSTEM_PROMPT.lower()
        
        # Should mention anime
        assert "anime" in prompt_lower
        
        # Should mention extraction
        assert "extract" in prompt_lower
        
        # Should mention title
        assert "title" in prompt_lower
        
        # Should have guidelines
        assert "guidelines" in prompt_lower or "task" in prompt_lower

    def test_system_prompt_has_examples(self) -> None:
        """Test that system prompt includes examples."""
        # Should have example patterns
        assert "Examples:" in TITLE_EXTRACTION_SYSTEM_PROMPT or "Example:" in TITLE_EXTRACTION_SYSTEM_PROMPT
        
        # Should show input/output format
        assert "→" in TITLE_EXTRACTION_SYSTEM_PROMPT or "->" in TITLE_EXTRACTION_SYSTEM_PROMPT


class TestBuildTitleExtractionPrompt:
    """Tests for build_title_extraction_prompt function."""

    def test_build_prompt_returns_chat_prompt_template(self) -> None:
        """Test that function returns ChatPromptTemplate instance."""
        prompt = build_title_extraction_prompt()
        
        assert isinstance(prompt, ChatPromptTemplate)

    def test_prompt_has_required_variable(self) -> None:
        """Test that prompt template has 'query' variable."""
        prompt = build_title_extraction_prompt()
        
        variables = prompt.input_variables
        
        assert "query" in variables
        assert len(variables) == 1  # Should only have 'query'

    def test_prompt_has_system_and_human_messages(self) -> None:
        """Test that prompt contains both system and human message types."""
        prompt = build_title_extraction_prompt()
        
        messages = prompt.format_messages(query="test query")
        
        assert len(messages) == 2
        assert messages[0].type == "system"
        assert messages[1].type == "human"

    def test_prompt_system_message_content(self) -> None:
        """Test that system message contains expected content."""
        prompt = build_title_extraction_prompt()
        
        messages = prompt.format_messages(query="test query")
        system_content = str(messages[0].content)
        
        # Should be the system prompt constant
        assert system_content == TITLE_EXTRACTION_SYSTEM_PROMPT

    def test_prompt_human_message_includes_query(self) -> None:
        """Test that human message includes the query."""
        prompt = build_title_extraction_prompt()
        
        test_query = "Tell me about Cowboy Bebop"
        messages = prompt.format_messages(query=test_query)
        human_content = str(messages[1].content)
        
        assert test_query in human_content
        assert "Extract" in human_content or "extract" in human_content

    def test_prompt_formatting_with_various_queries(self) -> None:
        """Test prompt formatting with different query types."""
        prompt = build_title_extraction_prompt()
        
        test_queries = [
            "What is Neon Genesis Evangelion about?",
            "Tell me about the anime Steins;Gate",
            "I want to watch Attack on Titan",
            "mecha anime recommendations",
            "進撃の巨人について教えて",  # Japanese query
        ]
        
        for query in test_queries:
            messages = prompt.format_messages(query=query)
            
            assert len(messages) == 2
            assert query in str(messages[1].content)

    def test_prompt_with_empty_query(self) -> None:
        """Test prompt formatting with empty query."""
        prompt = build_title_extraction_prompt()
        
        messages = prompt.format_messages(query="")
        
        assert len(messages) == 2
        # Should still format without error

    def test_prompt_with_special_characters(self) -> None:
        """Test prompt formatting with special characters in query."""
        prompt = build_title_extraction_prompt()
        
        query = "What about anime with 'quotes' and \"double quotes\"?"
        messages = prompt.format_messages(query=query)
        
        assert len(messages) == 2
        assert "quotes" in str(messages[1].content)

    def test_prompt_with_unicode_characters(self) -> None:
        """Test prompt formatting with unicode/Japanese characters."""
        prompt = build_title_extraction_prompt()
        
        query = "進撃の巨人 (Attack on Titan) について"
        messages = prompt.format_messages(query=query)
        
        assert len(messages) == 2
        assert "進撃の巨人" in str(messages[1].content)

    def test_prompt_with_very_long_query(self) -> None:
        """Test prompt formatting with very long query."""
        prompt = build_title_extraction_prompt()
        
        query = "A" * 1000  # Very long query
        messages = prompt.format_messages(query=query)
        
        assert len(messages) == 2
        assert query in str(messages[1].content)

    def test_prompt_with_multiline_query(self) -> None:
        """Test prompt formatting with multiline query."""
        prompt = build_title_extraction_prompt()
        
        query = "Tell me about\nCowboy Bebop\nplease"
        messages = prompt.format_messages(query=query)
        
        assert len(messages) == 2
        assert "Cowboy Bebop" in str(messages[1].content)


class TestPromptStructure:
    """Tests for prompt structure and consistency."""

    def test_prompt_message_order(self) -> None:
        """Test that messages are in correct order (system, then human)."""
        prompt = build_title_extraction_prompt()
        
        messages = prompt.format_messages(query="test")
        
        # First message should be system
        assert messages[0].type == "system"
        # Second message should be human
        assert messages[1].type == "human"

    def test_prompt_is_reusable(self) -> None:
        """Test that prompt can be used multiple times."""
        prompt = build_title_extraction_prompt()
        
        # Format with different queries
        messages1 = prompt.format_messages(query="query 1")
        messages2 = prompt.format_messages(query="query 2")
        
        # Both should work
        assert len(messages1) == 2
        assert len(messages2) == 2
        
        # Should have different content
        assert "query 1" in str(messages1[1].content)
        assert "query 2" in str(messages2[1].content)

    def test_system_prompt_mentions_extraction_task(self) -> None:
        """Test that system prompt clearly describes the extraction task."""
        prompt_lower = TITLE_EXTRACTION_SYSTEM_PROMPT.lower()
        
        # Should describe what to do
        assert any(word in prompt_lower for word in ["extract", "identify", "find"])
        
        # Should mention what to extract
        assert "title" in prompt_lower
        
        # Should mention the source
        assert "query" in prompt_lower or "question" in prompt_lower

    def test_system_prompt_has_clear_guidelines(self) -> None:
        """Test that system prompt provides clear guidelines."""
        # Should have bullet points or numbered list
        assert "-" in TITLE_EXTRACTION_SYSTEM_PROMPT or "•" in TITLE_EXTRACTION_SYSTEM_PROMPT
        
        # Should mention what to remove
        assert "remove" in TITLE_EXTRACTION_SYSTEM_PROMPT.lower()
        
        # Should mention what to preserve
        assert "preserve" in TITLE_EXTRACTION_SYSTEM_PROMPT.lower() or "keep" in TITLE_EXTRACTION_SYSTEM_PROMPT.lower()


class TestPromptEdgeCases:
    """Tests for edge cases in prompt usage."""

    def test_prompt_with_html_in_query(self) -> None:
        """Test prompt with HTML tags in query."""
        prompt = build_title_extraction_prompt()
        
        query = "What about <b>Cowboy Bebop</b>?"
        messages = prompt.format_messages(query=query)
        
        assert len(messages) == 2
        assert "Cowboy Bebop" in str(messages[1].content)

    def test_prompt_with_newlines_and_tabs(self) -> None:
        """Test prompt with newlines and tabs in query."""
        prompt = build_title_extraction_prompt()
        
        query = "Tell me\tabout\nCowboy\tBebop"
        messages = prompt.format_messages(query=query)
        
        assert len(messages) == 2

    def test_prompt_with_emoji(self) -> None:
        """Test prompt with emoji in query."""
        prompt = build_title_extraction_prompt()
        
        query = "What's 🎌 Cowboy Bebop about? 🚀"
        messages = prompt.format_messages(query=query)
        
        assert len(messages) == 2
        assert "Cowboy Bebop" in str(messages[1].content)

    def test_prompt_with_numbers_and_symbols(self) -> None:
        """Test prompt with numbers and symbols."""
        prompt = build_title_extraction_prompt()
        
        query = "Tell me about anime #1: Steins;Gate (2011) @best"
        messages = prompt.format_messages(query=query)
        
        assert len(messages) == 2
        assert "Steins;Gate" in str(messages[1].content)
