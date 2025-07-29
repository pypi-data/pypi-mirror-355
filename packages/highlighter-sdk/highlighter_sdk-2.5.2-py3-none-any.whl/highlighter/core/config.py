import os
import sys
import tomllib
from pathlib import Path
from typing import Any, Dict, Optional, Union

import tomli_w
from pydantic import BaseModel, Field, ValidationError

from highlighter.cli import get_default_logger

logger = get_default_logger(__name__)


class HighlighterRuntimeConfigError(Exception):
    """Raised when there’s a problem loading or validating the Highlighter Runtime config file."""

    pass


class HighlighterRuntimeConfig(BaseModel):

    class AgentConfig(BaseModel):
        queue_response_max_size: int = Field(
            default=100,
            ge=0,
            description="Maximum size of an agent's response queue. The larger the queue, the more memory consumed. Defaults to 100.",
        )
        timeout_secs: float = Field(
            default=60.0,
            ge=0.0,
            description="Timeout in seconds when the agent is processing data. Defaults to 60s. For example, when the timeout is 30s, if there is no output from the agent after 30s, a timeout error is raised.",
        )
        task_lease_duration_secs: float = Field(
            default=60.0,
            ge=0.0,
            description="Duration in seconds to lease a task for processing by an agent. Default is 60s.",
        )
        task_polling_period_secs: float = Field(
            default=5.0,
            ge=0.0,
            description="Period in seconds to poll a task for processing by an agent. Default is to poll every 5s.",
        )

    agent: AgentConfig = Field(default_factory=AgentConfig)

    # Do we always want Path or str or should we accept both
    local_cache_directory: str = Field(
        default=str(Path.home() / ".highlighter-cache"),
        description="Local cache directory used by agents and SDK. Defaults to $HOME/.highlighter-cache.",
    )
    download_timeout_secs: float = Field(
        default=300.0, ge=0.0, description="Timeout in seconds when downloading data. Defaults to 300s."
    )
    log_path: str = Field(
        default=str(Path.home() / ".highlighter" / "log" / "development.log"),
        description="Path to log file used by agents and SDK. Defaults to $HOME/.highlighter/log/development.log",
    )
    log_level: str = Field(
        default="WARNING",
        description="Log level used by agents and SDK. Set to one of python log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL. Defaults to WARNING.",
    )

    @classmethod
    def load(cls, config_path: Optional[str] = None) -> "HighlighterRuntimeConfig":
        """
        Load configuration from the specified path or the default path.

        If the configuration file doesn't exist:
        - If using the default path, create it with default values
        - If using a custom path, notify the user and exit

        Args:
            config_path: Path to the configuration file or None to use the default

        Returns:
            HighlighterRuntimeConfig: The loaded configuration
        """
        default_path = Path("~/.highlighter/config").expanduser()

        if config_path is None:
            path = default_path
        else:
            path = Path(config_path).expanduser()

        raw_config = parse_toml_file(path)

        if raw_config is None:
            if path == default_path:
                default_config = cls()
                write_default_config(path, default_config)
                return default_config
            else:
                raise HighlighterRuntimeConfigError(
                    f"Config file not found at {path}. Use --config to specify a valid configuration file or run without --config to use defaults."
                )
        try:
            cfg = cls(**raw_config)
            cfg.override_with_env_vars()
            return cfg

        except ValidationError as e:
            logger.error(f"Validation error in configuration file '{path}'")
            raise HighlighterRuntimeConfigError(f"Invalid configuration: {e}")

    def override_with_env_vars(self) -> None:
        """
        Override configuration values if corresponding environment variables are set.

        Supported environment variables:
        - HL_AGENT_QUEUE_RESPONSE_MAX_SIZE (int)
        - HL_CACHE_DIR (str)
        - HL_DOWNLOAD_TIMEOUT (int)
        - HL_LOG_LEVEL (str)
        """
        # Agent queue size
        val = os.getenv("HL_AGENT_QUEUE_RESPONSE_MAX_SIZE")
        if val is not None:
            try:
                self.agent.queue_response_max_size = int(val)
            except ValueError:
                raise ValueError(f"HL_AGENT_QUEUE_RESPONSE_MAX_SIZE must be an integer, got '{val}'")

        # Local cache directory
        val = os.getenv("HL_CACHE_DIR")
        if val:
            self.local_cache_directory = val

        # Download timeout seconds
        val = os.getenv("HL_DOWNLOAD_TIMEOUT")
        if val is not None:
            try:
                self.download_timeout_secs = float(val)
            except ValueError:
                raise ValueError(f"HL_DOWNLOAD_TIMEOUT must be a float, got '{val}'")

        # Log level
        val = os.getenv("HL_LOG_LEVEL")
        if val is not None:
            try:
                self.log_level = int(val)
            except ValueError:
                raise ValueError(f"HL_LOG_LEVEL must be an int, got '{val}'")

    def save(self, config_path: Optional[str] = None) -> None:
        """
        Save the current configuration to the specified path, or to the default path ~~/.highlighter/config if none provided.
        """
        default_path = Path("~/.highlighter/config").expanduser()
        path = Path(config_path).expanduser() if config_path else default_path
        write_default_config(path, self)


def ensure_directory_exists(path: Union[str, Path]) -> None:
    """Ensure the directory for the given file path exists."""
    directory = Path(path).parent
    try:
        directory.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        raise PermissionError(f"No permission to create directory: {directory}")
    except Exception as e:
        raise Exception(f"Could not create directory {directory}: {e}")


def write_default_config(config_path: Union[str, Path], config: BaseModel) -> None:
    """Write a default configuration to the specified path."""
    config_path = Path(config_path)
    ensure_directory_exists(config_path)

    try:
        with open(config_path, "wb") as f:
            config_dict = (
                config.model_dump()
            )  # Using model_dump() instead of dict() for Pydantic v2 compatibility
            f.write(tomli_w.dumps(config_dict).encode("utf-8"))
        logger.info(f"Created default configuration at: {config_path}")
    except PermissionError:
        logger.warning(f"No permission to write default configuration: {config_path}")
        # Still return the default config even if we can't write it
    except Exception as e:
        logger.warning(f"Unable to write default configuration: {config_path}: {e}")
        # Still return the default config even if we can't write it


def parse_toml_file(file_path: Union[str, Path]) -> Optional[Dict[str, Any]]:
    """Parse a TOML file and return its contents as a dictionary."""
    try:
        with open(file_path, "rb") as f:
            return tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
        raise tomllib.TOMLDecodeError(f"Error parsing TOML in configuration file {file_path}:")
    except FileNotFoundError:
        return None
    except PermissionError:
        raise PermissionError(f"No permission to read configuration: {file_path}")
    except Exception as e:
        raise Exception(f"Error reading configuration {file_path}: {e}")
