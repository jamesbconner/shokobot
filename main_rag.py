import argparse
import logging
import sys
from typing import Iterable

from dotenv import load_dotenv

from services.config_service import ConfigService
from services.rag_service import build_rag_chain

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)


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


def iter_stdin() -> Iterable[str]:
    """Iterate over non-empty lines from stdin.
    
    Yields:
        Stripped non-empty lines from stdin.
    """
    for line in sys.stdin:
        q = line.strip()
        if q:
            yield q


def iter_file(path: str) -> Iterable[str]:
    """Iterate over non-empty lines from a file.
    
    Args:
        path: Path to text file.
        
    Yields:
        Stripped non-empty lines from the file.
        
    Raises:
        FileNotFoundError: If file doesn't exist.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                q = line.strip()
                if q:
                    yield q
    except FileNotFoundError:
        logger.error(f"File not found: {path}")
        raise


def run_question(rag, question: str, show_context: bool = False) -> int:
    """Execute a single question through the RAG chain.
    
    Args:
        rag: RAG chain callable.
        question: Question to ask.
        show_context: Whether to display context documents.
        
    Returns:
        Exit code (0 for success, 1 for failure).
    """
    try:
        answer_text, docs = rag(question)
        print(f"Q: {question}\n")
        print("A:", answer_text.strip(), "\n")
        
        if show_context:
            print("Context:")
            for d in docs:
                title = d.metadata.get("title_main")
                anime_id = d.metadata.get("anime_id")
                alts = d.metadata.get("title_alts") or []
                print(f" - {title} [anime_id={anime_id}]")
            print()
        
        return 0
    
    except Exception as e:
        logger.error(f"Failed to process question: {e}")
        return 1


def repl(rag, show_context: bool = False) -> int:
    """Run interactive REPL for asking questions.
    
    Args:
        rag: RAG chain callable.
        show_context: Whether to display context documents.
        
    Returns:
        Exit code (0 for success).
    """
    print("Interactive RAG. Type a question, or Ctrl+C to exit.")
    try:
        while True:
            q = input("> ").strip()
            if not q:
                continue
            run_question(rag, q, show_context)
    except (KeyboardInterrupt, EOFError):
        print()
        return 0


def main() -> int:
    """Main entry point for RAG query interface.
    
    Returns:
        Exit code (0 for success, 1 for failure).
    """
    try:
        cfg = ConfigService()
        log_level = cfg.get("logging.level", "INFO")
        setup_logging(log_level)
        
        logger.info("Starting RAG query interface")

        p = argparse.ArgumentParser(description="Ask questions against the anime RAG index.")
        gsrc = p.add_mutually_exclusive_group()
        gsrc.add_argument("-q", "--question", help="Single question to ask.")
        gsrc.add_argument("-f", "--file", help="Path to a text file with one question per line.")
        gsrc.add_argument("--stdin", action="store_true", help="Read questions from stdin, one per line.")
        p.add_argument("--k", type=int, default=10, help="Top-k retrieval.")
        p.add_argument("--show-context", action="store_true", help="Print retrieved titles and ids.")
        p.add_argument("--repl", action="store_true", help="Start interactive prompt.")
        args = p.parse_args()

        # Build the chain once
        logger.info("Building RAG chain...")
        rag = build_rag_chain()

        exit_code = 0
        if args.question:
            exit_code = run_question(rag, args.question, args.show_context)
        elif args.file:
            for q in iter_file(args.file):
                exit_code |= run_question(rag, q, args.show_context)
        elif args.stdin:
            for q in iter_stdin():
                exit_code |= run_question(rag, q, args.show_context)
        else:
            # Default to REPL if nothing else is provided
            exit_code = repl(rag, args.show_context)

        return exit_code
    
    except Exception as e:
        logging.error(f"Application failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
