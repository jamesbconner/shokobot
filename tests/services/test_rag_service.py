"""Tests for RAGService query logic and retrieval functionality.

This module tests retriever building, alias prefiltering, and RAG chain
construction with various query patterns and configurations.
"""

from unittest.mock import Mock, patch

import pytest

from services.rag_service import alias_prefilter, build_rag_chain, build_retriever


class TestBuildRetriever:
    """Tests for build_retriever function."""

    def test_build_retriever_default_parameters(self, mock_context: Mock) -> None:
        """Test retriever creation with default parameters."""
        # Arrange
        mock_vectorstore = Mock()
        mock_retriever = Mock()
        mock_vectorstore.as_retriever.return_value = mock_retriever
        mock_context.vectorstore = mock_vectorstore

        # Act
        result = build_retriever(mock_context)

        # Assert
        assert result is mock_retriever
        mock_vectorstore.as_retriever.assert_called_once_with(search_kwargs={"k": 10})

    def test_build_retriever_custom_k(self, mock_context: Mock) -> None:
        """Test retriever creation with custom k parameter."""
        # Arrange
        mock_vectorstore = Mock()
        mock_retriever = Mock()
        mock_vectorstore.as_retriever.return_value = mock_retriever
        mock_context.vectorstore = mock_vectorstore

        # Act
        result = build_retriever(mock_context, k=5)

        # Assert
        assert result is mock_retriever
        mock_vectorstore.as_retriever.assert_called_once_with(search_kwargs={"k": 5})

    def test_build_retriever_with_threshold(self, mock_context: Mock) -> None:
        """Test retriever creation with score_threshold parameter."""
        # Arrange
        mock_vectorstore = Mock()
        mock_retriever = Mock()
        mock_vectorstore.as_retriever.return_value = mock_retriever
        mock_context.vectorstore = mock_vectorstore

        # Act
        result = build_retriever(mock_context, k=10, score_threshold=0.7)

        # Assert
        assert result is mock_retriever
        mock_vectorstore.as_retriever.assert_called_once_with(
            search_kwargs={"k": 10, "score_threshold": 0.7}
        )

    def test_build_retriever_invalid_k(self, mock_context: Mock) -> None:
        """Test that invalid k raises ValueError."""
        # Act & Assert
        with pytest.raises(ValueError, match="k must be positive"):
            build_retriever(mock_context, k=0)

        with pytest.raises(ValueError, match="k must be positive"):
            build_retriever(mock_context, k=-1)

    def test_build_retriever_invalid_threshold(self, mock_context: Mock) -> None:
        """Test that invalid score_threshold raises ValueError."""
        # Act & Assert
        with pytest.raises(ValueError, match="score_threshold must be between 0 and 1"):
            build_retriever(mock_context, score_threshold=1.5)

        with pytest.raises(ValueError, match="score_threshold must be between 0 and 1"):
            build_retriever(mock_context, score_threshold=-0.1)

    def test_build_retriever_threshold_boundary_values(self, mock_context: Mock) -> None:
        """Test that boundary values for score_threshold are accepted."""
        # Arrange
        mock_vectorstore = Mock()
        mock_retriever = Mock()
        mock_vectorstore.as_retriever.return_value = mock_retriever
        mock_context.vectorstore = mock_vectorstore

        # Act & Assert: Test 0.0
        result = build_retriever(mock_context, score_threshold=0.0)
        assert result is mock_retriever

        # Act & Assert: Test 1.0
        result = build_retriever(mock_context, score_threshold=1.0)
        assert result is mock_retriever



class TestAliasPrefilter:
    """Tests for alias_prefilter function."""

    def test_alias_prefilter_quoted_phrase(self, mock_context: Mock) -> None:
        """Test exact title match with quoted phrase."""
        # Arrange
        mock_vectorstore = Mock()
        mock_docs = [Mock(), Mock()]
        mock_vectorstore.similarity_search.return_value = mock_docs
        mock_context.vectorstore = mock_vectorstore

        # Act
        result = alias_prefilter('"Exact Title"', mock_context)

        # Assert
        assert result == mock_docs
        mock_vectorstore.similarity_search.assert_called_once_with(
            '"Exact Title"', k=12, where={"title_main": {"$eq": "Exact Title"}}
        )

    def test_alias_prefilter_quoted_phrase_with_extra_text(
        self, mock_context: Mock
    ) -> None:
        """Test exact title match with quoted phrase and surrounding text."""
        # Arrange
        mock_vectorstore = Mock()
        mock_docs = [Mock()]
        mock_vectorstore.similarity_search.return_value = mock_docs
        mock_context.vectorstore = mock_vectorstore

        # Act
        result = alias_prefilter('show me "Test Anime" please', mock_context)

        # Assert
        assert result == mock_docs
        mock_vectorstore.similarity_search.assert_called_once_with(
            'show me "Test Anime" please', k=12, where={"title_main": {"$eq": "Test Anime"}}
        )

    def test_alias_prefilter_alias_prefix(self, mock_context: Mock) -> None:
        """Test alias search with 'alias:' prefix."""
        # Arrange
        mock_vectorstore = Mock()
        mock_docs = [Mock(), Mock(), Mock()]
        mock_vectorstore.similarity_search.return_value = mock_docs
        mock_context.vectorstore = mock_vectorstore

        # Act
        result = alias_prefilter("alias:TestName", mock_context)

        # Assert
        assert result == mock_docs
        mock_vectorstore.similarity_search.assert_called_once_with(
            "alias:TestName", k=12, where={"title_alts": {"$contains": "TestName"}}
        )

    def test_alias_prefilter_alias_prefix_with_spaces(self, mock_context: Mock) -> None:
        """Test alias search with spaces after prefix."""
        # Arrange
        mock_vectorstore = Mock()
        mock_docs = [Mock()]
        mock_vectorstore.similarity_search.return_value = mock_docs
        mock_context.vectorstore = mock_vectorstore

        # Act
        result = alias_prefilter("alias: TestName extra words", mock_context)

        # Assert
        assert result == mock_docs
        # Should only use first word after alias:
        mock_vectorstore.similarity_search.assert_called_once_with(
            "alias: TestName extra words",
            k=12,
            where={"title_alts": {"$contains": "TestName"}},
        )

    def test_alias_prefilter_content_search(self, mock_context: Mock) -> None:
        """Test default content search for plain text query."""
        # Arrange
        mock_vectorstore = Mock()
        mock_docs = [Mock(), Mock()]
        mock_vectorstore.similarity_search.return_value = mock_docs
        mock_context.vectorstore = mock_vectorstore

        # Act
        result = alias_prefilter("action anime with robots", mock_context)

        # Assert
        assert result == mock_docs
        mock_vectorstore.similarity_search.assert_called_once_with(
            "action anime with robots",
            k=12,
            where_document={"$contains": "action anime with robots"},
        )

    def test_alias_prefilter_custom_limit(self, mock_context: Mock) -> None:
        """Test prefilter with custom limit parameter."""
        # Arrange
        mock_vectorstore = Mock()
        mock_docs = [Mock()] * 5
        mock_vectorstore.similarity_search.return_value = mock_docs
        mock_context.vectorstore = mock_vectorstore

        # Act
        result = alias_prefilter("test query", mock_context, limit=5)

        # Assert
        assert result == mock_docs
        mock_vectorstore.similarity_search.assert_called_once_with(
            "test query", k=5, where_document={"$contains": "test query"}
        )

    def test_alias_prefilter_invalid_limit(self, mock_context: Mock) -> None:
        """Test that invalid limit raises ValueError."""
        # Act & Assert
        with pytest.raises(ValueError, match="limit must be positive"):
            alias_prefilter("test", mock_context, limit=0)

        with pytest.raises(ValueError, match="limit must be positive"):
            alias_prefilter("test", mock_context, limit=-1)

    def test_alias_prefilter_search_failure(self, mock_context: Mock) -> None:
        """Test that search failures return empty list."""
        # Arrange
        mock_vectorstore = Mock()
        mock_vectorstore.similarity_search.side_effect = Exception("Search failed")
        mock_context.vectorstore = mock_vectorstore

        # Act
        result = alias_prefilter("test query", mock_context)

        # Assert
        assert result == []

    def test_alias_prefilter_empty_quoted_phrase(self, mock_context: Mock) -> None:
        """Test handling of empty quoted phrase."""
        # Arrange
        mock_vectorstore = Mock()
        mock_docs = [Mock()]
        mock_vectorstore.similarity_search.return_value = mock_docs
        mock_context.vectorstore = mock_vectorstore

        # Act
        result = alias_prefilter('""', mock_context)

        # Assert
        # Should match with empty string
        assert result == mock_docs
        mock_vectorstore.similarity_search.assert_called_once_with(
            '""', k=12, where={"title_main": {"$eq": ""}}
        )



