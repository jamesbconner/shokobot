import logging
from collections.abc import Callable, Sequence
from typing import TYPE_CHECKING, Any

from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from prompts import build_anime_rag_json_prompt, build_anime_rag_prompt

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


def _init_llm(
    model_name: str, max_output_tokens: int, output_format: str
) -> tuple[ChatOpenAI, ChatPromptTemplate]:
    """Initialize ChatOpenAI LLM and prompt template based on output format.

    Args:
        model_name: OpenAI model name (e.g., "gpt-5-nano").
        max_output_tokens: Maximum tokens for completion.
        output_format: Output format - "text" or "json".

    Returns:
        Tuple of (ChatOpenAI instance, ChatPromptTemplate instance).

    Raises:
        ValueError: If output_format is invalid.
    """
    if output_format == "json":
        # For JSON output, explicitly pass response_format parameter
        # This avoids the kwargs warning by using explicit parameter names
        llm = ChatOpenAI(
            model=model_name,
            max_completion_tokens=max_output_tokens,
            timeout=120,
            max_retries=3,
            model_kwargs={
                "response_format": {"type": "json_object"}
            }
        )
        prompt = build_anime_rag_json_prompt()
    elif output_format == "text":
        # For text output, use standard initialization
        llm = ChatOpenAI(
            model=model_name,
            max_completion_tokens=max_output_tokens,
            timeout=120,
            max_retries=3,
        )
        prompt = build_anime_rag_prompt()
    else:
        raise ValueError(f"output_format must be 'text' or 'json', got '{output_format}'")

    return llm, prompt


def build_rag_chain(
    ctx: "AppContext", output_format: str = "text"
) -> Callable[[str], tuple[str, list[Document]]]:
    """Build RAG chain for answering anime-related questions.

    Uses LangChain's ChatOpenAI with native Responses API support for GPT-5 models.

    Args:
        ctx: Application context with configuration and vectorstore access.
        output_format: Output format - "text" (default) or "json" for structured output.

    Returns:
        Callable that takes a question string and returns (answer_text, context_docs).

    Raises:
        ValueError: If required configuration is missing or invalid output format.
    """
    if output_format not in ("text", "json"):
        raise ValueError(f"output_format must be 'text' or 'json', got '{output_format}'")

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

    # Get configuration for GPT-5 Responses API with validation
    reasoning_effort = ctx.config.get_reasoning_effort()
    output_verbosity = ctx.config.get_output_verbosity()
    max_output_tokens = ctx.config.get_max_output_tokens()

    logger.info(
        f"Building RAG chain with model={model_name}, "
        f"reasoning_effort={reasoning_effort}, "
        f"text_verbosity={output_verbosity}, "
        f"output_format={output_format}"
    )

    # Initialize LLM and prompt based on output format
    # This avoids kwargs warnings by using explicit parameters
    llm, prompt = _init_llm(model_name, max_output_tokens, output_format)

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
            answer_text = ""
            if isinstance(response.content, list):
                # Handle list of content blocks (GPT-5 Responses API format)
                for block in response.content:
                    if isinstance(block, dict):
                        # Skip reasoning metadata blocks
                        if block.get("type") == "reasoning":
                            continue
                        # Keep only user-visible text blocks
                        block_type = block.get("type")
                        if block_type in (None, "output_text", "text"):
                            answer_text += block.get("text", "")
                    elif isinstance(block, str):
                        answer_text += block
            else:
                # Handle simple string response (fallback)
                answer_text = str(response.content)

            answer_text = answer_text.strip()

            # For JSON output, extract the answer field from the JSON response
            if output_format == "json":
                import json

                try:
                    json_response = json.loads(answer_text)
                    # Extract the answer field if it exists, otherwise use the whole response
                    answer_text = json_response.get("answer", answer_text)
                except json.JSONDecodeError:
                    # If parsing fails, use the raw text
                    logger.warning("Failed to parse JSON response, using raw text")

            logger.debug(f"Received answer: {answer_text[:100]}...")

            return answer_text, merged

        except Exception as e:
            logger.error(f"RAG chain execution failed: {e}")
            raise

    return chain_fn
