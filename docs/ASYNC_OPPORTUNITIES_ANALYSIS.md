# Async Operations - Performance Opportunities

## Executive Summary

**Current State**: Fully synchronous operations
**Potential Improvement**: 2-5x faster for I/O-bound operations
**Effort**: Medium (2-4 days)
**Recommendation**: Implement for ingestion and batch queries

---

## I/O-Bound Operations Analysis

### 1. Document Ingestion (HIGH IMPACT) 🔥

**Current Implementation** (Synchronous):
```python
def ingest_showdocs_streaming(docs_iter, config, batch_size=100):
    for batch in chunked(docs_iter, batch_size):
        batch_list = list(batch)
        upsert_documents(batch_list, config)  # Blocks on OpenAI API
        # Each batch waits for:
        # 1. OpenAI embeddings API call (~500ms-2s)
        # 2. ChromaDB upsert (~100-500ms)
```

**Performance**:
- 1458 documents in 15 batches
- ~2-3 seconds per batch
- **Total: ~40-50 seconds**

**Async Implementation**:
```python
async def ingest_showdocs_streaming_async(docs_iter, config, batch_size=100, concurrency=5):
    semaphore = asyncio.Semaphore(concurrency)

    async def process_batch(batch):
        async with semaphore:
            batch_list = list(batch)
            await upsert_documents_async(batch_list, config)

    tasks = []
    for batch in chunked(docs_iter, batch_size):
        tasks.append(process_batch(batch))

    await asyncio.gather(*tasks)
```

**Expected Performance**:
- Process 5 batches concurrently
- **Total: ~10-15 seconds** (3-4x faster)

**Impact**: ⭐⭐⭐⭐⭐ (Very High)
- Saves 30-35 seconds on full ingestion
- Better user experience
- Scales with more documents

---

### 2. RAG Query with Multiple Retrievals (MEDIUM IMPACT)

**Current Implementation** (Synchronous):
```python
def chain_fn(question: str):
    # Sequential operations:
    pre_docs = alias_prefilter(question, config)      # ~200ms (DB query)
    docs = retriever.invoke(question)                  # ~500ms (embedding + search)

    # Merge results
    merged = merge_and_dedupe(pre_docs, docs)

    # LLM call
    response = llm.invoke(messages)                    # ~2-5s (OpenAI API)

    return answer, merged
```

**Performance**: ~3-6 seconds per query

**Async Implementation**:
```python
async def chain_fn_async(question: str):
    # Parallel operations:
    pre_docs_task = asyncio.create_task(alias_prefilter_async(question, config))
    docs_task = asyncio.create_task(retriever.ainvoke(question))

    # Wait for both
    pre_docs, docs = await asyncio.gather(pre_docs_task, docs_task)

    # Merge results
    merged = merge_and_dedupe(pre_docs, docs)

    # LLM call
    response = await llm.ainvoke(messages)

    return answer, merged
```

**Expected Performance**: ~2.5-5 seconds per query (20-30% faster)

