"""Parser for AniDB XML responses to ShowDoc model."""

import json
import logging
import xml.etree.ElementTree as ET
from datetime import datetime

from models.show_doc import ShowDoc

logger = logging.getLogger(__name__)


def parse_anidb_xml(xml_data: str) -> ShowDoc:
    """Parse AniDB XML response into ShowDoc model.

    Args:
        xml_data: XML string from AniDB API.

    Returns:
        ShowDoc instance with parsed data.

    Raises:
        ValueError: If XML is invalid or missing required fields.
    """
    try:
        root = ET.fromstring(xml_data)
    except ET.ParseError as e:
        raise ValueError(f"Invalid XML: {e}")

    # Extract anime ID
    anime_id = root.get("id")
    if not anime_id:
        raise ValueError("Missing anime ID in XML")

    # Extract titles
    titles_elem = root.find("titles")
    title_main = ""
    title_alts = []

    if titles_elem is not None:
        for title in titles_elem.findall("title"):
            title_type = title.get("type")
            title_text = title.text or ""

            if title_type == "main":
                title_main = title_text
            else:
                title_alts.append(title_text)

    if not title_main:
        raise ValueError("Missing main title in XML")

    # Extract description
    description_elem = root.find("description")
    description = description_elem.text if description_elem is not None else ""

    # Extract episode count
    episode_count_elem = root.find("episodecount")
    episode_count = int(episode_count_elem.text) if episode_count_elem is not None else 0

    # Extract dates
    start_date_elem = root.find("startdate")
    end_date_elem = root.find("enddate")

    air_date = _parse_date(start_date_elem.text) if start_date_elem is not None else None
    end_date = _parse_date(end_date_elem.text) if end_date_elem is not None else None

    # Extract years from dates
    begin_year = air_date.year if air_date else None
    end_year = end_date.year if end_date else None

    # Extract ratings
    ratings_elem = root.find("ratings")
    rating = 0
    vote_count = 0

    if ratings_elem is not None:
        permanent_elem = ratings_elem.find("permanent")
        if permanent_elem is not None:
            try:
                # AniDB ratings are 0-10, convert to 0-1000
                rating = int(float(permanent_elem.text) * 100)
                vote_count = int(permanent_elem.get("count", 0))
            except (ValueError, TypeError):
                pass

    # Extract tags
    tags = []
    tags_elem = root.find("tags")
    if tags_elem is not None:
        for tag in tags_elem.findall("tag"):
            name_elem = tag.find("name")
            if name_elem is not None and name_elem.text:
                tags.append(name_elem.text)

    # Extract external resources
    ann_id = None
    crunchyroll_id = None
    wikipedia_id = None

    resources_elem = root.find("resources")
    if resources_elem is not None:
        for resource in resources_elem.findall("resource"):
            resource_type = resource.get("type")
            external = resource.find("externalentity")

            if external is not None:
                identifier_elem = external.find("identifier")
                if identifier_elem is not None and identifier_elem.text:
                    # Type 1 = ANN, Type 28 = Crunchyroll, Type 6 = Wikipedia
                    if resource_type == "1":
                        try:
                            ann_id = int(identifier_elem.text)
                        except ValueError:
                            pass
                    elif resource_type == "28":
                        crunchyroll_id = identifier_elem.text
                    elif resource_type == "6":
                        wikipedia_id = identifier_elem.text

    # Extract related anime
    relations = []
    related_elem = root.find("relatedanime")
    if related_elem is not None:
        for anime in related_elem.findall("anime"):
            rel_id = anime.get("id")
            rel_type = anime.get("type")
            rel_title = anime.text
            if rel_id and rel_type:
                relations.append({"id": rel_id, "type": rel_type, "title": rel_title or ""})

    # Extract similar anime
    similar = []
    similar_elem = root.find("similaranime")
    if similar_elem is not None:
        for anime in similar_elem.findall("anime"):
            sim_id = anime.get("id")
            sim_approval = anime.get("approval", "0")
            sim_total = anime.get("total", "0")
            sim_title = anime.text
            if sim_id:
                similar.append(
                    {
                        "id": sim_id,
                        "approval": sim_approval,
                        "total": sim_total,
                        "title": sim_title or "",
                    }
                )

    return ShowDoc(
        anime_id=anime_id,
        anidb_anime_id=int(anime_id),
        title_main=title_main,
        title_alts=title_alts,
        description=description,
        tags=tags,
        episode_count_normal=episode_count,
        episode_count_special=0,  # Not in basic XML
        air_date=air_date,
        end_date=end_date,
        begin_year=begin_year,
        end_year=end_year,
        rating=rating,
        vote_count=vote_count,
        avg_review_rating=0,  # Not in basic XML
        review_count=0,  # Not in basic XML
        ann_id=ann_id,
        crunchyroll_id=crunchyroll_id,
        wikipedia_id=wikipedia_id,
        relations=json.dumps(relations),
        similar=json.dumps(similar),
    )


def _parse_date(date_str: str | None) -> datetime | None:
    """Parse AniDB date string to datetime.

    Args:
        date_str: Date string in YYYY-MM-DD format.

    Returns:
        Parsed datetime or None if invalid.
    """
    if not date_str:
        return None

    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        logger.debug(f"Failed to parse date: {date_str}")
        return None
