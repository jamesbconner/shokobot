"""Parser for AniDB JSON responses from MCP server to ShowDoc model."""

import json
import logging
from datetime import datetime

from models.show_doc import ShowDoc

logger = logging.getLogger(__name__)


def parse_anidb_json(json_data: str | dict) -> ShowDoc:
    """Parse AniDB JSON response from MCP server into ShowDoc model.

    The MCP server now returns parsed JSON instead of raw XML.

    Args:
        json_data: JSON string or dict from MCP server.

    Returns:
        ShowDoc instance with parsed data.

    Raises:
        ValueError: If JSON is invalid or missing required fields.
    """
    try:
        if isinstance(json_data, str):
            data = json.loads(json_data)
        else:
            data = json_data
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {e}")

    # Extract required fields
    anidb_anime_id = data.get("aid")
    if not anidb_anime_id:
        raise ValueError("Missing 'aid' field in JSON")

    # Since we don't have Shoko anime_id, use AniDB ID as anime_id
    # This is acceptable since we're getting data directly from AniDB
    anime_id = str(anidb_anime_id)

    # Extract main title
    title_main = data.get("title", "")
    if not title_main:
        raise ValueError("Missing 'title' field in JSON")

    # Extract alternate titles from titles array
    title_alts = []
    titles_list = data.get("titles", [])
    for title_obj in titles_list:
        if isinstance(title_obj, dict):
            title_text = title_obj.get("title", "")
            title_type = title_obj.get("type", "")
            # Include all non-main titles as alternates
            if title_text and title_type != "main":
                title_alts.append(title_text)

    # Extract description/synopsis
    description = data.get("synopsis", "")

    # Extract tags from tags array
    tags = []
    tags_list = data.get("tags", [])
    for tag_obj in tags_list:
        if isinstance(tag_obj, dict):
            tag_name = tag_obj.get("name", "")
            if tag_name:
                tags.append(tag_name)

    # Extract episode counts
    episode_count_normal = data.get("episode_count_normal", 0) or 0
    episode_count_special = data.get("episode_count_special", 0) or 0

    # Extract dates
    air_date = None
    end_date = None
    start_date_str = data.get("start_date")
    end_date_str = data.get("end_date")

    if start_date_str:
        try:
            air_date = datetime.fromisoformat(start_date_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            logger.warning(f"Could not parse start_date: {start_date_str}")

    if end_date_str:
        try:
            end_date = datetime.fromisoformat(end_date_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            logger.warning(f"Could not parse end_date: {end_date_str}")

    # Extract years
    begin_year = data.get("begin_year")
    end_year = data.get("end_year")

    # Extract ratings
    ratings = data.get("ratings", {})
    if isinstance(ratings, dict):
        # AniDB ratings are typically 0-10, convert to 0-1000 scale
        permanent_rating = ratings.get("permanent", 0.0)
        rating = int(permanent_rating * 100) if permanent_rating else 0
        vote_count = ratings.get("permanent_count", 0) or 0
        
        # Review ratings
        review_rating = ratings.get("review")
        avg_review_rating = int(review_rating * 100) if review_rating else 0
        review_count = ratings.get("review_count", 0) or 0
    else:
        rating = 0
        vote_count = 0
        avg_review_rating = 0
        review_count = 0

    # Extract external IDs
    ann_id = data.get("ann_id")
    crunchyroll_id = data.get("crunchyroll_id")
    wikipedia_id = data.get("wikipedia_id")

    # Extract related anime
    related_anime = data.get("related_anime", [])
    relations = json.dumps(related_anime) if related_anime else "[]"

    # Extract similar anime
    similar_anime = data.get("similar_anime", [])
    similar = json.dumps(similar_anime) if similar_anime else "[]"

    # Create ShowDoc
    try:
        show_doc = ShowDoc(
            anime_id=anime_id,
            anidb_anime_id=anidb_anime_id,
            title_main=title_main,
            title_alts=title_alts,
            description=description,
            tags=tags,
            episode_count_normal=episode_count_normal,
            episode_count_special=episode_count_special,
            air_date=air_date,
            end_date=end_date,
            begin_year=begin_year,
            end_year=end_year,
            rating=rating,
            vote_count=vote_count,
            avg_review_rating=avg_review_rating,
            review_count=review_count,
            ann_id=ann_id,
            crunchyroll_id=crunchyroll_id,
            wikipedia_id=wikipedia_id,
            relations=relations,
            similar=similar,
        )
        
        logger.info(f"Successfully parsed anime: {title_main} (AID: {anidb_anime_id})")
        return show_doc

    except Exception as e:
        logger.error(f"Failed to create ShowDoc: {e}")
        raise ValueError(f"Failed to create ShowDoc from JSON: {e}")
