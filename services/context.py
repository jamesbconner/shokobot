"""Application context for dependency injection."""

from dataclasses import dataclass

from services.config_service import ConfigService


@dataclass
class AppContext:
    """Application context containing shared configuration and services.

    Attributes:
        config: Configuration service instance.
    """

    config: ConfigService

    @classmethod
    def create(cls, config_path: str = "resources/config.json") -> "AppContext":
        """Create application context with configuration.

        Args:
            config_path: Path to configuration file.

        Returns:
            Initialized AppContext instance.

        Raises:
            FileNotFoundError: If config file doesn't exist.
            json.JSONDecodeError: If config file is malformed.
        """
        config = ConfigService(config_path)
        return cls(config=config)