class TestBuildRagChain:
    """Tests for build_rag_chain function."""

    @patch("services.rag_service.build_retriever")
    @patch("services.rag_service.build_anime_rag_prompt")
    @patch("services.rag_service.ChatOpenAI")
    def test_build_rag_chain_valid_gpt5_model(
        self,
        mock_chat_class: Mock,
        mock_prompt_builder: Mock,
        mock_build_retriever: Mock,
        mock_context: Mock,
    ) -> None:
        """Test RAG chain construction with valid GPT-5 model."""
        # Arrange
        mock_context.config.get.side_effect = lambda key, default=None: {
            "openai.model": "gpt-5-nano",
        }.get(key, default)
        mock_context.config.get_reasoning_effort.return_value = "medium"
        mock_context.config.get_output_verbosity.return_value = "medium"
        mock_context.config.get_max_output_tokens.return_value = 4096

        mock_llm = Mock()
        mock_chat_class.return_value = mock_llm
        mock_prompt = Mock()
        mock_prompt_builder.return_value = mock_prompt
        mock_retriever = Mock()
        mock_build_retriever.return_value = mock_retriever

        # Act
        chain = build_rag_chain(mock_context)

        # Assert
        assert callable(chain)
        mock_chat_class.assert_called_once_with(
            model="gpt-5-nano",
            max_completion_tokens=4096,
            timeout=120,
            max_retries=3,
        )
        mock_build_retriever.assert_called_once_with(mock_context)

    def test_build_rag_chain_invalid_model(self, mock_context: Mock) -> None:
        """Test that non-GPT-5 model raises ValueError."""
        # Arrange
        mock_context.config.get.side_effect = lambda key, default=None: {
            "openai.model": "gpt-4-turbo",
        }.get(key, default)

        # Act & Assert
        with pytest.raises(ValueError, match="This service requires a GPT-5 model"):
            build_rag_chain(mock_context)

    def test_build_rag_chain_missing_model_config(self, mock_context: Mock) -> None:
        """Test that missing model configuration raises ValueError."""
        # Arrange
        mock_context.config.get.side_effect = lambda key, default=None: {
            "openai.model": None,
        }.get(key, default)

        # Act & Assert
        with pytest.raises(ValueError, match="openai.model not configured"):
            build_rag_chain(mock_context)

    @patch("services.rag_service.build_retriever")
    @patch("services.rag_service.build_anime_rag_prompt")
    @patch("services.rag_service.ChatOpenAI")
    def test_build_rag_chain_gpt5_variants(
        self,
        mock_chat_class: Mock,
        mock_prompt_builder: Mock,
        mock_build_retriever: Mock,
        mock_context: Mock,
    ) -> None:
        """Test that various GPT-5 model variants are accepted."""
        # Arrange
        gpt5_models = ["gpt-5-nano", "gpt-5-mini", "gpt-5", "gpt-5-turbo"]

        for model_name in gpt5_models:
            mock_context.config.get.side_effect = lambda key, default=None: {
                "openai.model": model_name,
                "openai.reasoning_effort": "medium",
                "openai.output_verbosity": "medium",
                "openai.max_output_tokens": 4096,
            }.get(key, default)

            mock_llm = Mock()
            mock_chat_class.return_value = mock_llm
            mock_prompt = Mock()
            mock_prompt_builder.return_value = mock_prompt
            mock_retriever = Mock()
            mock_build_retriever.return_value = mock_retriever

            # Act
            chain = build_rag_chain(mock_context)

            # Assert
            assert callable(chain)

    @patch("services.rag_service.build_retriever")
    @patch("services.rag_service.build_anime_rag_prompt")
    @patch("services.rag_service.ChatOpenAI")
    @patch("services.rag_service.alias_prefilter")
    def test_rag_chain_execution_empty_question(
        self,
        mock_prefilter: Mock,
        mock_chat_class: Mock,
        mock_prompt_builder: Mock,
        mock_build_retriever: Mock,
        mock_context: Mock,
    ) -> None:
        """Test that empty question raises ValueError."""
        # Arrange
        mock_context.config.get.side_effect = lambda key, default=None: {
            "openai.model": "gpt-5-nano",
            "openai.reasoning_effort": "medium",
            "openai.output_verbosity": "medium",
            "openai.max_output_tokens": 4096,
        }.get(key, default)

        mock_llm = Mock()
        mock_chat_class.return_value = mock_llm
        mock_prompt = Mock()
        mock_prompt_builder.return_value = mock_prompt
        mock_retriever = Mock()
        mock_build_retriever.return_value = mock_retriever

        # Act
        chain = build_rag_chain(mock_context)

        # Assert
        with pytest.raises(ValueError, match="Question cannot be empty"):
            chain("")

        with pytest.raises(ValueError, match="Question cannot be empty"):
            chain("   ")



