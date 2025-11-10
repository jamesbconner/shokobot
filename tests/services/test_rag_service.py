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
        mock_chat_class.assert_called_once_with(
            model="gpt-5-nano", max_completion_tokens=4096
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
