from datetime import datetime
from typing import Any

from langchain_core.documents import Document
from pydantic import BaseModel, Field, field_validator


class ShowDoc(BaseModel):
    """Data model for anime show document with comprehensive metadata.

    Attributes:
        anime_id: Unique Shoko anime identifier.
        anidb_anime_id: AniDB anime identifier.
        title_main: Primary title of the anime.
        title_alts: List of alternate titles and aliases.
        description: Text description of the anime.
        tags: List of tags/genres associated with the anime.
        episode_count_normal: Number of regular episodes.
        episode_count_special: Number of special episodes.
        air_date: Initial air date.
        end_date: Final air date.
        begin_year: Year the anime began airing.
        end_year: Year the anime finished airing.
        rating: AniDB rating score.
        vote_count: Number of votes on AniDB.
        avg_review_rating: Average review rating.
        review_count: Number of reviews.
        ann_id: Anime News Network ID.
        crunchyroll_id: Crunchyroll ID.
        wikipedia_id: Wikipedia page identifier.
        relations: JSON string of related anime.
        similar: JSON string of similar anime.
    """

    # Required identifiers
    anime_id: str = Field(..., min_length=1, description="Unique Shoko anime identifier")
    anidb_anime_id: int = Field(..., gt=0, description="AniDB anime identifier")

    # Title information
    title_main: str = Field(..., min_length=1, description="Primary anime title")
    title_alts: list[str] = Field(default_factory=list, description="Alternate titles")

    # Content
    description: str = Field(default="", description="Anime description")
    tags: list[str] = Field(default_factory=list, description="Tags and genres")

    # Episode counts
    episode_count_normal: int = Field(default=0, ge=0, description="Number of regular episodes")
    episode_count_special: int = Field(default=0, ge=0, description="Number of special episodes")

    # Dates
    air_date: datetime | None = Field(default=None, description="Initial air date")
    end_date: datetime | None = Field(default=None, description="Final air date")
    begin_year: int | None = Field(default=None, ge=1900, description="Year began airing")
    end_year: int | None = Field(default=None, ge=1900, description="Year finished airing")

    # Ratings
    rating: int = Field(default=0, ge=0, le=1000, description="AniDB rating score")
    vote_count: int = Field(default=0, ge=0, description="Number of votes")
    avg_review_rating: int = Field(default=0, ge=0, description="Average review rating")
    review_count: int = Field(default=0, ge=0, description="Number of reviews")

    # External IDs
    ann_id: int | None = Field(default=None, gt=0, description="Anime News Network ID")
    crunchyroll_id: str | None = Field(default=None, description="Crunchyroll ID")
    wikipedia_id: str | None = Field(default=None, description="Wikipedia page identifier")

    # Relationships (stored as JSON strings)
    relations: str = Field(default="[]", description="JSON string of related anime")
    similar: str = Field(default="[]", description="JSON string of similar anime")

    @field_validator("anime_id", "title_main")
    @classmethod
    def validate_non_empty_strings(cls, v: str) -> str:
        """Ensure required string fields are not empty after stripping.

        Args:
            v: String value to validate.

        Returns:
            Stripped string value.

        Raises:
            ValueError: If string is empty after stripping.
        """
        stripped = v.strip()
        if not stripped:
            raise ValueError("Field cannot be empty or whitespace")
        return stripped

    @field_validator("title_alts", "tags")
    @classmethod
    def validate_string_lists(cls, v: list[str]) -> list[str]:
        """Remove empty strings and strip whitespace from list items.

        Args:
            v: List of strings to validate.

        Returns:
            Cleaned list with non-empty, stripped strings.
        """
        return [item.strip() for item in v if item and item.strip()]

    @field_validator("crunchyroll_id", "wikipedia_id")
    @classmethod
    def validate_optional_strings(cls, v: str | None) -> str | None:
        """Convert empty strings to None for optional string fields.

        Args:
            v: Optional string value.

        Returns:
            Stripped string or None if empty.
        """
        if v is None or not v.strip():
            return None
        return v.strip()

    @field_validator("end_year")
    @classmethod
    def validate_end_year(cls, v: int | None, info: Any) -> int | None:
        """Ensure end_year is not before begin_year.

        Args:
            v: End year value.
            info: Validation context with other field values.

        Returns:
            Validated end year.

        Raises:
            ValueError: If end_year is before begin_year.
        """
        if v is not None and "begin_year" in info.data:
            begin_year = info.data["begin_year"]
            if begin_year is not None and v < begin_year:
                raise ValueError(f"end_year ({v}) cannot be before begin_year ({begin_year})")
        return v

    def to_langchain_doc(self) -> Document:
        """Convert ShowDoc to LangChain Document format.

        Creates a Document with formatted page content and structured metadata
        suitable for vector store ingestion. Note that complex metadata (lists, dates)
        will be filtered by the vector store service.

        Returns:
            LangChain Document instance with anime data.
        """
        # Build comprehensive metadata
        metadata = {
            "anime_id": self.anime_id,
            "anidb_anime_id": self.anidb_anime_id,
            "title_main": self.title_main,
            "title_alts": self.title_alts,
            "description": self.description,
            "tags": self.tags,
            "episode_count_normal": self.episode_count_normal,
            "episode_count_special": self.episode_count_special,
            "air_date": self.air_date.isoformat() if self.air_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "begin_year": self.begin_year,
            "end_year": self.end_year,
            "rating": self.rating,
            "vote_count": self.vote_count,
            "avg_review_rating": self.avg_review_rating,
            "review_count": self.review_count,
            "ann_id": self.ann_id,
            "crunchyroll_id": self.crunchyroll_id,
            "wikipedia_id": self.wikipedia_id,
            "relations": self.relations,
            "similar": self.similar,
        }

        # Build rich text content for embedding
        parts = [self.title_main]

        if self.title_alts:
            parts.append(f"Also known as: {', '.join(self.title_alts[:5])}")

        if self.description:
            parts.append(self.description)

        if self.tags:
            parts.append(f"Tags: {', '.join(self.tags)}")

        if self.episode_count_normal:
            parts.append(f"Episodes: {self.episode_count_normal}")

        if self.begin_year:
            year_str = (
                f"{self.begin_year}-{self.end_year}"
                if self.end_year and self.end_year != self.begin_year
                else str(self.begin_year)
            )
            parts.append(f"Year: {year_str}")

        text = "\n\n".join(parts)
        return Document(page_content=text, metadata=metadata)

    model_config = {"frozen": False, "validate_assignment": True}