class TestRagChainExecution:
    """Tests for RAG chain execution logic."""

    @patch("services.rag_service.build_retriever")
    @patch("services.rag_service.build_anime_rag_prompt")
    @patch("services.rag_service.ChatOpenAI")
    @patch("services.rag_service.alias_prefilter")
    def test_rag_chain_execution_success(
        self,
        mock_prefilter: Mock,
        mock_chat_class: Mock,
        mock_prompt_builder: Mock,
        mock_build_retriever: Mock,
        mock_context: Mock,
    ) -> None:
        """Test successful RAG chain execution with valid question."""
        # Arrange
        from langchain_core.documents import Document

        mock_context.config.get.side_effect = lambda key, default=None: {
            "openai.model": "gpt-5-nano",
            "openai.reasoning_effort": "medium",
            "openai.output_verbosity": "medium",
            "openai.max_output_tokens": 4096,
        }.get(key, default)

        # Mock documents
        mock_doc1 = Document(
            page_content="Anime 1 content", metadata={"anime_id": "1"}
        )
        mock_doc2 = Document(
            page_content="Anime 2 content", metadata={"anime_id": "2"}
        )

        # Mock prefilter and retriever
        mock_prefilter.return_value = [mock_doc1]
        mock_retriever = Mock()
        mock_retriever.invoke.return_value = [mock_doc2]
        mock_build_retriever.return_value = mock_retriever

        # Mock prompt
        mock_prompt = Mock()
        mock_messages = [Mock(), Mock()]
        mock_prompt.format_messages.return_value = mock_messages
        mock_prompt_builder.return_value = mock_prompt

        # Mock LLM response
        mock_llm = Mock()
        mock_response = Mock()
        mock_response.content = "This is the answer about anime."
        mock_llm.invoke.return_value = mock_response
        mock_chat_class.return_value = mock_llm

        # Act
        chain = build_rag_chain(mock_context)
        answer, docs = chain("What anime should I watch?")

        # Assert
        assert answer == "This is the answer about anime."
        assert len(docs) == 2
        assert docs[0].metadata["anime_id"] == "1"
        assert docs[1].metadata["anime_id"] == "2"
        mock_llm.invoke.assert_called_once()

    @patch("services.rag_service.build_retriever")
    @patch("services.rag_service.build_anime_rag_prompt")
    @patch("services.rag_service.ChatOpenAI")
    @patch("services.rag_service.alias_prefilter")
    def test_rag_chain_execution_with_list_response(
        self,
        mock_prefilter: Mock,
        mock_chat_class: Mock,
        mock_prompt_builder: Mock,
        mock_build_retriever: Mock,
        mock_context: Mock,
    ) -> None:
        """Test RAG chain execution with GPT-5 list response format."""
        # Arrange
        from langchain_core.documents import Document

        mock_context.config.get.side_effect = lambda key, default=None: {
            "openai.model": "gpt-5-nano",
            "openai.reasoning_effort": "medium",
            "openai.output_verbosity": "medium",
            "openai.max_output_tokens": 4096,
        }.get(key, default)

        mock_doc = Document(page_content="Test content", metadata={"anime_id": "1"})
        mock_prefilter.return_value = []
        mock_retriever = Mock()
        mock_retriever.invoke.return_value = [mock_doc]
        mock_build_retriever.return_value = mock_retriever

        mock_prompt = Mock()
        mock_prompt.format_messages.return_value = [Mock(), Mock()]
        mock_prompt_builder.return_value = mock_prompt

        # Mock LLM response with list content (GPT-5 format)
        mock_llm = Mock()
        mock_response = Mock()
        mock_response.content = [
            {"type": "reasoning", "text": "thinking..."},
            {"type": "text", "text": "Answer part 1"},
            {"text": "Answer part 2"},
            "Answer part 3",
        ]
        mock_llm.invoke.return_value = mock_response
        mock_chat_class.return_value = mock_llm

        # Act
        chain = build_rag_chain(mock_context)
        answer, docs = chain("Test question")

        # Assert
        assert answer == "Answer part 1Answer part 2Answer part 3"
        assert len(docs) == 1

    @patch("services.rag_service.build_retriever")
    @patch("services.rag_service.build_anime_rag_prompt")
    @patch("services.rag_service.ChatOpenAI")
    @patch("services.rag_service.alias_prefilter")
    def test_rag_chain_deduplicates_documents(
        self,
        mock_prefilter: Mock,
        mock_chat_class: Mock,
        mock_prompt_builder: Mock,
        mock_build_retriever: Mock,
        mock_context: Mock,
    ) -> None:
        """Test that RAG chain deduplicates documents by anime_id."""
        # Arrange
        from langchain_core.documents import Document

        mock_context.config.get.side_effect = lambda key, default=None: {
            "openai.model": "gpt-5-nano",
            "openai.reasoning_effort": "medium",
            "openai.output_verbosity": "medium",
            "openai.max_output_tokens": 4096,
        }.get(key, default)

        # Same anime_id in both prefilter and retriever results
        mock_doc1 = Document(page_content="Content 1", metadata={"anime_id": "1"})
        mock_doc2 = Document(page_content="Content 2", metadata={"anime_id": "1"})
        mock_doc3 = Document(page_content="Content 3", metadata={"anime_id": "2"})

        mock_prefilter.return_value = [mock_doc1]
        mock_retriever = Mock()
        mock_retriever.invoke.return_value = [mock_doc2, mock_doc3]
        mock_build_retriever.return_value = mock_retriever

        mock_prompt = Mock()
        mock_prompt.format_messages.return_value = [Mock(), Mock()]
        mock_prompt_builder.return_value = mock_prompt

        mock_llm = Mock()
        mock_response = Mock()
        mock_response.content = "Answer"
        mock_llm.invoke.return_value = mock_response
        mock_chat_class.return_value = mock_llm

        # Act
        chain = build_rag_chain(mock_context)
        answer, docs = chain("Test question")

        # Assert
        # Should only have 2 docs (anime_id "1" deduplicated)
        assert len(docs) == 2
        assert docs[0].metadata["anime_id"] == "1"
        assert docs[1].metadata["anime_id"] == "2"

    @patch("services.rag_service.build_retriever")
    @patch("services.rag_service.build_anime_rag_prompt")
    @patch("services.rag_service.ChatOpenAI")
    @patch("services.rag_service.alias_prefilter")
    def test_rag_chain_handles_no_prefilter_results(
        self,
        mock_prefilter: Mock,
        mock_chat_class: Mock,
        mock_prompt_builder: Mock,
        mock_build_retriever: Mock,
        mock_context: Mock,
    ) -> None:
        """Test RAG chain when prefilter returns no results."""
        # Arrange
        from langchain_core.documents import Document

        mock_context.config.get.side_effect = lambda key, default=None: {
            "openai.model": "gpt-5-nano",
            "openai.reasoning_effort": "medium",
            "openai.output_verbosity": "medium",
            "openai.max_output_tokens": 4096,
        }.get(key, default)

        mock_doc = Document(page_content="Content", metadata={"anime_id": "1"})
        mock_prefilter.return_value = []  # No prefilter results
        mock_retriever = Mock()
        mock_retriever.invoke.return_value = [mock_doc]
        mock_build_retriever.return_value = mock_retriever

        mock_prompt = Mock()
        mock_prompt.format_messages.return_value = [Mock(), Mock()]
        mock_prompt_builder.return_value = mock_prompt

        mock_llm = Mock()
        mock_response = Mock()
        mock_response.content = "Answer"
        mock_llm.invoke.return_value = mock_response
        mock_chat_class.return_value = mock_llm

        # Act
        chain = build_rag_chain(mock_context)
        answer, docs = chain("Test question")

        # Assert
        assert len(docs) == 1
        assert answer == "Answer"



