"""Tests for anime RAG prompt templates.

This module tests prompt template creation, formatting, and message structure
for various anime query scenarios.
"""

from langchain_core.prompts import ChatPromptTemplate

from prompts.anime_rag import (
    build_anime_rag_prompt,
    build_detailed_anime_prompt,
    build_recommendation_prompt,
)


class TestBuildAnimeRagPrompt:
    """Tests for build_anime_rag_prompt function."""

    def test_build_anime_rag_prompt_returns_template(self) -> None:
        """Test that build_anime_rag_prompt returns ChatPromptTemplate."""
        # Act
        result = build_anime_rag_prompt()

        # Assert
        assert isinstance(result, ChatPromptTemplate)

    def test_prompt_has_required_variables(self) -> None:
        """Test that prompt template has question and context variables."""
        # Arrange
        prompt = build_anime_rag_prompt()

        # Act
        variables = prompt.input_variables

        # Assert
        assert "question" in variables
        assert "context" in variables

    def test_prompt_formatting_with_values(self) -> None:
        """Test that prompt formats correctly with question and context."""
        # Arrange
        prompt = build_anime_rag_prompt()
        question = "What is Cowboy Bebop about?"
        context = "Cowboy Bebop: A space western anime from 1998."

        # Act
        messages = prompt.format_messages(question=question, context=context)

        # Assert
        assert len(messages) >= 2
        # Verify question appears in formatted output
        human_message = str(messages[-1].content)
        assert question in human_message
        assert context in human_message

    def test_prompt_has_system_and_human_messages(self) -> None:
        """Test that prompt contains both system and human message types."""
        # Arrange
        prompt = build_anime_rag_prompt()

        # Act
        messages = prompt.format_messages(question="Test question", context="Test context")

        # Assert
        assert len(messages) == 2
        assert messages[0].type == "system"
        assert messages[1].type == "human"

    def test_prompt_system_message_content(self) -> None:
        """Test that system message contains expected guidelines."""
        # Arrange
        prompt = build_anime_rag_prompt()

        # Act
        messages = prompt.format_messages(question="Test question", context="Test context")
        system_content = str(messages[0].content)

        # Assert
        assert "anime" in system_content.lower()
        assert "context" in system_content.lower()

    def test_prompt_formatting_with_empty_context(self) -> None:
        """Test prompt formatting with empty context."""
        # Arrange
        prompt = build_anime_rag_prompt()
        question = "What anime should I watch?"
        context = ""

        # Act
        messages = prompt.format_messages(question=question, context=context)

        # Assert
        assert len(messages) == 2
        human_message = str(messages[-1].content)
        assert question in human_message

    def test_prompt_formatting_with_multiline_context(self) -> None:
        """Test prompt formatting with multiline context."""
        # Arrange
        prompt = build_anime_rag_prompt()
        question = "Compare these anime"
        context = """Anime 1: Title, Description

Anime 2: Title, Description

Anime 3: Title, Description"""

        # Act
        messages = prompt.format_messages(question=question, context=context)

        # Assert
        assert len(messages) == 2
        human_message = str(messages[-1].content)
        assert "Anime 1" in human_message
        assert "Anime 2" in human_message
        assert "Anime 3" in human_message


