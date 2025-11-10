import json
import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class ConfigService:
    """Service for loading and managing application configuration.

    Supports JSON-based configuration with environment variable overrides.
    Environment variables follow the pattern: SECTION_KEY (e.g., CHROMA_PERSIST_DIRECTORY).
    """

    def __init__(self, config_path: str = "resources/config.json") -> None:
        """Initialize configuration service.

        Args:
            config_path: Path to JSON configuration file.

        Raises:
            FileNotFoundError: If config file doesn't exist.
            json.JSONDecodeError: If config file is malformed.
        """
        self._config_path = Path(config_path)
        self._config: dict[str, Any] = {}
        self.load()

    def load(self) -> None:
        """Load configuration from file and apply environment overrides.

        Raises:
            FileNotFoundError: If config file doesn't exist.
            json.JSONDecodeError: If config file is malformed.
        """
        if not self._config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self._config_path}")

        try:
            with self._config_path.open(encoding="utf-8") as f:
                self._config = json.load(f)
            logger.info(f"Loaded configuration from {self._config_path}")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse config file {self._config_path}: {e}")
            raise

        self.apply_env_overrides()

    def apply_env_overrides(self) -> None:
        """Override config values with matching environment variables.

        Environment variables follow the pattern SECTION_KEY.
        Example: CHROMA_PERSIST_DIRECTORY overrides chroma.persist_directory
        """
        override_count = 0
        for section, values in self._config.items():
            if isinstance(values, dict):
                for key in values:
                    env_key = f"{section.upper()}_{key.upper()}"
                    if env_key in os.environ:
                        old_val = self._config[section][key]
                        self._config[section][key] = os.environ[env_key]
                        logger.debug(
                            f"Override {section}.{key}: {old_val} -> {os.environ[env_key]}"
                        )
                        override_count += 1

        if override_count > 0:
            logger.info(f"Applied {override_count} environment variable overrides")

    def get(self, path: str, default: Any = None) -> Any:
        """Access nested config using dot notation.

        Args:
            path: Dot-separated path to config value (e.g., 'chroma.persist_directory').
            default: Default value if path doesn't exist.

        Returns:
            Configuration value at the specified path, or default if not found.

        Examples:
            >>> config.get('chroma.persist_directory')
            './.chroma'
            >>> config.get('missing.key', 'fallback')
            'fallback'
        """
        parts = path.split(".")
        ref = self._config

        for part in parts:
            if not isinstance(ref, dict) or part not in ref:
                return default
            ref = ref[part]

        return ref

    def as_dict(self) -> dict[str, Any]:
        """Return complete configuration as dictionary.

        Returns:
            Dictionary containing all configuration values.
        """
        return self._config.copy()
