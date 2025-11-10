import json
import logging
from collections.abc import Iterable, Iterator
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:
    from services.app_context import AppContext

from models.show_doc import ShowDoc
from services.vectorstore_service import upsert_documents
from utils.batch_utils import chunked
from utils.text_utils import clean_description, split_pipe

logger = logging.getLogger(__name__)

IdField = Literal["AnimeID", "AniDB_AnimeID"]


def _pick_id(rec: dict[str, Any], id_field: IdField = "AnimeID") -> str:
    """Extract anime ID from record using specified field.

    Args:
        rec: Dictionary containing anime record data.
        id_field: Primary field name to use for ID extraction.

    Returns:
        String representation of the anime ID.

    Raises:
        ValueError: If no valid ID field is found in the record.
    """
    val = rec.get(id_field) or rec.get("AnimeID") or rec.get("AniDB_AnimeID")
    if val is None:
        raise ValueError(f"Record missing both AnimeID and AniDB_AnimeID: {rec}")
    return str(val)


def _titles(rec: dict[str, Any]) -> tuple[str, list[str]]:
    """Extract main title and alternate titles from record.

    Args:
        rec: Dictionary containing anime record data.

    Returns:
        Tuple of (main_title, list_of_all_titles) where the main title
        is included in the list and duplicates are removed.
    """
    main = str(rec.get("MainTitle") or "").strip()
    if not main:
        logger.warning(f"Record missing MainTitle: {rec.get('AnimeID', 'unknown')}")
        main = "Unknown Title"

    alts = split_pipe(rec.get("AllTitles"))
    alts = [main] + [t for t in alts if t.lower() != main.lower()]
    return main, alts


def _tags(rec: dict[str, Any]) -> list[str]:
    """Extract tags from record.

    Args:
        rec: Dictionary containing anime record data.

    Returns:
        List of tag strings.
    """
    return split_pipe(rec.get("AllTags"))


def _description(rec: dict[str, Any]) -> str:
    """Extract and clean description from record.

    Args:
        rec: Dictionary containing anime record data.

    Returns:
        Cleaned description string.
    """
    return clean_description(rec.get("Description"))


def _parse_datetime(date_str: str | None) -> datetime | None:
    """Parse datetime string from Shoko format.

    Args:
        date_str: Date string in format 'YYYY-MM-DD HH:MM:SS'.

    Returns:
        Parsed datetime or None if invalid/empty.
    """
    if not date_str or not isinstance(date_str, str):
        return None

    try:
        return datetime.strptime(date_str.strip(), "%Y-%m-%d %H:%M:%S")
    except (ValueError, AttributeError):
        logger.debug(f"Failed to parse datetime: {date_str}")
        return None


def _safe_int(value: Any, default: int = 0) -> int:
    """Safely convert value to int with default fallback.

    Args:
        value: Value to convert.
        default: Default value if conversion fails.

    Returns:
        Integer value or default.
    """
    if value is None:
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def _safe_str(value: Any) -> str | None:
    """Safely convert value to string, returning None for empty strings.

    Args:
        value: Value to convert.

    Returns:
        String value or None if empty.
    """
    if value is None:
        return None
    s = str(value).strip()
    return s if s else None


def iter_showdocs_from_json(
    ctx: "AppContext",
    path: str | Path | None = None,
    id_field: IdField = "AnimeID",
) -> Iterator[ShowDoc]:
    """Load and iterate over anime show documents from JSON file.

    Args:
        ctx: Application context with configuration access.
        path: Path to JSON file containing anime data. If None, uses config default.
        id_field: Field name to use as primary anime ID.

    Yields:
        ShowDoc instances parsed from the JSON data.

    Raises:
        FileNotFoundError: If the JSON file doesn't exist.
        json.JSONDecodeError: If the JSON file is malformed.
        ValueError: If a record is missing required ID fields.
    """
    path = Path(path or ctx.config.get("data.shows_json"))

    if not path.exists():
        raise FileNotFoundError(f"Shows JSON file not found: {path}")

    try:
        with path.open(encoding="utf-8") as f:
            raw = json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON from {path}: {e}")
        raise

    rows = raw.get("AniDB_Anime")
    if not rows:
        logger.warning(f"No 'AniDB_Anime' key found in {path}")
        return

    if not isinstance(rows, list):
        raise ValueError(f"Expected 'AniDB_Anime' to be a list, got {type(rows)}")

    logger.info(f"Processing {len(rows)} anime records from {path}")

    for idx, r in enumerate(rows):
        try:
            title_main, title_alts = _titles(r)

            # Extract AniDB_AnimeID (required)
            anidb_id = r.get("AniDB_AnimeID")
            if not anidb_id:
                logger.warning(f"Record {idx} missing AniDB_AnimeID, skipping")
                continue

            yield ShowDoc(
                anime_id=_pick_id(r, id_field=id_field),
                anidb_anime_id=anidb_id,
                title_main=title_main,
                title_alts=title_alts,
                description=_description(r),
                tags=_tags(r),
                episode_count_normal=_safe_int(r.get("EpisodeCountNormal"), 0),
                episode_count_special=_safe_int(r.get("EpisodeCountSpecial"), 0),
                air_date=_parse_datetime(r.get("AirDate")),
                end_date=_parse_datetime(r.get("EndDate")),
                begin_year=_safe_int(r.get("BeginYear")) or None,
                end_year=_safe_int(r.get("EndYear")) or None,
                rating=_safe_int(r.get("Rating"), 0),
                vote_count=_safe_int(r.get("VoteCount"), 0),
                avg_review_rating=_safe_int(r.get("AvgReviewRating"), 0),
                review_count=_safe_int(r.get("ReviewCount"), 0),
                ann_id=_safe_int(r.get("ANNID")) or None,
                crunchyroll_id=_safe_str(r.get("CrunchyrollID")),
                wikipedia_id=_safe_str(r.get("Wikipedia_ID")),
                relations=_safe_str(r.get("relations")) or "[]",
                similar=_safe_str(r.get("similar")) or "[]",
            )
        except (ValueError, KeyError) as e:
            logger.error(f"Failed to process record {idx}: {e}")
            continue


def ingest_showdocs_streaming(
    docs_iter: Iterable[ShowDoc],
    ctx: "AppContext",
    batch_size: int | None = None,
) -> int:
    """Ingest show documents into vector store in batches.

    Args:
        docs_iter: Iterable of ShowDoc instances to ingest.
        ctx: Application context with configuration and vectorstore access.
        batch_size: Number of documents per batch. If None, uses config default.

    Returns:
        Total number of documents successfully ingested.

    Raises:
        ValueError: If batch_size is invalid.
    """
    batch_size = batch_size or int(ctx.config.get("ingest.batch_size", 256))

    if batch_size <= 0:
        raise ValueError(f"batch_size must be positive, got {batch_size}")

    logger.info(f"Starting ingestion with batch_size={batch_size}")
    total = 0
    batch_count = 0

    try:
        for batch in chunked((d.to_langchain_doc() for d in docs_iter), batch_size):
            batch_list = list(batch)
            upsert_documents(batch_list, ctx)
            total += len(batch_list)
            batch_count += 1
            logger.debug(f"Ingested batch {batch_count} ({len(batch_list)} docs)")
    except Exception as e:
        logger.error(f"Ingestion failed after {total} documents: {e}")
        raise

    logger.info(f"Ingestion complete: {total} documents in {batch_count} batches")
    return total
