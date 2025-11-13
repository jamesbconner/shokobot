"""Tests for AniDB XML parser."""

from pathlib import Path

import pytest

from services.anidb_parser import _parse_date, parse_anidb_xml


class TestParseAnidbXml:
    """Tests for parse_anidb_xml function."""

    def test_parse_dan_da_dan_season_2(self) -> None:
        """Test parsing Dan Da Dan Season 2 XML (resources/19060.xml)."""
        # Arrange
        xml_file = Path("resources/19060.xml")
        xml_data = xml_file.read_text(encoding="utf-8")

        # Act
        show_doc = parse_anidb_xml(xml_data)

        # Assert
        assert show_doc.anime_id == "19060"
        assert show_doc.anidb_anime_id == 19060
        assert show_doc.title_main == "Dan Da Dan (2025)"
        assert "Dan Da Dan Season 2" in show_doc.title_alts
        assert "ダンダダン (2025)" in show_doc.title_alts
        assert show_doc.episode_count_normal == 12
        assert show_doc.begin_year == 2025
        assert show_doc.end_year == 2025
        assert show_doc.rating > 0  # Should have rating
        assert show_doc.vote_count > 0
        assert len(show_doc.tags) > 0

    def test_parse_evangelion(self) -> None:
        """Test parsing Evangelion XML (resources/22.xml)."""
        # Arrange
        xml_file = Path("resources/22.xml")
        xml_data = xml_file.read_text(encoding="utf-8")

        # Act
        show_doc = parse_anidb_xml(xml_data)

        # Assert
        assert show_doc.anime_id == "22"
        assert show_doc.anidb_anime_id == 22
        assert show_doc.title_main == "Shinseiki Evangelion"
        assert "Neon Genesis Evangelion" in show_doc.title_alts
        assert show_doc.episode_count_normal == 26
        assert show_doc.begin_year == 1995
        assert show_doc.end_year == 1996
        assert show_doc.rating > 0
        assert len(show_doc.tags) > 0

    def test_parse_kaiju_no_8(self) -> None:
        """Test parsing Kaiju No. 8 XML (resources/17550.xml)."""
        # Arrange
        xml_file = Path("resources/17550.xml")
        xml_data = xml_file.read_text(encoding="utf-8")

        # Act
        show_doc = parse_anidb_xml(xml_data)

        # Assert
        assert show_doc.anime_id == "17550"
        assert show_doc.anidb_anime_id == 17550
        assert show_doc.title_main == "Kaijuu 8 Gou"
        assert "Kaiju No. 8" in show_doc.title_alts
        assert show_doc.episode_count_normal == 12
        assert show_doc.begin_year == 2024
        assert show_doc.end_year == 2024

    def test_parse_extracts_description(self) -> None:
        """Test that description is extracted correctly."""
        # Arrange
        xml_file = Path("resources/19060.xml")
        xml_data = xml_file.read_text(encoding="utf-8")

        # Act
        show_doc = parse_anidb_xml(xml_data)

        # Assert
        assert show_doc.description
        assert "paranormal mystery battle" in show_doc.description.lower()

    def test_parse_extracts_dates(self) -> None:
        """Test that dates are extracted and parsed correctly."""
        # Arrange
        xml_file = Path("resources/19060.xml")
        xml_data = xml_file.read_text(encoding="utf-8")

        # Act
        show_doc = parse_anidb_xml(xml_data)

        # Assert
        assert show_doc.air_date is not None
        assert show_doc.end_date is not None
        assert show_doc.air_date.year == 2025
        assert show_doc.air_date.month == 7
        assert show_doc.air_date.day == 4

    def test_parse_extracts_ratings(self) -> None:
        """Test that ratings are extracted and converted correctly."""
        # Arrange
        xml_file = Path("resources/19060.xml")
        xml_data = xml_file.read_text(encoding="utf-8")

        # Act
        show_doc = parse_anidb_xml(xml_data)

        # Assert
        # Rating should be converted from 0-10 scale to 0-1000 scale
        assert show_doc.rating > 0
        assert show_doc.rating <= 1000
        assert show_doc.vote_count > 0

    def test_parse_extracts_tags(self) -> None:
        """Test that tags are extracted correctly."""
        # Arrange
        xml_file = Path("resources/22.xml")
        xml_data = xml_file.read_text(encoding="utf-8")

        # Act
        show_doc = parse_anidb_xml(xml_data)

        # Assert
        assert len(show_doc.tags) > 0
        # Evangelion should have tags like "military", "robot", etc.
        tag_names = [tag.lower() for tag in show_doc.tags]
        assert any("military" in tag or "robot" in tag for tag in tag_names)

    def test_parse_extracts_external_ids(self) -> None:
        """Test that external IDs are extracted correctly."""
        # Arrange
        xml_file = Path("resources/22.xml")
        xml_data = xml_file.read_text(encoding="utf-8")

        # Act
        show_doc = parse_anidb_xml(xml_data)

        # Assert
        # Evangelion should have ANN ID
        assert show_doc.ann_id is not None
        assert show_doc.ann_id > 0

    def test_parse_extracts_relations(self) -> None:
        """Test that related anime are extracted correctly."""
        # Arrange
        xml_file = Path("resources/19060.xml")
        xml_data = xml_file.read_text(encoding="utf-8")

        # Act
        show_doc = parse_anidb_xml(xml_data)

        # Assert
        import json

        relations = json.loads(show_doc.relations)
        assert len(relations) > 0
        # Should have prequel and sequel
        assert any(r["type"] == "Prequel" for r in relations)

    def test_parse_extracts_similar(self) -> None:
        """Test that similar anime are extracted correctly."""
        # Arrange
        xml_file = Path("resources/22.xml")
        xml_data = xml_file.read_text(encoding="utf-8")

        # Act
        show_doc = parse_anidb_xml(xml_data)

        # Assert
        import json

        similar = json.loads(show_doc.similar)
        assert len(similar) > 0
        # Each similar anime should have id, approval, total
        assert all("id" in s for s in similar)

    def test_parse_handles_missing_optional_fields(self) -> None:
        """Test that parser handles missing optional fields gracefully."""
        # Arrange
        minimal_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <anime id="99999">
            <titles>
                <title type="main">Minimal Anime</title>
            </titles>
        </anime>"""

        # Act
        show_doc = parse_anidb_xml(minimal_xml)

        # Assert
        assert show_doc.anime_id == "99999"
        assert show_doc.title_main == "Minimal Anime"
        assert show_doc.description == ""
        assert show_doc.tags == []
        assert show_doc.episode_count_normal == 0
        assert show_doc.air_date is None
        assert show_doc.rating == 0
        assert show_doc.ann_id is None

    def test_parse_raises_on_malformed_xml(self) -> None:
        """Test that parser raises ValueError on malformed XML."""
        # Arrange
        bad_xml = "{ this is not xml }"

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid XML"):
            parse_anidb_xml(bad_xml)

    def test_parse_raises_on_missing_anime_id(self) -> None:
        """Test that parser raises ValueError when anime ID is missing."""
        # Arrange
        xml_without_id = """<?xml version="1.0" encoding="UTF-8"?>
        <anime>
            <titles>
                <title type="main">Test</title>
            </titles>
        </anime>"""

        # Act & Assert
        with pytest.raises(ValueError, match="Missing anime ID"):
            parse_anidb_xml(xml_without_id)

    def test_parse_raises_on_missing_main_title(self) -> None:
        """Test that parser raises ValueError when main title is missing."""
        # Arrange
        xml_without_title = """<?xml version="1.0" encoding="UTF-8"?>
        <anime id="12345">
            <titles>
                <title type="synonym">Alt Title</title>
            </titles>
        </anime>"""

        # Act & Assert
        with pytest.raises(ValueError, match="Missing main title"):
            parse_anidb_xml(xml_without_title)

    def test_parse_handles_invalid_rating(self) -> None:
        """Test that parser handles invalid rating values gracefully."""
        # Arrange
        xml_with_bad_rating = """<?xml version="1.0" encoding="UTF-8"?>
        <anime id="12345">
            <titles>
                <title type="main">Test</title>
            </titles>
            <ratings>
                <permanent count="100">invalid</permanent>
            </ratings>
        </anime>"""

        # Act
        show_doc = parse_anidb_xml(xml_with_bad_rating)

        # Assert
        assert show_doc.rating == 0  # Should default to 0


class TestParseDateHelper:
    """Tests for _parse_date helper function."""

    def test_parse_date_valid(self) -> None:
        """Test parsing valid date string."""
        # Act
        result = _parse_date("2020-01-15")

        # Assert
        assert result is not None
        assert result.year == 2020
        assert result.month == 1
        assert result.day == 15

    def test_parse_date_invalid(self) -> None:
        """Test parsing invalid date string returns None."""
        # Act & Assert
        assert _parse_date("invalid-date") is None
        assert _parse_date("2020-13-01") is None  # Invalid month
        assert _parse_date("not a date") is None

    def test_parse_date_none(self) -> None:
        """Test parsing None returns None."""
        # Act
        result = _parse_date(None)

        # Assert
        assert result is None

    def test_parse_date_empty_string(self) -> None:
        """Test parsing empty string returns None."""
        # Act
        result = _parse_date("")

        # Assert
        assert result is None
