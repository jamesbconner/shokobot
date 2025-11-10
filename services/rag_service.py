import logging
from collections.abc import Callable, Sequence
from typing import TYPE_CHECKING, Any

from langchain_core.documents import Document
from langchain_openai import ChatOpenAI

from prompts import build_anime_rag_prompt

if TYPE_CHECKING:
    from services.app_context import AppContext

logger = logging.getLogger(__name__)


def build_retriever(ctx: "AppContext", k: int = 10, score_threshold: float | None = None) -> Any:
    """Build a vector store retriever with specified parameters.

    Args:
        ctx: Application context with vectorstore access.
        k: Number of documents to retrieve.
        score_threshold: Optional minimum similarity score threshold.

    Returns:
        Configured retriever instance.

    Raises:
        ValueError: If k is invalid.
    """
    if k <= 0:
        raise ValueError(f"k must be positive, got {k}")

    vs = ctx.vectorstore
    kwargs: dict[str, Any] = {"k": k}
    if score_threshold is not None:
        if not 0.0 <= score_threshold <= 1.0:
            raise ValueError(f"score_threshold must be between 0 and 1, got {score_threshold}")
        kwargs["score_threshold"] = score_threshold

    logger.debug(f"Building retriever with k={k}, score_threshold={score_threshold}")
    return vs.as_retriever(search_kwargs=kwargs)


def alias_prefilter(query: str, ctx: "AppContext", limit: int = 12) -> Sequence[Document]:
    """Pre-filter documents based on query patterns for exact matches.

    Supports special query patterns:
    - Quoted phrases: "exact title" searches for exact title_main match
    - Alias prefix: "alias:name" searches for exact alias match
    - Default: searches document content

    Args:
        query: User query string with optional special patterns.
        ctx: Application context with vectorstore access.
        limit: Maximum number of documents to return.

    Returns:
        Sequence of matching documents.

    Raises:
        Exception: If vector store search fails.
    """
    if limit <= 0:
        raise ValueError(f"limit must be positive, got {limit}")

    try:
        vs = ctx.vectorstore

        # Exact title match using quotes
        if '"' in query:
            parts = query.split('"')
            if len(parts) >= 2:
                phrase = parts[1].strip()
                logger.debug(f"Exact title search for: {phrase}")
                return vs.similarity_search(query, k=limit, where={"title_main": {"$eq": phrase}})

        # Alias-based search
        if "alias:" in query:
            alias_parts = query.split("alias:")[-1].split()
            if alias_parts:
                alias = alias_parts[0].strip()
                logger.debug(f"Alias search for: {alias}")
                return vs.similarity_search(
                    query, k=limit, where={"title_alts": {"$contains": alias}}
                )

        # Default content search
        logger.debug(f"Content search for: {query}")
        return vs.similarity_search(query, k=limit, where_document={"$contains": query})

    except Exception as e:
        logger.error(f"Prefilter search failed for query '{query}': {e}")
        return []


def build_rag_chain(ctx: "AppContext") -> Callable[[str], tuple[str, list[Document]]]:
    """Build RAG chain for answering anime-related questions.

    Uses LangChain's ChatOpenAI with native Responses API support for GPT-5 models.

    Args:
        ctx: Application context with configuration and vectorstore access.

    Returns:
        Callable that takes a question string and returns (answer_text, context_docs).

    Raises:
        ValueError: If required configuration is missing.
    """
    model_name = ctx.config.get("openai.model")
    if not model_name:
        raise ValueError("openai.model not configured")

    # Validate that a GPT-5 model is configured
    # GPT-5 models use the Responses API exclusively
    if not model_name.startswith("gpt-5"):
        raise ValueError(
            f"This service requires a GPT-5 model (e.g., gpt-5-nano, gpt-5-mini, gpt-5). "
            f"Configured model '{model_name}' is not supported. "
            f"GPT-5 models use the Responses API with reasoning capabilities."
        )

    # Get configuration for GPT-5 Responses API
    reasoning_effort = ctx.config.get("openai.reasoning_effort", "medium")
    output_verbosity = ctx.config.get("openai.output_verbosity", "medium")
    max_output_tokens = ctx.config.get("openai.max_output_tokens", 4096)

    logger.info(
        f"Building RAG chain with model={model_name}, "
        f"reasoning_effort={reasoning_effort}, "
        f"text_verbosity={output_verbosity}"
    )

    # Initialize ChatOpenAI with Responses API parameters
    # GPT-5 models automatically use the Responses API
    # Note: reasoning and text parameters are passed at invocation time, not initialization
    llm = ChatOpenAI(
        model=model_name,
        max_completion_tokens=max_output_tokens,
    )

    # Load prompt template from prompts module
    prompt = build_anime_rag_prompt()

    retriever = build_retriever(ctx)

    def chain_fn(question: str) -> tuple[str, list[Document]]:
        """Execute RAG chain for a given question.

        Args:
            question: User question about anime.

        Returns:
            Tuple of (answer_text, list of context documents used).

        Raises:
            Exception: If retrieval or LLM invocation fails.
        """
        if not question or not question.strip():
            raise ValueError("Question cannot be empty")

        logger.info(f"Processing question: {question[:100]}...")

        try:
            # Get pre-filtered documents for exact matches
            pre_docs = alias_prefilter(question, ctx) or []
            logger.debug(f"Prefilter returned {len(pre_docs)} documents")

            # Get semantic search results
            docs = retriever.invoke(question)
            logger.debug(f"Retriever returned {len(docs)} documents")

            # Merge and deduplicate by anime_id
            seen, merged = set(), []
            for d in list(pre_docs) + list(docs):
                key = d.metadata.get("anime_id")
                if key and key not in seen:
                    seen.add(key)
                    merged.append(d)

            logger.debug(f"Using {len(merged)} unique documents for context")

            # Build context and invoke LLM
            context = "\n\n".join(d.page_content for d in merged)
            messages = prompt.format_messages(question=question, context=context)

            # Invoke LLM with GPT-5 Responses API parameters
            response = llm.invoke(
                messages,
                reasoning={"effort": reasoning_effort},
                text={"verbosity": output_verbosity},
            )

            # GPT-5 Responses API returns content as a list of content blocks
            # Extract text from the response, filtering out reasoning metadata
            if isinstance(response.content, list):
                # Handle list of content blocks (GPT-5 Responses API format)
                answer_text = ""
                for block in response.content:
                    if isinstance(block, dict):
                        # Skip reasoning metadata blocks
                        if block.get("type") == "reasoning":
                            continue
                        # Extract text content
                        if "text" in block:
                            answer_text += block["text"]
                    elif isinstance(block, str):
                        answer_text += block
            else:
                # Handle simple string response (fallback)
                answer_text = str(response.content)

            logger.debug(f"Received answer: {answer_text[:100]}...")

            return answer_text, merged

        except Exception as e:
            logger.error(f"RAG chain execution failed: {e}")
            raise

    return chain_fn
