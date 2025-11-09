import logging
import sys

from dotenv import load_dotenv

from services.ingest_service import iter_showdocs_from_json, ingest_showdocs_streaming
from services.config_service import ConfigService

# Load environment variables from .env file
load_dotenv()


def setup_logging(level: str = "INFO") -> None:
    """Configure logging for the application.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
    """
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )


def main() -> int:
    """Main entry point for ingestion process.
    
    Returns:
        Exit code (0 for success, 1 for failure).
    """
    try:
        cfg = ConfigService()
        log_level = cfg.get("logging.level", "INFO")
        setup_logging(log_level)
        
        logger = logging.getLogger(__name__)
        logger.info("Starting ingestion process")
        logger.info(f"Using config: {cfg.as_dict()['chroma']}")
        
        docs_iter = iter_showdocs_from_json(id_field="AnimeID")
        total = ingest_showdocs_streaming(docs_iter)
        
        logger.info(f"Ingestion complete: {total} documents processed")
        return 0
    
    except Exception as e:
        logging.error(f"Ingestion failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
