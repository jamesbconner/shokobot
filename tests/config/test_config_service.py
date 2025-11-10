import json
from pathlib import Path
from typing import Any

import pytest

from services.config_service import ConfigService


def test_env_overrides(tmp_path: Path, monkeypatch: Any) -> None:
    cfgfile = tmp_path / "config.json"
    cfgfile.write_text(
        '{"chroma":{"persist_directory":"./.chroma"},"openai":{"model":"x"}}', encoding="utf-8"
    )
    monkeypatch.setenv("CHROMA_PERSIST_DIRECTORY", "/tmp/chroma")
    monkeypatch.setenv("OPENAI_MODEL", "unit-model")

    cfg = ConfigService(str(cfgfile))
    assert cfg.get("chroma.persist_directory") == "/tmp/chroma"
    assert cfg.get("openai.model") == "unit-model"


def test_config_missing_file() -> None:
    """Test that missing config file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError, match="Config file not found"):
        ConfigService("/nonexistent/config.json")


def test_config_malformed_json(tmp_path: Path) -> None:
    """Test that malformed JSON raises JSONDecodeError."""
    cfgfile = tmp_path / "bad.json"
    cfgfile.write_text("{ invalid json }", encoding="utf-8")

    with pytest.raises(json.JSONDecodeError):
        ConfigService(str(cfgfile))


def test_config_as_dict(tmp_path: Path) -> None:
    """Test as_dict returns configuration dictionary."""
    cfgfile = tmp_path / "config.json"
    cfgfile.write_text('{"test":{"key":"value"}}', encoding="utf-8")

    cfg = ConfigService(str(cfgfile))
    result = cfg.as_dict()

    assert result == {"test": {"key": "value"}}
    assert isinstance(result, dict)
    assert "test" in result


def test_config_get_with_default(tmp_path: Path) -> None:
    """Test get method with default values."""
    cfgfile = tmp_path / "config.json"
    cfgfile.write_text('{"test":{"key":"value"}}', encoding="utf-8")

    cfg = ConfigService(str(cfgfile))

    # Test missing key returns None
    assert cfg.get("nonexistent") is None

    # Test missing key with default
    assert cfg.get("nonexistent", "default") == "default"

    # Test nested missing key with default
    assert cfg.get("test.missing", 42) == 42


def test_config_get_nested_paths(tmp_path: Path) -> None:
    """Test get method with various nested paths."""
    cfgfile = tmp_path / "config.json"
    cfgfile.write_text(
        '{"level1":{"level2":{"level3":"deep"},"value":"mid"},"top":"surface"}', encoding="utf-8"
    )

    cfg = ConfigService(str(cfgfile))

    # Test top-level access
    assert cfg.get("top") == "surface"

    # Test nested access
    assert cfg.get("level1.value") == "mid"
    assert cfg.get("level1.level2.level3") == "deep"

    # Test getting dict value
    level2 = cfg.get("level1.level2")
    assert isinstance(level2, dict)
    assert level2["level3"] == "deep"


def test_config_get_path_through_non_dict(tmp_path: Path) -> None:
    """Test get method when trying to traverse through non-dict values."""
    cfgfile = tmp_path / "config.json"
    cfgfile.write_text('{"string":"value","number":42,"nested":{"value":"test"}}', encoding="utf-8")

    cfg = ConfigService(str(cfgfile))

    # Try to traverse through a string value
    assert cfg.get("string.nested") is None
    assert cfg.get("string.nested", "default") == "default"

    # Try to traverse through a number value
    assert cfg.get("number.nested") is None

    # Try to access non-existent key in nested dict
    assert cfg.get("nested.missing") is None


def test_config_all_env_overrides(tmp_path: Path, monkeypatch: Any) -> None:
    """Test all supported environment variable overrides."""
    cfgfile = tmp_path / "config.json"
    cfgfile.write_text(
        '{"openai":{"model":"default","api_key":"default"},"chroma":{"persist_directory":"default"}}',
        encoding="utf-8",
    )

    # Set all environment overrides
    monkeypatch.setenv("OPENAI_MODEL", "env-model")
    monkeypatch.setenv("OPENAI_API_KEY", "env-key")
    monkeypatch.setenv("CHROMA_PERSIST_DIRECTORY", "env-dir")

    cfg = ConfigService(str(cfgfile))

    # Verify all overrides work
    assert cfg.get("openai.model") == "env-model"
    assert cfg.get("openai.api_key") == "env-key"
    assert cfg.get("chroma.persist_directory") == "env-dir"
