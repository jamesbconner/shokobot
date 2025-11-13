import logging
from collections.abc import Awaitable, Callable, Sequence
from typing import TYPE_CHECKING, Any

from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from prompts import build_anime_rag_json_prompt, build_anime_rag_prompt

if TYPE_CHECKING:
    from services.app_context import AppContext

logger = logging.getLogger(__name__)


def _extract_anime_title_regex(query: str) -> str | None:
    """Try to extract anime title using regex patterns.

    Args:
        query: Natural language query.

    Returns:
        Extracted anime title or None if no pattern matches.
    """
    import re

    # Common question patterns
    patterns = [
        r"tell me about (?:the )?(?:anime )?(?:called )?['\"]?(.+?)['\"]?\.?$",
        r"what (?:is|are) (?:the )?(?:anime )?['\"]?(.+?)['\"]? (?:about|like)",
        r"(?:search for|find) (?:the )?(?:anime )?['\"]?(.+?)['\"]?\.?$",
        r"(?:anime )?(?:called|named) ['\"]?(.+?)['\"]?\.?$",
        r"(?:best|worst|top) (?:episodes?|seasons?) (?:of|from) (?:the )?(?:anime )?['\"]?(.+?)['\"]?\.?$",
    ]

    query_lower = query.lower().strip()

    for pattern in patterns:
        match = re.search(pattern, query_lower, re.IGNORECASE)
        if match:
            title = match.group(1).strip()
            # Remove trailing punctuation
            title = re.sub(r"[.!?]+$", "", title)
            logger.debug(f"Regex extracted title '{title}' from query '{query}'")
            return title

    return None


async def _extract_anime_title_llm(query: str, ctx: "AppContext") -> str:
    """Extract anime title using LLM when regex fails.

    Args:
        query: Natural language query.
        ctx: Application context with LLM access.

    Returns:
        Extracted anime title.
    """
    from langchain_openai import ChatOpenAI

    from prompts import build_title_extraction_prompt

    logger.debug(f"Using LLM to extract title from query: '{query}'")

    # Use configured GPT-5 model from context
    model_name = ctx.config.get("openai.model")
    if not model_name:
        logger.warning("No model configured, using original query")
        return query

    # GPT-5 Responses API (no temperature/top_p parameters)
    llm = ChatOpenAI(
        model=model_name,
        max_completion_tokens=150,  # Anime titles can be very long (especially isekai)
    )

    prompt = build_title_extraction_prompt()
    messages = prompt.format_messages(query=query)

    try:
        # Use GPT-5 Responses API
        response = llm.invoke(
            messages,
            reasoning={"effort": "low"},  # Simple task, low reasoning
            text={"verbosity": "low"},  # Just the title, minimal verbosity
        )

        # Extract text from GPT-5 response
        if isinstance(response.content, list):
            title = ""
            for block in response.content:
                if isinstance(block, dict) and block.get("type") != "reasoning":
                    title += block.get("text", "")
                elif isinstance(block, str):
                    title += block
            title = title.strip()
        else:
            title = str(response.content).strip()

        logger.info(f"LLM extracted title '{title}' from query '{query}'")
        return title
    except Exception as e:
        logger.warning(f"LLM title extraction failed: {e}, using original query")
        return query


async def _extract_anime_title(query: str, ctx: "AppContext") -> str:
    """Extract anime title from a natural language query.

    Uses a hybrid approach:
    1. Try regex patterns first (fast, no API cost)
    2. Fall back to LLM if regex fails (handles any pattern)

    Args:
        query: Natural language query.
        ctx: Application context with LLM access.

    Returns:
        Extracted anime title.
    """
    # Try regex first
    title = _extract_anime_title_regex(query)
    if title:
        return title

    # Fall back to LLM
    logger.info("Regex patterns failed, using LLM for title extraction")
    return await _extract_anime_title_llm(query, ctx)