class TestSearchWithMCPFallback:
    """Tests for search_with_mcp_fallback function."""

    @pytest.mark.asyncio
    async def test_search_with_mcp_fallback_empty_query(
        self, mock_context: Mock
    ) -> None:
        """Test that empty query raises ValueError."""
        from services.rag_service import search_with_mcp_fallback

        # Act & Assert
        with pytest.raises(ValueError, match="Query cannot be empty"):
            await search_with_mcp_fallback("", mock_context)

        with pytest.raises(ValueError, match="Query cannot be empty"):
            await search_with_mcp_fallback("   ", mock_context)

    @pytest.mark.asyncio
    async def test_search_with_mcp_fallback_invalid_thresholds(
        self, mock_context: Mock
    ) -> None:
        """Test that invalid thresholds raise ValueError."""
        from services.rag_service import search_with_mcp_fallback

        # Act & Assert
        with pytest.raises(ValueError, match="min_results must be positive"):
            await search_with_mcp_fallback("test", mock_context, min_results=0)

        with pytest.raises(ValueError, match="min_score must be between 0 and 1"):
            await search_with_mcp_fallback("test", mock_context, min_score=1.5)

        with pytest.raises(ValueError, match="min_score must be between 0 and 1"):
            await search_with_mcp_fallback("test", mock_context, min_score=-0.1)

    @pytest.mark.asyncio
    async def test_search_with_mcp_fallback_both_thresholds_met(
        self, mock_context: Mock
    ) -> None:
        """Test that MCP fallback is not triggered when both thresholds are met."""
        from langchain_core.documents import Document

        from services.rag_service import search_with_mcp_fallback

        # Arrange
        mock_context.config.get_mcp_fallback_count_threshold.return_value = 3
        mock_context.config.get_mcp_fallback_score_threshold.return_value = 0.7

        mock_doc1 = Document(page_content="Content 1", metadata={"anime_id": "1"})
        mock_doc2 = Document(page_content="Content 2", metadata={"anime_id": "2"})
        mock_doc3 = Document(page_content="Content 3", metadata={"anime_id": "3"})

        mock_vectorstore = Mock()
        # Distance scores: lower = better. Best score (0.3) is <= threshold (0.7)
        mock_vectorstore.similarity_search_with_score.return_value = [
            (mock_doc1, 0.3),  # Good match
            (mock_doc2, 0.4),  # Good match
            (mock_doc3, 0.5),  # Good match
        ]
        mock_context.vectorstore = mock_vectorstore

        # Act
        result = await search_with_mcp_fallback("test query", mock_context)

        # Assert
        assert len(result) == 3
        assert result[0] == mock_doc1
        assert result[1] == mock_doc2
        assert result[2] == mock_doc3
        # MCP should not be called
        mock_context.config.get_mcp_enabled.assert_not_called()

    @pytest.mark.asyncio
    async def test_search_with_mcp_fallback_count_threshold_not_met(
        self, mock_context: Mock
    ) -> None:
        """Test that MCP fallback is triggered when count threshold is not met."""
        from langchain_core.documents import Document

        from services.rag_service import search_with_mcp_fallback

        # Arrange
        mock_context.config.get_mcp_fallback_count_threshold.return_value = 3
        mock_context.config.get_mcp_fallback_score_threshold.return_value = 0.7
        mock_context.config.get_mcp_enabled.return_value = False  # Disabled

        mock_doc1 = Document(page_content="Content 1", metadata={"anime_id": "1"})

        mock_vectorstore = Mock()
        # Distance score: 0.3 is good, but only 1 result (< threshold of 3)
        mock_vectorstore.similarity_search_with_score.return_value = [
            (mock_doc1, 0.3),  # Good distance but only 1 result
        ]
        mock_context.vectorstore = mock_vectorstore

        # Act
        result = await search_with_mcp_fallback("test query", mock_context)

        # Assert
        assert len(result) == 1
        assert result[0] == mock_doc1
        # MCP enabled check should be called
        mock_context.config.get_mcp_enabled.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_with_mcp_fallback_score_threshold_not_met(
        self, mock_context: Mock
    ) -> None:
        """Test that MCP fallback is triggered when score threshold is not met."""
        from langchain_core.documents import Document

        from services.rag_service import search_with_mcp_fallback

        # Arrange
        mock_context.config.get_mcp_fallback_count_threshold.return_value = 3
        mock_context.config.get_mcp_fallback_score_threshold.return_value = 0.7
        mock_context.config.get_mcp_enabled.return_value = False  # Disabled

        mock_doc1 = Document(page_content="Content 1", metadata={"anime_id": "1"})
        mock_doc2 = Document(page_content="Content 2", metadata={"anime_id": "2"})
        mock_doc3 = Document(page_content="Content 3", metadata={"anime_id": "3"})

        mock_vectorstore = Mock()
        # Distance scores: best (0.8) is > threshold (0.7), so MCP should trigger
        mock_vectorstore.similarity_search_with_score.return_value = [
            (mock_doc1, 0.8),  # Poor match (> 0.7 threshold)
            (mock_doc2, 0.9),  # Poor match
            (mock_doc3, 1.0),  # Poor match
        ]
        mock_context.vectorstore = mock_vectorstore

        # Act
        result = await search_with_mcp_fallback("test query", mock_context)

        # Assert
        assert len(result) == 3
        # MCP enabled check should be called
        mock_context.config.get_mcp_enabled.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_with_mcp_fallback_mcp_disabled(
        self, mock_context: Mock
    ) -> None:
        """Test that MCP fallback returns vector store results when MCP is disabled."""
        from langchain_core.documents import Document

        from services.rag_service import search_with_mcp_fallback

        # Arrange
        mock_context.config.get_mcp_fallback_count_threshold.return_value = 3
        mock_context.config.get_mcp_fallback_score_threshold.return_value = 0.7
        mock_context.config.get_mcp_enabled.return_value = False

        mock_doc1 = Document(page_content="Content 1", metadata={"anime_id": "1"})

        mock_vectorstore = Mock()
        # Both thresholds not met: count=1 (< 3) AND distance=0.8 (> 0.7)
        mock_vectorstore.similarity_search_with_score.return_value = [
            (mock_doc1, 0.8),  # Poor score AND insufficient count
        ]
        mock_context.vectorstore = mock_vectorstore

        # Act
        result = await search_with_mcp_fallback("test query", mock_context)

        # Assert
        assert len(result) == 1
        assert result[0] == mock_doc1

    @pytest.mark.asyncio
    @patch("services.mcp_client_service.create_mcp_client")
    @patch("services.showdoc_persistence.ShowDocPersistence")
    @patch("services.anidb_parser.parse_anidb_xml")
    @patch("services.vectorstore_service.upsert_documents")
    async def test_search_with_mcp_fallback_fetches_from_mcp(
        self,
        mock_upsert: Mock,
        mock_parse: Mock,
        mock_persistence_class: Mock,
        mock_create_client: Mock,
        mock_context: Mock,
    ) -> None:
        """Test that MCP fallback fetches and persists anime data."""
        from unittest.mock import AsyncMock

        from langchain_core.documents import Document

        from models.show_doc import ShowDoc
        from services.rag_service import search_with_mcp_fallback

        # Arrange
        mock_context.config.get_mcp_fallback_count_threshold.return_value = 3
        mock_context.config.get_mcp_fallback_score_threshold.return_value = 0.7
        mock_context.config.get_mcp_enabled.return_value = True
        mock_context.config.get_mcp_cache_dir.return_value = "data/mcp_cache"

        # Vector store returns insufficient results
        mock_doc1 = Document(page_content="Content 1", metadata={"anime_id": "1"})
        mock_vectorstore = Mock()
        mock_vectorstore.similarity_search_with_score.return_value = [
            (mock_doc1, 0.5),
        ]
        mock_context.vectorstore = mock_vectorstore

        # Mock MCP client
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.search_anime.return_value = [{"aid": 12345, "title": "Test Anime"}]
        mock_client.get_anime_details.return_value = "<anime>...</anime>"
        mock_create_client.return_value = mock_client

        # Mock persistence
        mock_persistence = Mock()
        mock_persistence.exists.return_value = False
        mock_persistence_class.return_value = mock_persistence

        # Mock ShowDoc
        mock_show_doc = ShowDoc(
            anime_id="12345",
            anidb_anime_id=12345,
            title_main="Test Anime",
            description="Test description",
        )
        mock_parse.return_value = mock_show_doc

        # Act
        result = await search_with_mcp_fallback("test query", mock_context)

        # Assert
        assert len(result) == 2  # 1 from vector store + 1 from MCP
        mock_client.search_anime.assert_called_once_with("test query")
        mock_client.get_anime_details.assert_called_once_with(12345)
        mock_parse.assert_called_once_with("<anime>...</anime>")
        mock_persistence.save_showdoc.assert_called_once_with(mock_show_doc)
        mock_upsert.assert_called_once()

    @pytest.mark.asyncio
    @patch("services.mcp_client_service.create_mcp_client")
    @patch("services.showdoc_persistence.ShowDocPersistence")
    async def test_search_with_mcp_fallback_uses_persistence_cache(
        self,
        mock_persistence_class: Mock,
        mock_create_client: Mock,
        mock_context: Mock,
    ) -> None:
        """Test that MCP fallback uses persistence cache when available."""
        from langchain_core.documents import Document

        from models.show_doc import ShowDoc
        from services.rag_service import search_with_mcp_fallback

        # Arrange
        mock_context.config.get_mcp_fallback_count_threshold.return_value = 3
        mock_context.config.get_mcp_fallback_score_threshold.return_value = 0.7
        mock_context.config.get_mcp_enabled.return_value = True
        mock_context.config.get_mcp_cache_dir.return_value = "data/mcp_cache"

        # Vector store returns insufficient results
        mock_doc1 = Document(page_content="Content 1", metadata={"anime_id": "1"})
        mock_vectorstore = Mock()
        mock_vectorstore.similarity_search_with_score.return_value = [
            (mock_doc1, 0.5),
        ]
        mock_context.vectorstore = mock_vectorstore

        # Mock MCP client
        from unittest.mock import AsyncMock
        
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.search_anime.return_value = [{"aid": 12345, "title": "Test Anime"}]
        mock_create_client.return_value = mock_client

        # Mock persistence with cached data
        mock_show_doc = ShowDoc(
            anime_id="12345",
            anidb_anime_id=12345,
            title_main="Cached Anime",
            description="Cached description",
        )
        mock_persistence = Mock()
        mock_persistence.exists.return_value = True
        mock_persistence.load_showdoc.return_value = mock_show_doc
        mock_persistence_class.return_value = mock_persistence

        # Act
        result = await search_with_mcp_fallback("test query", mock_context)

        # Assert
        assert len(result) == 2  # 1 from vector store + 1 from cache
        mock_client.search_anime.assert_called_once_with("test query")
        # Should NOT call get_anime_details since it's cached
        mock_client.get_anime_details.assert_not_called()
        mock_persistence.load_showdoc.assert_called_once_with(12345)

    @pytest.mark.asyncio
    @patch("services.mcp_client_service.create_mcp_client")
    @patch("services.showdoc_persistence.ShowDocPersistence")
    async def test_search_with_mcp_fallback_handles_mcp_failure(
        self,
        mock_persistence_class: Mock,
        mock_create_client: Mock,
        mock_context: Mock,
    ) -> None:
        """Test that MCP fallback handles failures gracefully."""
        from langchain_core.documents import Document

        from services.rag_service import search_with_mcp_fallback

        # Arrange
        mock_context.config.get_mcp_fallback_count_threshold.return_value = 3
        mock_context.config.get_mcp_fallback_score_threshold.return_value = 0.7
        mock_context.config.get_mcp_enabled.return_value = True
        mock_context.config.get_mcp_cache_dir.return_value = "data/mcp_cache"

        # Vector store returns insufficient results
        mock_doc1 = Document(page_content="Content 1", metadata={"anime_id": "1"})
        mock_vectorstore = Mock()
        mock_vectorstore.similarity_search_with_score.return_value = [
            (mock_doc1, 0.5),
        ]
        mock_context.vectorstore = mock_vectorstore

        # Mock MCP client to raise exception
        mock_create_client.side_effect = Exception("MCP connection failed")

        # Act
        result = await search_with_mcp_fallback("test query", mock_context)

        # Assert - should return vector store results despite MCP failure
        assert len(result) == 1
        assert result[0] == mock_doc1

    @pytest.mark.asyncio
    @patch("services.mcp_client_service.create_mcp_client")
    @patch("services.showdoc_persistence.ShowDocPersistence")
    @patch("services.vectorstore_service.upsert_documents")
    async def test_search_with_mcp_fallback_deduplicates_results(
        self,
        mock_upsert: Mock,
        mock_persistence_class: Mock,
        mock_create_client: Mock,
        mock_context: Mock,
    ) -> None:
        """Test that MCP fallback deduplicates results by anime_id."""
        from langchain_core.documents import Document

        from models.show_doc import ShowDoc
        from services.rag_service import search_with_mcp_fallback

        # Arrange
        mock_context.config.get_mcp_fallback_count_threshold.return_value = 3
        mock_context.config.get_mcp_fallback_score_threshold.return_value = 0.7
        mock_context.config.get_mcp_enabled.return_value = True
        mock_context.config.get_mcp_cache_dir.return_value = "data/mcp_cache"

        # Vector store returns result with same anime_id as MCP will return
        mock_doc1 = Document(page_content="Content 1", metadata={"anime_id": "12345"})
        mock_vectorstore = Mock()
        mock_vectorstore.similarity_search_with_score.return_value = [
            (mock_doc1, 0.5),
        ]
        mock_context.vectorstore = mock_vectorstore

        # Mock MCP client
        mock_client = Mock()
        mock_client.__aenter__ = Mock(return_value=mock_client)
        mock_client.__aexit__ = Mock(return_value=None)
        mock_client.search_anime = Mock(
            return_value=[{"aid": 12345, "title": "Test Anime"}]
        )
        mock_create_client.return_value = mock_client

        # Mock persistence with cached data (same anime_id)
        mock_show_doc = ShowDoc(
            anime_id="12345",
            anidb_anime_id=12345,
            title_main="Test Anime",
            description="Test description",
        )
        mock_persistence = Mock()
        mock_persistence.exists.return_value = True
        mock_persistence.load_showdoc.return_value = mock_show_doc
        mock_persistence_class.return_value = mock_persistence

        # Act
        result = await search_with_mcp_fallback("test query", mock_context)

        # Assert - should only have 1 result (deduplicated)
        assert len(result) == 1
        assert result[0].metadata["anime_id"] == "12345"

    @pytest.mark.asyncio
    @patch("services.mcp_client_service.create_mcp_client")
    @patch("services.showdoc_persistence.ShowDocPersistence")
    async def test_search_with_mcp_fallback_no_mcp_results(
        self,
        mock_persistence_class: Mock,
        mock_create_client: Mock,
        mock_context: Mock,
    ) -> None:
        """Test that MCP fallback handles no search results gracefully."""
        from langchain_core.documents import Document

        from services.rag_service import search_with_mcp_fallback

        # Arrange
        mock_context.config.get_mcp_fallback_count_threshold.return_value = 3
        mock_context.config.get_mcp_fallback_score_threshold.return_value = 0.7
        mock_context.config.get_mcp_enabled.return_value = True
        mock_context.config.get_mcp_cache_dir.return_value = "data/mcp_cache"

        # Vector store returns insufficient results
        mock_doc1 = Document(page_content="Content 1", metadata={"anime_id": "1"})
        mock_vectorstore = Mock()
        mock_vectorstore.similarity_search_with_score.return_value = [
            (mock_doc1, 0.5),
        ]
        mock_context.vectorstore = mock_vectorstore

        # Mock MCP client with no results
        from unittest.mock import AsyncMock
        
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.search_anime.return_value = []
        mock_create_client.return_value = mock_client

        mock_persistence = Mock()
        mock_persistence_class.return_value = mock_persistence

        # Act
        result = await search_with_mcp_fallback("test query", mock_context)

        # Assert - should return vector store results only
        assert len(result) == 1
        assert result[0] == mock_doc1

    @pytest.mark.asyncio
    @patch("services.mcp_client_service.create_mcp_client")
    @patch("services.showdoc_persistence.ShowDocPersistence")
    @patch("services.anidb_parser.parse_anidb_xml")
    async def test_search_with_mcp_fallback_handles_xml_parsing_failure(
        self,
        mock_parse: Mock,
        mock_persistence_class: Mock,
        mock_create_client: Mock,
        mock_context: Mock,
    ) -> None:
        """Test that MCP fallback handles XML parsing failures gracefully."""
        from langchain_core.documents import Document

        from services.rag_service import search_with_mcp_fallback

        # Arrange
        mock_context.config.get_mcp_fallback_count_threshold.return_value = 3
        mock_context.config.get_mcp_fallback_score_threshold.return_value = 0.7
        mock_context.config.get_mcp_enabled.return_value = True
        mock_context.config.get_mcp_cache_dir.return_value = "data/mcp_cache"

        # Vector store returns insufficient results
        mock_doc1 = Document(page_content="Content 1", metadata={"anime_id": "1"})
        mock_vectorstore = Mock()
        mock_vectorstore.similarity_search_with_score.return_value = [
            (mock_doc1, 0.5),
        ]
        mock_context.vectorstore = mock_vectorstore

        # Mock MCP client
        from unittest.mock import AsyncMock
        
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.search_anime.return_value = [{"aid": 12345, "title": "Test Anime"}]
        mock_client.get_anime_details.return_value = "<invalid>xml</invalid>"
        mock_create_client.return_value = mock_client

        # Mock persistence
        mock_persistence = Mock()
        mock_persistence.exists.return_value = False
        mock_persistence_class.return_value = mock_persistence

        # Mock XML parser to raise exception
        mock_parse.side_effect = ValueError("Invalid XML format")

        # Act
        result = await search_with_mcp_fallback("test query", mock_context)

        # Assert - should return vector store results despite XML parsing failure
        assert len(result) == 1
        assert result[0] == mock_doc1
        mock_parse.assert_called_once_with("<invalid>xml</invalid>")

    @pytest.mark.asyncio
    @patch("services.mcp_client_service.create_mcp_client")
    @patch("services.showdoc_persistence.ShowDocPersistence")
    @patch("services.anidb_parser.parse_anidb_xml")
    @patch("services.vectorstore_service.upsert_documents")
    async def test_search_with_mcp_fallback_handles_persistence_failure(
        self,
        mock_upsert: Mock,
        mock_parse: Mock,
        mock_persistence_class: Mock,
        mock_create_client: Mock,
        mock_context: Mock,
    ) -> None:
        """Test that MCP fallback handles persistence failures gracefully.
        
        NOTE: Current implementation catches all exceptions at the outer level,
        so persistence failures cause the entire MCP fallback to fail and return
        only vector store results.
        """
        from langchain_core.documents import Document

        from models.show_doc import ShowDoc
        from services.rag_service import search_with_mcp_fallback

        # Arrange
        mock_context.config.get_mcp_fallback_count_threshold.return_value = 3
        mock_context.config.get_mcp_fallback_score_threshold.return_value = 0.7
        mock_context.config.get_mcp_enabled.return_value = True
        mock_context.config.get_mcp_cache_dir.return_value = "data/mcp_cache"

        # Vector store returns insufficient results
        mock_doc1 = Document(page_content="Content 1", metadata={"anime_id": "1"})
        mock_vectorstore = Mock()
        mock_vectorstore.similarity_search_with_score.return_value = [
            (mock_doc1, 0.5),
        ]
        mock_context.vectorstore = mock_vectorstore

        # Mock MCP client
        from unittest.mock import AsyncMock
        
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.search_anime.return_value = [{"aid": 12345, "title": "Test Anime"}]
        mock_client.get_anime_details.return_value = "<anime>...</anime>"
        mock_create_client.return_value = mock_client

        # Mock persistence to fail on save
        mock_persistence = Mock()
        mock_persistence.exists.return_value = False
        mock_persistence.save_showdoc.side_effect = IOError("Disk write failed")
        mock_persistence_class.return_value = mock_persistence

        # Mock ShowDoc
        mock_show_doc = ShowDoc(
            anime_id="12345",
            anidb_anime_id=12345,
            title_main="Test Anime",
            description="Test description",
        )
        mock_parse.return_value = mock_show_doc

        # Act
        result = await search_with_mcp_fallback("test query", mock_context)

        # Assert - current implementation returns vector store results only when persistence fails
        # NOTE: This doesn't fully meet Requirement 7.3 which states persistence failures
        # should be logged but the anime should still be added to the vector store.
        # The current implementation catches all exceptions at the outer level.
        assert len(result) == 1  # Only vector store result (MCP fallback failed)
        assert result[0] == mock_doc1
        mock_persistence.save_showdoc.assert_called_once_with(mock_show_doc)
        # Vector store upsert should NOT be called because persistence failed first
        mock_upsert.assert_not_called()


    @pytest.mark.asyncio
    @patch("services.mcp_client_service.create_mcp_client")
    @patch("services.showdoc_persistence.ShowDocPersistence")
    async def test_search_with_mcp_fallback_search_result_with_attribute(
        self,
        mock_persistence_class: Mock,
        mock_create_client: Mock,
        mock_context: Mock,
    ) -> None:
        """Test MCP fallback with search result that has aid as attribute."""
        from unittest.mock import AsyncMock

        from langchain_core.documents import Document

        from models.show_doc import ShowDoc
        from services.rag_service import search_with_mcp_fallback

        # Arrange
        mock_context.config.get_mcp_fallback_count_threshold.return_value = 3
        mock_context.config.get_mcp_fallback_score_threshold.return_value = 0.7
        mock_context.config.get_mcp_enabled.return_value = True
        mock_context.config.get_mcp_cache_dir.return_value = "data/mcp_cache"

        mock_doc1 = Document(page_content="Content 1", metadata={"anime_id": "1"})
        mock_vectorstore = Mock()
        mock_vectorstore.similarity_search_with_score.return_value = [
            (mock_doc1, 0.5),
        ]
        mock_context.vectorstore = mock_vectorstore

        # Mock MCP client with search result that has aid as attribute
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        
        # Create a mock object with aid attribute
        mock_search_result = Mock()
        mock_search_result.aid = 12345
        mock_client.search_anime.return_value = [mock_search_result]
        mock_create_client.return_value = mock_client

        # Mock persistence with cached data
        mock_show_doc = ShowDoc(
            anime_id="12345",
            anidb_anime_id=12345,
            title_main="Test Anime",
            description="Test description",
        )
        mock_persistence = Mock()
        mock_persistence.exists.return_value = True
        mock_persistence.load_showdoc.return_value = mock_show_doc
        mock_persistence_class.return_value = mock_persistence

        # Act
        result = await search_with_mcp_fallback("test query", mock_context)

        # Assert
        assert len(result) == 2
        mock_persistence.load_showdoc.assert_called_once_with(12345)

    @pytest.mark.asyncio
    @patch("services.mcp_client_service.create_mcp_client")
    @patch("services.showdoc_persistence.ShowDocPersistence")
    async def test_search_with_mcp_fallback_search_result_no_aid(
        self,
        mock_persistence_class: Mock,
        mock_create_client: Mock,
        mock_context: Mock,
    ) -> None:
        """Test MCP fallback with search result that has no aid."""
        from unittest.mock import AsyncMock

        from langchain_core.documents import Document

        from services.rag_service import search_with_mcp_fallback

        # Arrange
        mock_context.config.get_mcp_fallback_count_threshold.return_value = 3
        mock_context.config.get_mcp_fallback_score_threshold.return_value = 0.7
        mock_context.config.get_mcp_enabled.return_value = True
        mock_context.config.get_mcp_cache_dir.return_value = "data/mcp_cache"

        mock_doc1 = Document(page_content="Content 1", metadata={"anime_id": "1"})
        mock_vectorstore = Mock()
        mock_vectorstore.similarity_search_with_score.return_value = [
            (mock_doc1, 0.5),
        ]
        mock_context.vectorstore = mock_vectorstore

        # Mock MCP client with search result that has no aid
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.search_anime.return_value = [{"title": "No ID"}]  # Missing aid
        mock_create_client.return_value = mock_client

        mock_persistence = Mock()
        mock_persistence_class.return_value = mock_persistence

        # Act
        result = await search_with_mcp_fallback("test query", mock_context)

        # Assert - should return only vector store results
        assert len(result) == 1
        assert result[0] == mock_doc1

    @pytest.mark.asyncio
    @patch("services.mcp_client_service.create_mcp_client")
    @patch("services.showdoc_persistence.ShowDocPersistence")
    async def test_search_with_mcp_fallback_search_result_invalid_type(
        self,
        mock_persistence_class: Mock,
        mock_create_client: Mock,
        mock_context: Mock,
    ) -> None:
        """Test MCP fallback with search result of invalid type."""
        from unittest.mock import AsyncMock

        from langchain_core.documents import Document

        from services.rag_service import search_with_mcp_fallback

        # Arrange
        mock_context.config.get_mcp_fallback_count_threshold.return_value = 3
        mock_context.config.get_mcp_fallback_score_threshold.return_value = 0.7
        mock_context.config.get_mcp_enabled.return_value = True
        mock_context.config.get_mcp_cache_dir.return_value = "data/mcp_cache"

        mock_doc1 = Document(page_content="Content 1", metadata={"anime_id": "1"})
        mock_vectorstore = Mock()
        mock_vectorstore.similarity_search_with_score.return_value = [
            (mock_doc1, 0.5),
        ]
        mock_context.vectorstore = mock_vectorstore

        # Mock MCP client with invalid search result type
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.search_anime.return_value = ["invalid_string_result"]
        mock_create_client.return_value = mock_client

        mock_persistence = Mock()
        mock_persistence_class.return_value = mock_persistence

        # Act
        result = await search_with_mcp_fallback("test query", mock_context)

        # Assert - should return only vector store results
        assert len(result) == 1
        assert result[0] == mock_doc1

    @pytest.mark.asyncio
    @patch("services.mcp_client_service.create_mcp_client")
    @patch("services.showdoc_persistence.ShowDocPersistence")
    async def test_search_with_mcp_fallback_empty_xml_response(
        self,
        mock_persistence_class: Mock,
        mock_create_client: Mock,
        mock_context: Mock,
    ) -> None:
        """Test MCP fallback when get_anime_details returns empty XML."""
        from unittest.mock import AsyncMock

        from langchain_core.documents import Document

        from services.rag_service import search_with_mcp_fallback

        # Arrange
        mock_context.config.get_mcp_fallback_count_threshold.return_value = 3
        mock_context.config.get_mcp_fallback_score_threshold.return_value = 0.7
        mock_context.config.get_mcp_enabled.return_value = True
        mock_context.config.get_mcp_cache_dir.return_value = "data/mcp_cache"

        mock_doc1 = Document(page_content="Content 1", metadata={"anime_id": "1"})
        mock_vectorstore = Mock()
        mock_vectorstore.similarity_search_with_score.return_value = [
            (mock_doc1, 0.5),
        ]
        mock_context.vectorstore = mock_vectorstore

        # Mock MCP client that returns empty XML
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.search_anime.return_value = [{"aid": 12345}]
        mock_client.get_anime_details.return_value = ""  # Empty XML
        mock_create_client.return_value = mock_client

        mock_persistence = Mock()
        mock_persistence.exists.return_value = False
        mock_persistence_class.return_value = mock_persistence

        # Act
        result = await search_with_mcp_fallback("test query", mock_context)

        # Assert - should return only vector store results
        assert len(result) == 1
        assert result[0] == mock_doc1

    @pytest.mark.asyncio
    @patch("services.mcp_client_service.create_mcp_client")
    @patch("services.showdoc_persistence.ShowDocPersistence")
    async def test_search_with_mcp_fallback_persistence_load_returns_none(
        self,
        mock_persistence_class: Mock,
        mock_create_client: Mock,
        mock_context: Mock,
    ) -> None:
        """Test MCP fallback when persistence.load_showdoc returns None."""
        from unittest.mock import AsyncMock

        from langchain_core.documents import Document

        from services.rag_service import search_with_mcp_fallback

        # Arrange
        mock_context.config.get_mcp_fallback_count_threshold.return_value = 3
        mock_context.config.get_mcp_fallback_score_threshold.return_value = 0.7
        mock_context.config.get_mcp_enabled.return_value = True
        mock_context.config.get_mcp_cache_dir.return_value = "data/mcp_cache"

        mock_doc1 = Document(page_content="Content 1", metadata={"anime_id": "1"})
        mock_vectorstore = Mock()
        mock_vectorstore.similarity_search_with_score.return_value = [
            (mock_doc1, 0.5),
        ]
        mock_context.vectorstore = mock_vectorstore

        # Mock MCP client
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.search_anime.return_value = [{"aid": 12345}]
        mock_create_client.return_value = mock_client

        # Mock persistence that exists but returns None on load
        mock_persistence = Mock()
        mock_persistence.exists.return_value = True
        mock_persistence.load_showdoc.return_value = None  # Returns None
        mock_persistence_class.return_value = mock_persistence

        # Act
        result = await search_with_mcp_fallback("test query", mock_context)

        # Assert - should return only vector store results
        assert len(result) == 1
        assert result[0] == mock_doc1



