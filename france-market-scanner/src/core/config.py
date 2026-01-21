"""Configuration management."""
from pathlib import Path
from typing import Any
import os
import yaml
from dotenv import load_dotenv


def load_config(config_path: str | Path = None) -> dict[str, Any]:
    """Load configuration from YAML file and environment variables.

    Args:
        config_path: Path to config file. Defaults to config/config.yaml.

    Returns:
        Configuration dictionary.
    """
    # Load .env file if present
    load_dotenv()

    # Determine config path
    if config_path is None:
        # Try to find config relative to project root
        current = Path(__file__).parent.parent.parent
        config_path = current / "config" / "config.yaml"

    config_path = Path(config_path)

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    # Load YAML config
    with open(config_path) as f:
        config = yaml.safe_load(f)

    # Override with environment variables
    config = _apply_env_overrides(config)

    return config


def _apply_env_overrides(config: dict) -> dict:
    """Apply environment variable overrides to config."""
    # Database path
    if db_path := os.getenv("DATABASE_PATH"):
        config["database"]["path"] = db_path

    # Log level
    if log_level := os.getenv("LOG_LEVEL"):
        config["logging"]["level"] = log_level

    # INPI credentials
    if not config.get("inpi"):
        config["inpi"] = {}
    if username := os.getenv("INPI_USERNAME"):
        config["inpi"]["username"] = username
    if password := os.getenv("INPI_PASSWORD"):
        config["inpi"]["password"] = password

    # BODACC FTPS credentials
    if not config.get("bodacc"):
        config["bodacc"] = {}
    if username := os.getenv("BODACC_FTPS_USERNAME"):
        config["bodacc"]["ftps_username"] = username
    if password := os.getenv("BODACC_FTPS_PASSWORD"):
        config["bodacc"]["ftps_password"] = password

    return config


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent.parent
