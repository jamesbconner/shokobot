import logging
from collections.abc import Sequence
from typing import TYPE_CHECKING

from langchain_chroma import Chroma
from langchain_community.vectorstores.utils import filter_complex_metadata
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings

if TYPE_CHECKING:
    from services.app_context import AppContext

from services.config_service import ConfigService

logger = logging.getLogger(__name__)


def _create_embeddings(config: ConfigService) -> OpenAIEmbeddings:
    """Create OpenAI embeddings instance.

    Args:
        config: Configuration service instance.

    Returns:
        Configured OpenAIEmbeddings instance.

    Raises:
        ValueError: If embedding model configuration is invalid.
    """
    model = config.get("openai.embedding_model")
    if not model:
        raise ValueError("openai.embedding_model not configured")

    timeout = float(config.get("openai.request_timeout_s", 60))
    retries = int(config.get("openai.max_retries", 3))
    logger.info(
        f"Initializing embeddings with model={model}, timeout={timeout}s, max_retries={retries}"
    )

    return OpenAIEmbeddings(model=model, request_timeout=timeout, max_retries=retries)


def _validate_distance_function(vectorstore: Chroma, collection_name: str) -> None:
    """Validate that collection uses cosine distance.

    Args:
        vectorstore: ChromaDB vectorstore instance.
        collection_name: Name of the collection.

    Logs:
        Warning if incorrect distance function detected.
    """
    try:
        if hasattr(vectorstore, "_collection"):
            collection = vectorstore._collection
            metadata = getattr(collection, "metadata", None)

            if metadata is None or metadata.get("hnsw:space") != "cosine":
                actual = metadata.get("hnsw:space", "default (L2)") if metadata else "none"
                logger.warning(
                    f"Collection '{collection_name}' using {actual} distance instead of cosine. "
                    f"Run 'python scripts/migrate_chromadb_distance.py' to fix."
                )
            else:
                logger.info(
                    f"Collection '{collection_name}' correctly configured with cosine distance"
                )
    except Exception as e:
        logger.debug(f"Could not validate distance function: {e}")


def get_chroma_vectorstore(config: ConfigService) -> Chroma:
    """Get or create Chroma vector store with cosine distance.

    Args:
        config: Configuration service instance.

    Returns:
        Configured Chroma vector store instance with cosine distance.

    Raises:
        ValueError: If required configuration is missing.

    Notes:
        - Uses cosine distance for normalized embeddings from OpenAI
        - Validates existing collection's distance function
        - Logs warning if incorrect distance function detected
    """
    persist_dir = config.get("chroma.persist_directory")
    collection_name = config.get("chroma.collection_name")

    if not persist_dir or not collection_name:
        raise ValueError(
            "Chroma configuration incomplete: missing persist_directory or collection_name"
        )

    logger.info(f"Initializing Chroma vectorstore: collection={collection_name}, dir={persist_dir}")

    # Specify cosine distance for normalized embeddings
    collection_metadata = {"hnsw:space": "cosine"}

    # Create Chroma vector store with cosine distance
    vectorstore = Chroma(
        collection_name=collection_name,
        embedding_function=_create_embeddings(config),
        persist_directory=persist_dir,
        collection_metadata=collection_metadata,
    )

    # Validate distance function
    _validate_distance_function(vectorstore, collection_name)

    return vectorstore


def delete_by_anime_ids(anime_ids: Sequence[str], ctx: "AppContext") -> None:
    """Delete documents from vector store by anime IDs.

    Args:
        anime_ids: Sequence of anime ID strings to delete.
        ctx: Application context with vectorstore access.

    Raises:
        Exception: If deletion fails.
    """
    if not anime_ids:
        logger.debug("No anime IDs provided for deletion")
        return

    try:
        vs = ctx.vectorstore
        vs.delete(where={"anime_id": {"$in": list(map(str, anime_ids))}})
        logger.info(f"Deleted {len(anime_ids)} documents by anime_id")
    except Exception as e:
        logger.error(f"Failed to delete documents: {e}")
        raise


def upsert_documents(docs: list[Document], ctx: "AppContext") -> list[str]:
    """Idempotent upsert of documents by anime_id.

    Deletes existing documents with matching anime_ids, then adds the new batch.
    Filters complex metadata (lists, dicts) to ensure ChromaDB compatibility.

    Args:
        docs: List of LangChain Document instances to upsert.
        ctx: Application context with vectorstore access.

    Returns:
        List of document IDs that were upserted.

    Raises:
        ValueError: If documents are missing anime_id metadata.
        Exception: If upsert operation fails.
    """
    if not docs:
        logger.warning("No documents provided for upsert")
        return []

    try:
        vs = ctx.vectorstore
        ids = []

        # Filter complex metadata before upserting
        filtered_docs = filter_complex_metadata(docs)

        for d in filtered_docs:
            anime_id = d.metadata.get("anime_id")
            if not anime_id:
                raise ValueError(f"Document missing anime_id in metadata: {d.metadata}")
            ids.append(str(anime_id))

        # Delete existing documents with these IDs
        vs.delete(where={"anime_id": {"$in": ids}})

        # Add new documents
        vs.add_documents(filtered_docs, ids=ids)
        logger.info(f"Upserted {len(ids)} documents")

        return ids
    except Exception as e:
        logger.error(f"Failed to upsert documents: {e}")
        raise
