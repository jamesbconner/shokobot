import json
import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Allowed values for GPT-5 Responses API parameters
_ALLOWED_REASONING = {"low", "medium", "high"}
_ALLOWED_VERBOSITY = {"low", "medium", "high"}
_MIN_OUTPUT_TOKENS = 512
_MAX_OUTPUT_TOKENS = 16384


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

    def get_reasoning_effort(self) -> str:
        """Get validated reasoning effort setting for GPT-5 Responses API.

        Returns:
            Reasoning effort level: "low", "medium", or "high".

        Raises:
            ValueError: If configured value is not in allowed set.

        Examples:
            >>> config.get_reasoning_effort()
            'medium'
        """
        value = str(self.get("openai.reasoning_effort", "medium"))
        if value not in _ALLOWED_REASONING:
            raise ValueError(
                f"Invalid reasoning_effort '{value}'. "
                f"Must be one of: {', '.join(sorted(_ALLOWED_REASONING))}"
            )
        return value

    def get_output_verbosity(self) -> str:
        """Get validated output verbosity setting for GPT-5 Responses API.

        Returns:
            Output verbosity level: "low", "medium", or "high".

        Raises:
            ValueError: If configured value is not in allowed set.

        Examples:
            >>> config.get_output_verbosity()
            'medium'
        """
        value = str(self.get("openai.output_verbosity", "medium"))
        if value not in _ALLOWED_VERBOSITY:
            raise ValueError(
                f"Invalid output_verbosity '{value}'. "
                f"Must be one of: {', '.join(sorted(_ALLOWED_VERBOSITY))}"
            )
        return value

    def get_max_output_tokens(self) -> int:
        """Get validated max output tokens setting for GPT-5 Responses API.

        Returns:
            Maximum output tokens (between 512 and 16384).

        Raises:
            ValueError: If configured value is not in valid range or not an integer.

        Examples:
            >>> config.get_max_output_tokens()
            8192
        """
        value = self.get("openai.max_output_tokens", 4096)

        # Ensure value is an integer
        try:
            value = int(value)
        except (TypeError, ValueError) as e:
            raise ValueError(f"Invalid max_output_tokens '{value}'. Must be an integer.") from e

        # Validate range
        if not _MIN_OUTPUT_TOKENS <= value <= _MAX_OUTPUT_TOKENS:
            raise ValueError(
                f"Invalid max_output_tokens {value}. "
                f"Must be between {_MIN_OUTPUT_TOKENS} and {_MAX_OUTPUT_TOKENS}."
            )

        return int(value)

    def get_mcp_enabled(self) -> bool:
        """Get MCP integration enabled status.

        Returns:
            True if MCP integration is enabled, False otherwise.

        Examples:
            >>> config.get_mcp_enabled()
            True
        """
        return bool(self.get("mcp.enabled", False))

    def get_mcp_servers(self) -> dict[str, dict[str, Any]]:
        """Get all configured MCP servers.

        Returns:
            Dictionary of server configurations keyed by server name.

        Examples:
            >>> config.get_mcp_servers()
            {'anime': {'command': '/path/to/python', 'args': [...]}}
        """
        servers = self.get("mcp.servers", {})
        return dict(servers) if isinstance(servers, dict) else {}

    def get_mcp_server_config(self, server_name: str) -> dict[str, Any]:
        """Get configuration for a specific MCP server.

        Args:
            server_name: Name of the MCP server (e.g., "anime").

        Returns:
            Server configuration dictionary.

        Raises:
            ValueError: If server is not configured.

        Examples:
            >>> config.get_mcp_server_config("anime")
            {'command': '/path/to/python', 'args': [...]}
        """
        servers = self.get_mcp_servers()
        if server_name not in servers:
            raise ValueError(
                f"MCP server '{server_name}' not configured. "
                f"Available servers: {', '.join(servers.keys()) or 'none'}"
            )
        return servers[server_name]

    def get_mcp_cache_dir(self) -> str:
        """Get MCP cache directory path for persisted ShowDocs.

        Returns:
            Path to MCP cache directory.

        Examples:
            >>> config.get_mcp_cache_dir()
            'data/mcp_cache'
        """
        return str(self.get("mcp.cache_dir", "data/mcp_cache"))

    def get_mcp_fallback_count_threshold(self) -> int:
        """Get minimum result count before MCP fallback.

        Returns:
            Minimum number of results required to skip MCP fallback.

        Examples:
            >>> config.get_mcp_fallback_count_threshold()
            3
        """
        return int(self.get("mcp.fallback_count_threshold", 3))

    def get_mcp_fallback_score_threshold(self) -> float:
        """Get maximum distance score before MCP fallback.

        Returns:
            Maximum distance score (0.0-2.0) to skip MCP fallback.
            Lower scores = better matches. If best result has distance <= threshold,
            MCP fallback is skipped.

        Examples:
            >>> config.get_mcp_fallback_score_threshold()
            0.7

        Notes:
            With cosine distance (lower=better):
            - 0.0-0.3: Excellent match
            - 0.3-0.6: Very good match
            - 0.6-0.9: Good match
            - Default 0.7 means: skip MCP if best match is "good" or better
        """
        return float(self.get("mcp.fallback_score_threshold", 0.7))

    def get_mcp_timeout(self) -> int:
        """Get MCP server timeout in seconds.

        Returns:
            Timeout in seconds for MCP server operations.

        Examples:
            >>> config.get_mcp_timeout()
            30
        """
        return int(self.get("mcp.timeout", 30))