class TestBuildDetailedAnimePrompt:
    """Tests for build_detailed_anime_prompt function."""

    def test_build_detailed_anime_prompt_returns_template(self) -> None:
        """Test that build_detailed_anime_prompt returns ChatPromptTemplate."""
        # Act
        result = build_detailed_anime_prompt()

        # Assert
        assert isinstance(result, ChatPromptTemplate)

    def test_detailed_prompt_has_required_variables(self) -> None:
        """Test that detailed prompt has question and context variables."""
        # Arrange
        prompt = build_detailed_anime_prompt()

        # Act
        variables = prompt.input_variables

        # Assert
        assert "question" in variables
        assert "context" in variables

    def test_detailed_prompt_formatting(self) -> None:
        """Test that detailed prompt formats correctly."""
        # Arrange
        prompt = build_detailed_anime_prompt()
        question = "Explain the themes in this anime"
        context = "Anime with complex themes"

        # Act
        messages = prompt.format_messages(question=question, context=context)

        # Assert
        assert len(messages) == 2
        assert messages[0].type == "system"
        assert messages[1].type == "human"

    def test_detailed_prompt_has_different_system_message(self) -> None:
        """Test that detailed prompt has different system message than basic."""
        # Arrange
        basic_prompt = build_anime_rag_prompt()
        detailed_prompt = build_detailed_anime_prompt()

        # Act
        basic_messages = basic_prompt.format_messages(question="test", context="test")
        detailed_messages = detailed_prompt.format_messages(question="test", context="test")

        # Assert
        basic_system = str(basic_messages[0].content)
        detailed_system = str(detailed_messages[0].content)
        assert basic_system != detailed_system


class TestBuildRecommendationPrompt:
    """Tests for build_recommendation_prompt function."""

    def test_build_recommendation_prompt_returns_template(self) -> None:
        """Test that build_recommendation_prompt returns ChatPromptTemplate."""
        # Act
        result = build_recommendation_prompt()

        # Assert
        assert isinstance(result, ChatPromptTemplate)

    def test_recommendation_prompt_has_required_variables(self) -> None:
        """Test that recommendation prompt has question and context variables."""
        # Arrange
        prompt = build_recommendation_prompt()

        # Act
        variables = prompt.input_variables

        # Assert
        assert "question" in variables
        assert "context" in variables

    def test_recommendation_prompt_formatting(self) -> None:
        """Test that recommendation prompt formats correctly."""
        # Arrange
        prompt = build_recommendation_prompt()
        question = "Recommend action anime"
        context = "Action anime list with ratings"

        # Act
        messages = prompt.format_messages(question=question, context=context)

        # Assert
        assert len(messages) == 2
        assert messages[0].type == "system"
        assert messages[1].type == "human"

    def test_recommendation_prompt_system_message_mentions_recommendations(
        self,
    ) -> None:
        """Test that recommendation prompt mentions recommendations in system message."""
        # Arrange
        prompt = build_recommendation_prompt()

        # Act
        messages = prompt.format_messages(question="test", context="test")
        system_content = str(messages[0].content).lower()

        # Assert
        assert "recommend" in system_content

    def test_all_prompts_have_consistent_structure(self) -> None:
        """Test that all prompt variants have consistent structure."""
        # Arrange
        prompts = [
            build_anime_rag_prompt(),
            build_detailed_anime_prompt(),
            build_recommendation_prompt(),
        ]

        # Act & Assert
        for prompt in prompts:
            messages = prompt.format_messages(question="test question", context="test context")
            # All should have 2 messages: system and human
            assert len(messages) == 2
            assert messages[0].type == "system"
            assert messages[1].type == "human"
            # All should have same variables
            assert "question" in prompt.input_variables
            assert "context" in prompt.input_variables


class TestPromptEdgeCases:
    """Tests for edge cases in prompt formatting."""

    def test_prompt_with_special_characters(self) -> None:
        """Test prompt formatting with special characters."""
        # Arrange
        prompt = build_anime_rag_prompt()
        question = "What about anime with 'quotes' and \"double quotes\"?"
        context = "Anime: Title with special chars: @#$%"

        # Act
        messages = prompt.format_messages(question=question, context=context)

        # Assert
        assert len(messages) == 2
        human_message = str(messages[-1].content)
        assert "quotes" in human_message

    def test_prompt_with_unicode_characters(self) -> None:
        """Test prompt formatting with unicode/Japanese characters."""
        # Arrange
        prompt = build_anime_rag_prompt()
        question = "What is 進撃の巨人 about?"
        context = "進撃の巨人 (Attack on Titan): Japanese anime"

        # Act
        messages = prompt.format_messages(question=question, context=context)

        # Assert
        assert len(messages) == 2
        human_message = str(messages[-1].content)
        assert "進撃の巨人" in human_message

    def test_prompt_with_very_long_context(self) -> None:
        """Test prompt formatting with very long context."""
        # Arrange
        prompt = build_anime_rag_prompt()
        question = "Tell me about these anime"
        # Create long context
        context = "\n\n".join([f"Anime {i}: Description" for i in range(100)])

        # Act
        messages = prompt.format_messages(question=question, context=context)

        # Assert
        assert len(messages) == 2
        human_message = str(messages[-1].content)
        assert "Anime 0" in human_message
        assert "Anime 99" in human_message


