import logging
from typing import Sequence

from langchain_chroma import Chroma
from langchain_community.vectorstores.utils import filter_complex_metadata
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings

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

    timeout = int(config.get("openai.request_timeout_s", 60))
    logger.info(f"Initializing embeddings with model={model}, timeout={timeout}s")

    return OpenAIEmbeddings(model=model, request_timeout=timeout)


def get_chroma_vectorstore(config: ConfigService) -> Chroma:
    """Get or create Chroma vector store instance.

    Args:
        config: Configuration service instance.

    Returns:
        Configured Chroma vector store instance.

    Raises:
        ValueError: If required configuration is missing.
    """
    persist_dir = config.get("chroma.persist_directory")
    collection_name = config.get("chroma.collection_name")

    if not persist_dir or not collection_name:
        raise ValueError(
            "Chroma configuration incomplete: missing persist_directory or collection_name"
        )

    logger.info(f"Initializing Chroma vectorstore: collection={collection_name}, dir={persist_dir}")

    return Chroma(
        collection_name=collection_name,
        embedding_function=_create_embeddings(config),
        persist_directory=persist_dir,
    )


def delete_by_anime_ids(anime_ids: Sequence[str], config: ConfigService) -> None:
    """Delete documents from vector store by anime IDs.

    Args:
        anime_ids: Sequence of anime ID strings to delete.
        config: Configuration service instance.

    Raises:
        Exception: If deletion fails.
    """
    if not anime_ids:
        logger.debug("No anime IDs provided for deletion")
        return

    try:
        vs = get_chroma_vectorstore(config)
        vs.delete(where={"anime_id": {"$in": list(map(str, anime_ids))}})
        logger.info(f"Deleted {len(anime_ids)} documents by anime_id")
    except Exception as e:
        logger.error(f"Failed to delete documents: {e}")
        raise


def upsert_documents(docs: list[Document], config: ConfigService) -> list[str]:
    """Idempotent upsert of documents by anime_id.

    Deletes existing documents with matching anime_ids, then adds the new batch.
    Filters complex metadata (lists, dicts) to ensure ChromaDB compatibility.

    Args:
        docs: List of LangChain Document instances to upsert.
        config: Configuration service instance.

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
        vs = get_chroma_vectorstore(config)
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
