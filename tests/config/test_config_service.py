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


# GPT-5 Responses API Configuration Tests


def test_get_reasoning_effort_default(tmp_path: Path) -> None:
    """Test get_reasoning_effort returns default value."""
    cfgfile = tmp_path / "config.json"
    cfgfile.write_text('{"openai":{}}', encoding="utf-8")

    cfg = ConfigService(str(cfgfile))
    assert cfg.get_reasoning_effort() == "medium"


def test_get_reasoning_effort_valid_values(tmp_path: Path) -> None:
    """Test get_reasoning_effort with all valid values."""
    for value in ["low", "medium", "high"]:
        cfgfile = tmp_path / "config.json"
        cfgfile.write_text(f'{{"openai":{{"reasoning_effort":"{value}"}}}}', encoding="utf-8")

        cfg = ConfigService(str(cfgfile))
        assert cfg.get_reasoning_effort() == value


def test_get_reasoning_effort_invalid_value(tmp_path: Path) -> None:
    """Test get_reasoning_effort raises ValueError for invalid value."""
    cfgfile = tmp_path / "config.json"
    cfgfile.write_text('{"openai":{"reasoning_effort":"invalid"}}', encoding="utf-8")

    cfg = ConfigService(str(cfgfile))
    with pytest.raises(ValueError, match="Invalid reasoning_effort"):
        cfg.get_reasoning_effort()


def test_get_output_verbosity_default(tmp_path: Path) -> None:
    """Test get_output_verbosity returns default value."""
    cfgfile = tmp_path / "config.json"
    cfgfile.write_text('{"openai":{}}', encoding="utf-8")

    cfg = ConfigService(str(cfgfile))
    assert cfg.get_output_verbosity() == "medium"


def test_get_output_verbosity_valid_values(tmp_path: Path) -> None:
    """Test get_output_verbosity with all valid values."""
    for value in ["low", "medium", "high"]:
        cfgfile = tmp_path / "config.json"
        cfgfile.write_text(f'{{"openai":{{"output_verbosity":"{value}"}}}}', encoding="utf-8")

        cfg = ConfigService(str(cfgfile))
        assert cfg.get_output_verbosity() == value


def test_get_output_verbosity_invalid_value(tmp_path: Path) -> None:
    """Test get_output_verbosity raises ValueError for invalid value."""
    cfgfile = tmp_path / "config.json"
    cfgfile.write_text('{"openai":{"output_verbosity":"invalid"}}', encoding="utf-8")

    cfg = ConfigService(str(cfgfile))
    with pytest.raises(ValueError, match="Invalid output_verbosity"):
        cfg.get_output_verbosity()


def test_get_max_output_tokens_default(tmp_path: Path) -> None:
    """Test get_max_output_tokens returns default value."""
    cfgfile = tmp_path / "config.json"
    cfgfile.write_text('{"openai":{}}', encoding="utf-8")

    cfg = ConfigService(str(cfgfile))
    assert cfg.get_max_output_tokens() == 4096


def test_get_max_output_tokens_valid_values(tmp_path: Path) -> None:
    """Test get_max_output_tokens with valid range."""
    for value in [512, 4096, 8192, 16384]:
        cfgfile = tmp_path / "config.json"
        cfgfile.write_text(f'{{"openai":{{"max_output_tokens":{value}}}}}', encoding="utf-8")

        cfg = ConfigService(str(cfgfile))
        assert cfg.get_max_output_tokens() == value


def test_get_max_output_tokens_below_minimum(tmp_path: Path) -> None:
    """Test get_max_output_tokens raises ValueError for value below minimum."""
    cfgfile = tmp_path / "config.json"
    cfgfile.write_text('{"openai":{"max_output_tokens":256}}', encoding="utf-8")

    cfg = ConfigService(str(cfgfile))
    with pytest.raises(ValueError, match="Must be between 512 and 16384"):
        cfg.get_max_output_tokens()


def test_get_max_output_tokens_above_maximum(tmp_path: Path) -> None:
    """Test get_max_output_tokens raises ValueError for value above maximum."""
    cfgfile = tmp_path / "config.json"
    cfgfile.write_text('{"openai":{"max_output_tokens":20000}}', encoding="utf-8")

    cfg = ConfigService(str(cfgfile))
    with pytest.raises(ValueError, match="Must be between 512 and 16384"):
        cfg.get_max_output_tokens()


def test_get_max_output_tokens_invalid_type(tmp_path: Path) -> None:
    """Test get_max_output_tokens raises ValueError for non-integer value."""
    cfgfile = tmp_path / "config.json"
    cfgfile.write_text('{"openai":{"max_output_tokens":"not_a_number"}}', encoding="utf-8")

    cfg = ConfigService(str(cfgfile))
    with pytest.raises(ValueError, match="Must be an integer"):
        cfg.get_max_output_tokens()


# MCP Configuration Tests


def test_get_mcp_enabled_default(tmp_path: Path) -> None:
    """Test get_mcp_enabled returns False by default."""
    cfgfile = tmp_path / "config.json"
    cfgfile.write_text("{}", encoding="utf-8")

    cfg = ConfigService(str(cfgfile))
    assert cfg.get_mcp_enabled() is False


def test_get_mcp_enabled_true(tmp_path: Path) -> None:
    """Test get_mcp_enabled returns True when configured."""
    cfgfile = tmp_path / "config.json"
    cfgfile.write_text('{"mcp":{"enabled":true}}', encoding="utf-8")

    cfg = ConfigService(str(cfgfile))
    assert cfg.get_mcp_enabled() is True


