"""config module for KCPC.

Loads environment variables and provides configuration values.
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv

# Load .env file from project root
load_dotenv()


@dataclass(frozen=True)
class Config:
    """Configuration for KCPC application."""

    # DuckDuckGo request settings
    ddg_min_delay: float
    ddg_max_delay: float
    ddg_max_retries: int
    ddg_timeout: int
    ddg_user_agent: str
    ddg_max_results: int

    # Bypass options (user explicit settings only)
    ddg_use_proxy: bool
    ddg_proxy_list: str
    ddg_rotate_ua: bool
    ddg_ua_list: str
    ddg_ignore_delay: bool
    ddg_ignore_ssl: bool

    # Database and output paths
    db_file_path: str
    log_file_path: str
    output_file_path: str
    output_format: Literal["xlsx", "csv"]

    @classmethod
    def from_env(cls) -> "Config":
        """Create Config from environment variables.

        Returns:
            Config: Configuration instance with default values for missing keys.
        """
        # Helper to parse boolean from string
        def parse_bool(value: str | None, default: bool = False) -> bool:
            if value is None:
                return default
            return value.strip().lower() in ("true", "1", "yes", "on")

        # DuckDuckGo settings
        ddg_min_delay = float(os.getenv("DDG_MIN_DELAY", "2.0"))
        ddg_max_delay = float(os.getenv("DDG_MAX_DELAY", "3.5"))
        ddg_max_retries = int(os.getenv("DDG_MAX_RETRIES", "3"))
        ddg_timeout = int(os.getenv("DDG_TIMEOUT", "10"))
        ddg_user_agent = os.getenv(
            "DDG_USER_AGENT",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        )
        ddg_max_results = int(os.getenv("DDG_MAX_RESULTS", "10"))

        # Bypass options
        ddg_use_proxy = parse_bool(os.getenv("DDG_USE_PROXY"), False)
        ddg_proxy_list = os.getenv("DDG_PROXY_LIST", "./proxies.txt")
        ddg_rotate_ua = parse_bool(os.getenv("DDG_ROTATE_UA"), False)
        ddg_ua_list = os.getenv("DDG_UA_LIST", "./user_agents.txt")
        ddg_ignore_delay = parse_bool(os.getenv("DDG_IGNORE_DELAY"), False)
        ddg_ignore_ssl = parse_bool(os.getenv("DDG_IGNORE_SSL"), False)

        # Paths
        db_file_path = os.getenv("DB_FILE_PATH", "./data/kcpc_database.db")
        log_file_path = os.getenv("LOG_FILE_PATH", "./logs/kcpc.log")
        output_file_path = os.getenv("OUTPUT_FILE_PATH", "./output/kcpc_result.xlsx")
        output_format_raw = os.getenv("OUTPUT_FORMAT", "xlsx")
        output_format: Literal["xlsx", "csv"] = (
            "xlsx" if output_format_raw in ("xlsx", "XLSX") else "csv"
        )

        return cls(
            ddg_min_delay=ddg_min_delay,
            ddg_max_delay=ddg_max_delay,
            ddg_max_retries=ddg_max_retries,
            ddg_timeout=ddg_timeout,
            ddg_user_agent=ddg_user_agent,
            ddg_max_results=ddg_max_results,
            ddg_use_proxy=ddg_use_proxy,
            ddg_proxy_list=ddg_proxy_list,
            ddg_rotate_ua=ddg_rotate_ua,
            ddg_ua_list=ddg_ua_list,
            ddg_ignore_delay=ddg_ignore_delay,
            ddg_ignore_ssl=ddg_ignore_ssl,
            db_file_path=db_file_path,
            log_file_path=log_file_path,
            output_file_path=output_file_path,
            output_format=output_format,
        )

    def ensure_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        Path(self.db_file_path).parent.mkdir(parents=True, exist_ok=True)
        Path(self.log_file_path).parent.mkdir(parents=True, exist_ok=True)
        Path(self.output_file_path).parent.mkdir(parents=True, exist_ok=True)


# Global config instance
_config: Config | None = None


def get_config() -> Config:
    """Get global configuration instance.

    Returns:
        Config: Global configuration instance.
    """
    global _config
    if _config is None:
        _config = Config.from_env()
        _config.ensure_directories()
    return _config


def reset_config() -> None:
    """Reset global configuration instance (for testing)."""
    global _config
    _config = None