async def search_with_mcp_fallback(
    query: str,
    ctx: "AppContext",
) -> list[Document]:
    """Search vector store with MCP fallback for insufficient results.

    Queries the vector store first. If results don't meet both count and score
    thresholds, attempts to fetch data from AniDB via MCP server, persists it,
    and adds it to the vector store.

    Args:
        query: Search query string.
        ctx: Application context with configuration and services.

    Returns:
        List of Document objects from vector store and/or MCP.

    Raises:
        ValueError: If query is empty.
    """
    if not query or not query.strip():
        raise ValueError("Query cannot be empty")

    # Get k from context (set by CLI or defaults to 10)
    k = ctx.retrieval_k

    # Get thresholds from config
    count_threshold = ctx.config.get_mcp_fallback_count_threshold()
    score_threshold = ctx.config.get_mcp_fallback_score_threshold()

    logger.debug(
        f"Searching with MCP fallback: query='{query}', k={k}, "
        f"count_threshold={count_threshold}, score_threshold={score_threshold}"
    )

    # Query vector store with similarity scores
    # Retrieve k documents, then check if they meet thresholds
    vs = ctx.vectorstore
    results = vs.similarity_search_with_score(query, k=k)

    # Evaluate results
    result_count = len(results)
    # For distance scores: lower = better, so we want the minimum (best) score
    best_score = min((score for _, score in results), default=float("inf"))

    logger.debug(
        f"Vector store returned {result_count} results, best score: {best_score:.3f} (lower=better)"
    )

    # Check if both thresholds are met
    # For distance scores: good results have LOW scores, so check if best score is BELOW threshold
    count_met = result_count >= count_threshold
    score_met = best_score <= score_threshold

    if count_met and score_met:
        logger.debug("Both thresholds met, returning vector store results")
        docs = [doc for doc, _ in results]
        # Store distance scores in document metadata
        for doc, distance in results:
            doc.metadata["_distance_score"] = distance
        return docs

    # Check if MCP is enabled
    if not ctx.config.get_mcp_enabled():
        logger.debug("MCP disabled, returning vector store results only")
        docs = [doc for doc, _ in results]
        # Store distance scores in document metadata
        for doc, distance in results:
            doc.metadata["_distance_score"] = distance
        return docs

    # Trigger MCP fallback
    reason = []
    if not count_met:
        reason.append(f"count {result_count} < {count_threshold}")
    if not score_met:
        reason.append(f"score {best_score:.3f} < {score_threshold}")

    logger.info(f"MCP fallback triggered for query '{query}': {', '.join(reason)}")

    try:
        # Import services needed for MCP fallback
        from services.mcp_anime_json_parser import parse_anidb_json
        from services.mcp_client_service import create_mcp_client
        from services.showdoc_persistence import ShowDocPersistence
        from services.vectorstore_service import upsert_documents

        # Initialize persistence
        cache_dir = ctx.config.get_mcp_cache_dir()
        persistence = ShowDocPersistence(cache_dir)

        # Connect to MCP server
        async with await create_mcp_client(ctx) as mcp:
            # Extract anime title from natural language query
            anime_title = await _extract_anime_title(query, ctx)
            logger.info(f"Searching MCP for anime title: '{anime_title}'")

            # Search for anime
            search_results = await mcp.search_anime(anime_title)

            if not search_results:
                logger.info(f"No MCP results found for query '{query}'")
                docs = [doc for doc, _ in results]
                # Store distance scores in document metadata
                for doc, distance in results:
                    doc.metadata["_distance_score"] = distance
                return docs

            # Process first result
            mcp_docs = []
            for search_result in search_results[:1]:  # Only process top result
                # Extract anime ID from search result
                if isinstance(search_result, dict):
                    aid = search_result.get("aid")
                elif hasattr(search_result, "aid"):
                    aid = search_result.aid
                else:
                    logger.warning(f"Could not extract aid from search result: {search_result}")
                    continue

                if not aid:
                    logger.warning("Search result missing anime ID")
                    continue

                # Check persistence cache first
                if persistence.exists(aid):
                    logger.debug(f"Loading anime {aid} from persistence cache")
                    show_doc = persistence.load_showdoc(aid)
                    if show_doc:
                        mcp_docs.append(show_doc.to_langchain_doc())
                        logger.info(f"Loaded cached anime: {show_doc.title_main} ({aid})")
                        continue

                # Fetch from MCP
                logger.debug(f"Fetching anime details from MCP: {aid}")
                json_data = await mcp.get_anime_details(aid)

                if not json_data:
                    logger.warning(f"No JSON data returned for anime {aid}")
                    continue

                # Parse JSON to ShowDoc
                show_doc = parse_anidb_json(json_data)
                logger.info(f"Fetched anime from MCP: {show_doc.title_main} ({aid})")

                # Save to persistence
                persistence.save_showdoc(show_doc)
                logger.info(f"Persisted anime to cache: {show_doc.title_main}")

                # Convert to LangChain Document
                doc = show_doc.to_langchain_doc()
                mcp_docs.append(doc)

                # Upsert to vector store
                upsert_documents([doc], ctx)
                logger.info(f"Added anime to vector store: {show_doc.title_main}")

            # Merge and deduplicate results by anime_id
            seen_ids = set()
            merged_docs = []

            # Add MCP docs first (higher priority)
            # MCP docs get distance 0.0 (perfect match from external source)
            for doc in mcp_docs:
                anime_id = doc.metadata.get("anime_id")
                if anime_id and anime_id not in seen_ids:
                    seen_ids.add(anime_id)
                    doc.metadata["_distance_score"] = 0.0
                    merged_docs.append(doc)

            # Add vector store docs with their distance scores
            for doc, distance in results:
                anime_id = doc.metadata.get("anime_id")
                if anime_id and anime_id not in seen_ids:
                    seen_ids.add(anime_id)
                    doc.metadata["_distance_score"] = distance
                    merged_docs.append(doc)

            logger.debug(f"Returning {len(merged_docs)} merged documents")
            return merged_docs

    except Exception as e:
        logger.error(f"MCP fallback failed: {e}", exc_info=True)
        logger.info("Continuing with vector store results only")
        docs = [doc for doc, _ in results]
        # Store distance scores in document metadata
        for doc, distance in results:
            doc.metadata["_distance_score"] = distance
        return docs


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
            model_kwargs={"response_format": {"type": "json_object"}},
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
) -> Callable[[str], Awaitable[tuple[str, list[Document]]]]:
    """Build RAG chain for answering anime-related questions.

    Uses LangChain's ChatOpenAI with native Responses API support for GPT-5 models.
    Includes MCP fallback for poor quality vector store results.

    Args:
        ctx: Application context with configuration and vectorstore access.
        output_format: Output format - "text" (default) or "json" for structured output.

    Returns:
        Async callable that takes a question string and returns (answer_text, context_docs).

    Raises:
        ValueError: If required configuration is missing or invalid output format.

    Note:
        The returned chain function is async and must be awaited.
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

    async def chain_fn(question: str) -> tuple[str, list[Document]]:
        """Execute RAG chain for a given question.

        Args:
            question: User question about anime.

        Returns:
            Tuple of (answer_text, list of context documents used).

        Raises:
            Exception: If retrieval or LLM invocation fails.

        Note:
            This function is async and must be awaited.
        """
        if not question or not question.strip():
            raise ValueError("Question cannot be empty")

        logger.info(f"Processing question: {question[:100]}...")

        try:
            # Get pre-filtered documents for exact matches
            pre_docs = alias_prefilter(question, ctx) or []
            logger.debug(f"Prefilter returned {len(pre_docs)} documents")

            # Get semantic search results with MCP fallback
            # This will automatically trigger MCP if vector store results are poor
            docs = await search_with_mcp_fallback(question, ctx)
            logger.debug(f"Search (with MCP fallback) returned {len(docs)} documents")

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