class TestBuildAnimeRagJsonPrompt:
    """Tests for build_anime_rag_json_prompt function."""

    def test_build_anime_rag_json_prompt_returns_template(self) -> None:
        """Test that build_anime_rag_json_prompt returns ChatPromptTemplate."""
        from prompts.anime_rag import build_anime_rag_json_prompt

        # Act
        result = build_anime_rag_json_prompt()

        # Assert
        assert isinstance(result, ChatPromptTemplate)

    def test_json_prompt_has_required_variables(self) -> None:
        """Test that JSON prompt has question and context variables."""
        from prompts.anime_rag import build_anime_rag_json_prompt

        # Arrange
        prompt = build_anime_rag_json_prompt()

        # Act
        variables = prompt.input_variables

        # Assert
        assert "question" in variables
        assert "context" in variables

    def test_json_prompt_system_message_mentions_json(self) -> None:
        """Test that JSON prompt mentions JSON in system message."""
        from prompts.anime_rag import build_anime_rag_json_prompt

        # Arrange
        prompt = build_anime_rag_json_prompt()

        # Act
        messages = prompt.format_messages(question="test", context="test")
        system_content = str(messages[0].content).lower()

        # Assert
        # OpenAI requires the word 'json' in the prompt
        assert "json" in system_content

    def test_json_prompt_formatting(self) -> None:
        """Test that JSON prompt formats correctly."""
        from prompts.anime_rag import build_anime_rag_json_prompt

        # Arrange
        prompt = build_anime_rag_json_prompt()
        question = "What is Cowboy Bebop about?"
        context = "Cowboy Bebop: A space western anime from 1998."

        # Act
        messages = prompt.format_messages(question=question, context=context)

        # Assert
        assert len(messages) == 2
        assert messages[0].type == "system"
        assert messages[1].type == "human"
        human_message = str(messages[-1].content)
        assert question in human_message
        assert context in human_message

    def test_json_prompt_has_answer_field_instruction(self) -> None:
        """Test that JSON prompt instructs to use 'answer' field."""
        from prompts.anime_rag import build_anime_rag_json_prompt

        # Arrange
        prompt = build_anime_rag_json_prompt()

        # Act
        messages = prompt.format_messages(question="test", context="test")
        system_content = str(messages[0].content).lower()

        # Assert
        assert "answer" in system_content