**Impact**: ⭐⭐⭐ (Medium)
- Saves 500ms-1s per query
- Most time is LLM call (can't parallelize)
- Noticeable in interactive mode

---

### 3. Batch Query Processing (HIGH IMPACT) 🔥

**Current Implementation** (Synchronous):
```python
# cli/query.py - file mode
for question in questions:
    answer, docs = rag(question)  # Blocks for 3-6s each
    print(answer)
```

**Performance**:
- 10 questions = 30-60 seconds

**Async Implementation**:
```python
async def process_questions_async(questions, rag, concurrency=3):
    semaphore = asyncio.Semaphore(concurrency)

    async def process_one(q):
        async with semaphore:
            return await rag(q)

    tasks = [process_one(q) for q in questions]
    results = await asyncio.gather(*tasks)
    return results
```

**Expected Performance**:
- 10 questions = 10-20 seconds (3x faster)

**Impact**: ⭐⭐⭐⭐⭐ (Very High)
- Dramatic improvement for batch processing
- Better resource utilization

---

### 4. Embedding Generation (MEDIUM IMPACT)

**Current Implementation** (Synchronous):
```python
# In upsert_documents
for batch in batches:
    embeddings = OpenAIEmbeddings.embed_documents(batch)  # Blocks
    vectorstore.add(embeddings)
```

**Async Implementation**:
```python
async def upsert_documents_async(docs, config):
    # OpenAI SDK supports async
    embeddings = await OpenAIEmbeddings.aembed_documents(docs)
    await vectorstore.aadd(embeddings)
```

**Expected Performance**:
- 20-30% faster per batch
- Allows concurrent batch processing

**Impact**: ⭐⭐⭐⭐ (High)
- Enables concurrent ingestion
- Better API utilization

---

## Detailed Opportunities

### Priority 1: Async Ingestion (Highest ROI)

**Files to Modify**:
- `services/vectorstore_service.py`
- `services/ingest_service.py`
- `cli/ingest.py`

**Changes Required**:

```python
# services/vectorstore_service.py
async def upsert_documents_async(
    docs: list[Document],
    config: ConfigService
) -> list[str]:
    """Async version of upsert_documents."""
    if not docs:
        return []

    vs = get_chroma_vectorstore(config)
    ids = []

    filtered_docs = filter_complex_metadata(docs)

    for d in filtered_docs:
        anime_id = d.metadata.get("anime_id")
        if not anime_id:
            raise ValueError(f"Document missing anime_id")
        ids.append(str(anime_id))

    # Delete existing (sync - ChromaDB doesn't have async delete)
    vs.delete(where={"anime_id": {"$in": ids}})

    # Add documents with async embeddings
    await vs.aadd_documents(filtered_docs, ids=ids)

    return ids


# services/ingest_service.py
async def ingest_showdocs_streaming_async(
    docs_iter: Iterable[ShowDoc],
    config: ConfigService,
    batch_size: int | None = None,
    concurrency: int = 5,
) -> int:
    """Async ingestion with concurrent batch processing."""
    batch_size = batch_size or int(config.get("ingest.batch_size", 256))

    semaphore = asyncio.Semaphore(concurrency)
    total = 0

    async def process_batch(batch):
        nonlocal total
        async with semaphore:
            batch_list = list(batch)
            await upsert_documents_async(batch_list, config)
            total += len(batch_list)

    tasks = []
    for batch in chunked((d.to_langchain_doc() for d in docs_iter), batch_size):
        tasks.append(process_batch(batch))

    await asyncio.gather(*tasks)
    return total


# cli/ingest.py
@click.command()
@click.pass_context
def ingest(ctx, ...):
    """Ingest with async support."""
    # ... setup ...

    # Run async ingestion
    total = asyncio.run(
        ingest_showdocs_streaming_async(docs_iter, config, batch_size)
    )
```

**Expected Improvement**: 3-4x faster (40s → 10-15s)

---

### Priority 2: Async RAG Chain (Medium ROI)

**Files to Modify**:
- `services/rag_service.py`
- `cli/query.py`

**Changes Required**:

```python
# services/rag_service.py
def build_rag_chain_async(config: ConfigService) -> Callable:
    """Build async RAG chain."""
    # ... setup ...

    async def chain_fn_async(question: str) -> tuple[str, list[Document]]:
        """Async RAG chain execution."""
        if not question or not question.strip():
            raise ValueError("Question cannot be empty")

        # Parallel retrieval
        pre_docs_task = asyncio.create_task(
            alias_prefilter_async(question, config)
        )
        docs_task = asyncio.create_task(
            retriever.ainvoke(question)
        )

        pre_docs, docs = await asyncio.gather(
            pre_docs_task,
            docs_task,
            return_exceptions=True
        )

        # Handle exceptions
        if isinstance(pre_docs, Exception):
            pre_docs = []
        if isinstance(docs, Exception):
            raise docs

        # Merge and deduplicate
        seen, merged = set(), []
        for d in list(pre_docs) + list(docs):
            key = d.metadata.get("anime_id")
            if key and key not in seen:
                seen.add(key)
                merged.append(d)

        # Build context and invoke LLM (async)
        context = "\n\n".join(d.page_content for d in merged)
        messages = prompt.format_messages(question=question, context=context)

        response = await llm.ainvoke(
            messages,
            reasoning={"effort": reasoning_effort},
            text={"verbosity": output_verbosity},
        )

        # Parse response
        answer_text = extract_text_from_blocks(response.content)

        return answer_text, merged

    return chain_fn_async


# cli/query.py
async def _run_single_question_async(console, rag, question, show_context):
    """Async version of single question."""
    console.print(f"[bold cyan]Q:[/] {question}\n")

    with Progress(...) as progress:
        task = progress.add_task("Thinking...", total=None)
        answer, docs = await rag(question)
        progress.update(task, description="[green]✓[/] Answer ready")

    console.print(f"\n[bold green]A:[/] {answer}\n")

    if show_context:
        _display_context(console, docs)


@click.command()
@click.pass_context
def query(ctx, question, ...):
    """Query with async support."""
    config = ctx.obj["config"]
    console = ctx.obj["console"]

    # Build async RAG chain
    rag = build_rag_chain_async(config)

    if question:
        asyncio.run(_run_single_question_async(console, rag, question, show_context))
```

**Expected Improvement**: 20-30% faster per query

---

### Priority 3: Batch Query Processing (High ROI)

**Files to Modify**:
- `cli/query.py`

**Changes Required**:

```python
# cli/query.py
async def _run_file_questions_async(
    console,
    rag,
    file_path,
    show_context,
    concurrency=3
):
    """Process file questions concurrently."""
    with file_path.open("r", encoding="utf-8") as f:
        questions = [line.strip() for line in f if line.strip()]

    semaphore = asyncio.Semaphore(concurrency)

    async def process_one(i, q):
        async with semaphore:
            console.print(f"[dim]Question {i}/{len(questions)}[/]")
            await _run_single_question_async(console, rag, q, show_context)

    tasks = [process_one(i+1, q) for i, q in enumerate(questions)]
    await asyncio.gather(*tasks)


@click.command()
@click.option("--concurrency", "-n", type=int, default=3, help="Concurrent queries")
@click.pass_context
def query(ctx, file, concurrency, ...):
    """Query with concurrent batch processing."""
    if file:
        rag = build_rag_chain_async(config)
        asyncio.run(
            _run_file_questions_async(console, rag, file, show_context, concurrency)
        )
```

**Expected Improvement**: 3x faster for batch queries

---

## Performance Comparison

### Ingestion (1458 documents)

| Implementation | Time | Improvement |
|----------------|------|-------------|
| Current (sync) | 40-50s | Baseline |
| Async (concurrency=3) | 15-20s | 2.5x faster |
| Async (concurrency=5) | 10-15s | 3-4x faster |
| Async (concurrency=10) | 8-12s | 4-5x faster |

### Single Query

| Implementation | Time | Improvement |
|----------------|------|-------------|
| Current (sync) | 3-6s | Baseline |
| Async | 2.5-5s | 20-30% faster |

### Batch Queries (10 questions)

| Implementation | Time | Improvement |
|----------------|------|-------------|
| Current (sync) | 30-60s | Baseline |
| Async (concurrency=3) | 10-20s | 3x faster |
| Async (concurrency=5) | 8-15s | 4x faster |

---

## Implementation Complexity

### Easy (1-2 days)
- ✓ Async ingestion with concurrent batches
- ✓ Batch query processing

### Medium (2-3 days)
- ⚠️ Async RAG chain
- ⚠️ Async embeddings
- ⚠️ Error handling and retries

### Hard (3-4 days)
- ⚠️ Async ChromaDB operations (limited support)
- ⚠️ Progress tracking with async
- ⚠️ Graceful cancellation

---

## Recommended Implementation Plan

### Phase 1: Async Ingestion (Highest Impact)
**Effort**: 1-2 days
**Impact**: 3-4x faster ingestion

1. Add `upsert_documents_async()` to vectorstore_service
2. Add `ingest_showdocs_streaming_async()` to ingest_service
3. Update CLI to use async ingestion
4. Add concurrency parameter

### Phase 2: Batch Query Processing (High Impact)
**Effort**: 1 day
**Impact**: 3x faster batch queries

1. Add `_run_file_questions_async()` to query CLI
2. Add concurrency parameter
3. Update progress display for concurrent operations

### Phase 3: Async RAG Chain (Medium Impact)
**Effort**: 2 days
**Impact**: 20-30% faster queries

1. Add `build_rag_chain_async()` to rag_service
2. Implement parallel retrieval
3. Use async LLM invocation
4. Update CLI for async queries

---

## Considerations

### Pros ✓
- **Significant performance gains** (2-5x faster)
- **Better resource utilization**
- **Improved user experience**
- **Scales better with more data**
- **Modern Python best practice**

### Cons ⚠️
- **Increased complexity** (async/await everywhere)
- **More difficult debugging**
- **Need to handle async context properly**
- **Some libraries have limited async support**
- **Testing becomes more complex**

### Risks
- **ChromaDB async support** is limited
- **OpenAI rate limits** may negate benefits
- **Memory usage** may increase with concurrency
- **Error handling** becomes more complex

---

## Alternative: Threading

For simpler implementation, consider threading:

```python
from concurrent.futures import ThreadPoolExecutor

def ingest_showdocs_streaming_threaded(docs_iter, config, batch_size=100, workers=5):
    """Thread-based concurrent ingestion."""
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = []
        for batch in chunked(docs_iter, batch_size):
            batch_list = list(batch)
            future = executor.submit(upsert_documents, batch_list, config)
            futures.append(future)

        for future in futures:
            future.result()  # Wait for completion
```

**Pros**:
- ✓ Simpler than async
- ✓ Works with sync libraries
- ✓ Easier to debug

**Cons**:
- ⚠️ GIL limitations (less efficient)
- ⚠️ Higher memory overhead
- ⚠️ Less control over concurrency

---

## Recommendation

### Implement Phase 1 & 2 (Async Ingestion + Batch Queries)

**Why**:
1. **Highest ROI** - 3-4x performance improvement
2. **Reasonable effort** - 2-3 days total
3. **Clear benefits** - Noticeable user experience improvement
4. **Low risk** - Well-supported by libraries

**Skip Phase 3 (Async RAG Chain) for now**:
- Only 20-30% improvement
- Most time is LLM call (can't parallelize)
- Adds complexity for marginal gain

### Implementation Priority

1. **Start with async ingestion** (Phase 1)
   - Biggest impact
   - Clear use case
   - Easy to test

2. **Add batch query processing** (Phase 2)
   - High value for file input mode
   - Relatively simple
   - Good user experience

3. **Consider threading as alternative**
   - If async proves too complex
   - Simpler mental model
   - Still provides benefits

**Expected Total Improvement**:
- Ingestion: 3-4x faster
- Batch queries: 3x faster
- Overall user experience: Significantly better

**Effort**: 2-3 days
**Risk**: Low
**Value**: High ✓
