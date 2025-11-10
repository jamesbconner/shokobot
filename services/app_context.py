"""Application context for dependency injection."""

from collections.abc import Callable
from dataclasses import dataclass, field

from langchain_chroma import Chroma

from services.config_service import ConfigService


@dataclass
class AppContext:
    """Application context containing shared configuration and services.

    Provides lazy-loaded access to expensive resources like vectorstore and RAG chain.
    Services are initialized only when first accessed.

    Attributes:
        config: Configuration service instance.
    """

    config: ConfigService
    _vectorstore: Chroma | None = field(default=None, init=False, repr=False)
    _rag_chain: Callable[[str], tuple[str, list]] | None = field(
        default=None, init=False, repr=False
    )

    @classmethod
    def create(cls, config_path: str = "resources/config.json") -> "AppContext":
        """Create application context with configuration.

        Args:
            config_path: Path to configuration file.

        Returns:
            Initialized AppContext instance.

        Raises:
            FileNotFoundError: If config file doesn't exist.
            json.JSONDecodeError: If config file is malformed.
        """
        config = ConfigService(config_path)
        return cls(config=config)

    @property
    def vectorstore(self) -> Chroma:
        """Get or create ChromaDB vectorstore instance (lazy initialization).

        Returns:
            Configured Chroma vectorstore instance.

        Raises:
            ValueError: If vectorstore configuration is invalid.
        """
        if self._vectorstore is None:
            from services.vectorstore_service import get_chroma_vectorstore

            self._vectorstore = get_chroma_vectorstore(self.config)
        return self._vectorstore

    @property
    def rag_chain(self) -> Callable[[str], tuple[str, list]]:
        """Get or create RAG chain with default text output (lazy initialization).

        Returns:
            Callable that takes a question and returns (answer, context_docs).

        Raises:
            ValueError: If RAG chain configuration is invalid.
        """
        if self._rag_chain is None:
            from services.rag_service import build_rag_chain

            self._rag_chain = build_rag_chain(self, output_format="text")
        return self._rag_chain

    def get_rag_chain(self, output_format: str = "text") -> Callable[[str], tuple[str, list]]:
        """Get or create RAG chain with specified output format.

        Args:
            output_format: Output format - "text" (default) or "json" for structured output.

        Returns:
            Callable that takes a question and returns (answer, context_docs).

        Raises:
            ValueError: If RAG chain configuration is invalid or output format unsupported.
        """
        from services.rag_service import build_rag_chain

        # Don't cache when using non-default format
        if output_format != "text":
            return build_rag_chain(self, output_format=output_format)

        # Use cached version for default text format
        return self.rag_chain

    def reset_vectorstore(self) -> None:
        """Reset vectorstore instance, forcing reinitialization on next access.

        Useful after ingestion or when vectorstore state changes.
        """
        self._vectorstore = None

    def reset_rag_chain(self) -> None:
        """Reset RAG chain instance, forcing reinitialization on next access.

        Useful when configuration changes or after vectorstore updates.
        """
        self._rag_chain = None

    def reset_all(self) -> None:
        """Reset all cached services, forcing reinitialization on next access."""
        self._vectorstore = None
        self._rag_chain = None