class TestPromptConstants:
    """Tests for prompt constant strings."""

    def test_anime_rag_system_prompt_exists(self) -> None:
        """Test that ANIME_RAG_SYSTEM_PROMPT constant exists."""
        from prompts.anime_rag import ANIME_RAG_SYSTEM_PROMPT

        assert isinstance(ANIME_RAG_SYSTEM_PROMPT, str)
        assert len(ANIME_RAG_SYSTEM_PROMPT) > 0

    def test_anime_rag_detailed_prompt_exists(self) -> None:
        """Test that ANIME_RAG_DETAILED_PROMPT constant exists."""
        from prompts.anime_rag import ANIME_RAG_DETAILED_PROMPT

        assert isinstance(ANIME_RAG_DETAILED_PROMPT, str)
        assert len(ANIME_RAG_DETAILED_PROMPT) > 0

    def test_anime_rag_recommendation_prompt_exists(self) -> None:
        """Test that ANIME_RAG_RECOMMENDATION_PROMPT constant exists."""
        from prompts.anime_rag import ANIME_RAG_RECOMMENDATION_PROMPT

        assert isinstance(ANIME_RAG_RECOMMENDATION_PROMPT, str)
        assert len(ANIME_RAG_RECOMMENDATION_PROMPT) > 0

    def test_anime_rag_json_prompt_exists(self) -> None:
        """Test that ANIME_RAG_JSON_PROMPT constant exists."""
        from prompts.anime_rag import ANIME_RAG_JSON_PROMPT

        assert isinstance(ANIME_RAG_JSON_PROMPT, str)
        assert len(ANIME_RAG_JSON_PROMPT) > 0

    def test_system_prompts_contain_key_instructions(self) -> None:
        """Test that system prompts contain key instructions."""
        from prompts.anime_rag import (
            ANIME_RAG_DETAILED_PROMPT,
            ANIME_RAG_RECOMMENDATION_PROMPT,
            ANIME_RAG_SYSTEM_PROMPT,
        )

        # All should mention context
        assert "context" in ANIME_RAG_SYSTEM_PROMPT.lower()
        assert "context" in ANIME_RAG_DETAILED_PROMPT.lower()
        assert "context" in ANIME_RAG_RECOMMENDATION_PROMPT.lower()

        # All should mention anime
        assert "anime" in ANIME_RAG_SYSTEM_PROMPT.lower()
        assert "anime" in ANIME_RAG_DETAILED_PROMPT.lower()
        assert "anime" in ANIME_RAG_RECOMMENDATION_PROMPT.lower()


class TestPromptComparison:
    """Tests comparing different prompt variants."""

    def test_all_prompts_have_same_input_variables(self) -> None:
        """Test that all prompt variants use the same input variables."""
        from prompts.anime_rag import (
            build_anime_rag_json_prompt,
            build_anime_rag_prompt,
            build_detailed_anime_prompt,
            build_recommendation_prompt,
        )

        prompts = [
            build_anime_rag_prompt(),
            build_detailed_anime_prompt(),
            build_recommendation_prompt(),
            build_anime_rag_json_prompt(),
        ]

        # All should have same variables
        for prompt in prompts:
            assert set(prompt.input_variables) == {"question", "context"}

    def test_all_prompts_have_different_system_messages(self) -> None:
        """Test that each prompt variant has a unique system message."""
        from prompts.anime_rag import (
            build_anime_rag_json_prompt,
            build_anime_rag_prompt,
            build_detailed_anime_prompt,
            build_recommendation_prompt,
        )

        prompts = [
            build_anime_rag_prompt(),
            build_detailed_anime_prompt(),
            build_recommendation_prompt(),
            build_anime_rag_json_prompt(),
        ]

        system_messages = []
        for prompt in prompts:
            messages = prompt.format_messages(question="test", context="test")
            system_messages.append(str(messages[0].content))

        # All system messages should be unique
        assert len(system_messages) == len(set(system_messages))

    def test_recommendation_prompt_differs_from_basic(self) -> None:
        """Test that recommendation prompt has distinct characteristics."""
        from prompts.anime_rag import (
            build_anime_rag_prompt,
            build_recommendation_prompt,
        )

        basic = build_anime_rag_prompt()
        recommendation = build_recommendation_prompt()

        basic_msgs = basic.format_messages(question="test", context="test")
        rec_msgs = recommendation.format_messages(question="test", context="test")

        basic_system = str(basic_msgs[0].content).lower()
        rec_system = str(rec_msgs[0].content).lower()

        # Recommendation should mention recommendations
        assert "recommend" in rec_system
        # Basic might not
        assert basic_system != rec_system

    def test_detailed_prompt_differs_from_basic(self) -> None:
        """Test that detailed prompt has distinct characteristics."""
        from prompts.anime_rag import (
            build_anime_rag_prompt,
            build_detailed_anime_prompt,
        )

        basic = build_anime_rag_prompt()
        detailed = build_detailed_anime_prompt()

        basic_msgs = basic.format_messages(question="test", context="test")
        detailed_msgs = detailed.format_messages(question="test", context="test")

        basic_system = str(basic_msgs[0].content)
        detailed_system = str(detailed_msgs[0].content)

        # Should be different
        assert basic_system != detailed_system
        # Detailed should be longer or have more instructions
        assert len(detailed_system) >= len(basic_system)