def test_get_mcp_enabled_false(tmp_path: Path) -> None:
    """Test get_mcp_enabled returns False when explicitly disabled."""
    cfgfile = tmp_path / "config.json"
    cfgfile.write_text('{"mcp":{"enabled":false}}', encoding="utf-8")

    cfg = ConfigService(str(cfgfile))
    assert cfg.get_mcp_enabled() is False


def test_get_mcp_servers_default(tmp_path: Path) -> None:
    """Test get_mcp_servers returns empty dict by default."""
    cfgfile = tmp_path / "config.json"
    cfgfile.write_text("{}", encoding="utf-8")

    cfg = ConfigService(str(cfgfile))
    assert cfg.get_mcp_servers() == {}


def test_get_mcp_servers_with_config(tmp_path: Path) -> None:
    """Test get_mcp_servers returns configured servers."""
    cfgfile = tmp_path / "config.json"
    cfgfile.write_text(
        '{"mcp":{"servers":{"anime":{"command":"python","args":["-m","server"]},"other":{"command":"node"}}}}',
        encoding="utf-8",
    )

    cfg = ConfigService(str(cfgfile))
    servers = cfg.get_mcp_servers()

    assert "anime" in servers
    assert "other" in servers
    assert servers["anime"]["command"] == "python"
    assert servers["anime"]["args"] == ["-m", "server"]


def test_get_mcp_server_config_valid(tmp_path: Path) -> None:
    """Test get_mcp_server_config returns specific server config."""
    cfgfile = tmp_path / "config.json"
    cfgfile.write_text(
        '{"mcp":{"servers":{"anime":{"command":"python","args":["-m","server"]}}}}',
        encoding="utf-8",
    )

    cfg = ConfigService(str(cfgfile))
    server_config = cfg.get_mcp_server_config("anime")

    assert server_config["command"] == "python"
    assert server_config["args"] == ["-m", "server"]


def test_get_mcp_server_config_missing(tmp_path: Path) -> None:
    """Test get_mcp_server_config raises ValueError for missing server."""
    cfgfile = tmp_path / "config.json"
    cfgfile.write_text('{"mcp":{"servers":{"anime":{}}}}', encoding="utf-8")

    cfg = ConfigService(str(cfgfile))
    with pytest.raises(ValueError, match="MCP server 'missing' not configured"):
        cfg.get_mcp_server_config("missing")


def test_get_mcp_cache_dir_default(tmp_path: Path) -> None:
    """Test get_mcp_cache_dir returns default value."""
    cfgfile = tmp_path / "config.json"
    cfgfile.write_text("{}", encoding="utf-8")

    cfg = ConfigService(str(cfgfile))
    assert cfg.get_mcp_cache_dir() == "data/mcp_cache"


def test_get_mcp_cache_dir_custom(tmp_path: Path) -> None:
    """Test get_mcp_cache_dir returns custom value."""
    cfgfile = tmp_path / "config.json"
    cfgfile.write_text('{"mcp":{"cache_dir":"/custom/path"}}', encoding="utf-8")

    cfg = ConfigService(str(cfgfile))
    assert cfg.get_mcp_cache_dir() == "/custom/path"


def test_get_mcp_fallback_count_threshold_default(tmp_path: Path) -> None:
    """Test get_mcp_fallback_count_threshold returns default value."""
    cfgfile = tmp_path / "config.json"
    cfgfile.write_text("{}", encoding="utf-8")

    cfg = ConfigService(str(cfgfile))
    assert cfg.get_mcp_fallback_count_threshold() == 3


def test_get_mcp_fallback_count_threshold_custom(tmp_path: Path) -> None:
    """Test get_mcp_fallback_count_threshold returns custom value."""
    cfgfile = tmp_path / "config.json"
    cfgfile.write_text('{"mcp":{"fallback_count_threshold":5}}', encoding="utf-8")

    cfg = ConfigService(str(cfgfile))
    assert cfg.get_mcp_fallback_count_threshold() == 5


def test_get_mcp_fallback_score_threshold_default(tmp_path: Path) -> None:
    """Test get_mcp_fallback_score_threshold returns default value."""
    cfgfile = tmp_path / "config.json"
    cfgfile.write_text("{}", encoding="utf-8")

    cfg = ConfigService(str(cfgfile))
    assert cfg.get_mcp_fallback_score_threshold() == 0.7


def test_get_mcp_fallback_score_threshold_custom(tmp_path: Path) -> None:
    """Test get_mcp_fallback_score_threshold returns custom value."""
    cfgfile = tmp_path / "config.json"
    cfgfile.write_text('{"mcp":{"fallback_score_threshold":0.85}}', encoding="utf-8")

    cfg = ConfigService(str(cfgfile))
    assert cfg.get_mcp_fallback_score_threshold() == 0.85


def test_get_mcp_timeout_default(tmp_path: Path) -> None:
    """Test get_mcp_timeout returns default value."""
    cfgfile = tmp_path / "config.json"
    cfgfile.write_text("{}", encoding="utf-8")

    cfg = ConfigService(str(cfgfile))
    assert cfg.get_mcp_timeout() == 30


def test_get_mcp_timeout_custom(tmp_path: Path) -> None:
    """Test get_mcp_timeout returns custom value."""
    cfgfile = tmp_path / "config.json"
    cfgfile.write_text('{"mcp":{"timeout":60}}', encoding="utf-8")

    cfg = ConfigService(str(cfgfile))
    assert cfg.get_mcp_timeout() == 60