class TestBuildRagChainJsonFormat:
    """Tests for build_rag_chain with JSON output format."""

    @patch("services.rag_service.build_retriever")
    @patch("services.rag_service.build_anime_rag_json_prompt")
    @patch("services.rag_service.ChatOpenAI")
    def test_build_rag_chain_json_format(
        self,
        mock_chat_class: Mock,
        mock_prompt_builder: Mock,
        mock_build_retriever: Mock,
        mock_context: Mock,
    ) -> None:
        """Test RAG chain construction with JSON output format."""
        # Arrange
        mock_context.config.get.side_effect = lambda key, default=None: {
            "openai.model": "gpt-5-nano",
        }.get(key, default)
        mock_context.config.get_reasoning_effort.return_value = "medium"
        mock_context.config.get_output_verbosity.return_value = "medium"
        mock_context.config.get_max_output_tokens.return_value = 4096

        mock_llm = Mock()
        mock_chat_class.return_value = mock_llm
        mock_prompt = Mock()
        mock_prompt_builder.return_value = mock_prompt
        mock_retriever = Mock()
        mock_build_retriever.return_value = mock_retriever

        # Act
        chain = build_rag_chain(mock_context, output_format="json")

        # Assert
        assert callable(chain)
        mock_chat_class.assert_called_once_with(
            model="gpt-5-nano",
            max_completion_tokens=4096,
            timeout=120,
            max_retries=3,
            model_kwargs={"response_format": {"type": "json_object"}},
        )
        mock_prompt_builder.assert_called_once()

    @patch("services.rag_service.build_retriever")
    @patch("services.rag_service.build_anime_rag_json_prompt")
    @patch("services.rag_service.ChatOpenAI")
    def test_build_rag_chain_invalid_output_format(
        self,
        mock_chat_class: Mock,
        mock_prompt_builder: Mock,
        mock_build_retriever: Mock,
        mock_context: Mock,
    ) -> None:
        """Test that invalid output format raises ValueError."""
        # Arrange
        mock_context.config.get.side_effect = lambda key, default=None: {
            "openai.model": "gpt-5-nano",
        }.get(key, default)

        # Act & Assert
        with pytest.raises(ValueError, match="output_format must be 'text' or 'json'"):
            build_rag_chain(mock_context, output_format="invalid")