class TestPromptMessageStructure:
    """Tests for message structure consistency."""

    def test_all_prompts_produce_two_messages(self) -> None:
        """Test that all prompts produce exactly 2 messages."""
        from prompts.anime_rag import (
            build_anime_rag_json_prompt,
            build_anime_rag_prompt,
            build_detailed_anime_prompt,
            build_recommendation_prompt,
        )

        prompts = [
            build_anime_rag_prompt(),
            build_detailed_anime_prompt(),
            build_recommendation_prompt(),
            build_anime_rag_json_prompt(),
        ]

        for prompt in prompts:
            messages = prompt.format_messages(question="test", context="test")
            assert len(messages) == 2

    def test_all_prompts_have_system_then_human(self) -> None:
        """Test that all prompts follow system->human message order."""
        from prompts.anime_rag import (
            build_anime_rag_json_prompt,
            build_anime_rag_prompt,
            build_detailed_anime_prompt,
            build_recommendation_prompt,
        )

        prompts = [
            build_anime_rag_prompt(),
            build_detailed_anime_prompt(),
            build_recommendation_prompt(),
            build_anime_rag_json_prompt(),
        ]

        for prompt in prompts:
            messages = prompt.format_messages(question="test", context="test")
            assert messages[0].type == "system"
            assert messages[1].type == "human"

    def test_human_message_contains_both_question_and_context(self) -> None:
        """Test that human message contains both question and context."""
        from prompts.anime_rag import build_anime_rag_prompt

        prompt = build_anime_rag_prompt()
        question = "Unique question text"
        context = "Unique context text"

        messages = prompt.format_messages(question=question, context=context)
        human_message = str(messages[1].content)

        assert question in human_message
        assert context in human_message


class TestPromptRobustness:
    """Tests for prompt robustness with various inputs."""

    def test_prompts_handle_empty_strings(self) -> None:
        """Test that prompts handle empty strings gracefully."""
        from prompts.anime_rag import build_anime_rag_prompt

        prompt = build_anime_rag_prompt()

        # Should not raise exception
        messages = prompt.format_messages(question="", context="")
        assert len(messages) == 2

    def test_prompts_handle_newlines_in_question(self) -> None:
        """Test that prompts handle newlines in question."""
        from prompts.anime_rag import build_anime_rag_prompt

        prompt = build_anime_rag_prompt()
        question = "Line 1\nLine 2\nLine 3"

        messages = prompt.format_messages(question=question, context="test")
        human_message = str(messages[1].content)

        assert "Line 1" in human_message
        assert "Line 3" in human_message

    def test_prompts_handle_html_in_context(self) -> None:
        """Test that prompts handle HTML in context."""
        from prompts.anime_rag import build_anime_rag_prompt

        prompt = build_anime_rag_prompt()
        context = "<p>Anime with <b>HTML</b> tags</p>"

        messages = prompt.format_messages(question="test", context=context)
        human_message = str(messages[1].content)

        # HTML should be preserved in the message
        assert "HTML" in human_message

    def test_prompts_handle_very_long_inputs(self) -> None:
        """Test that prompts handle very long inputs."""
        from prompts.anime_rag import build_anime_rag_prompt

        prompt = build_anime_rag_prompt()
        question = "A" * 1000
        context = "B" * 10000

        # Should not raise exception
        messages = prompt.format_messages(question=question, context=context)
        assert len(messages) == 2
