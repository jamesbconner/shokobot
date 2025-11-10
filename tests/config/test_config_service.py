from pathlib import Path
from typing import Any

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
