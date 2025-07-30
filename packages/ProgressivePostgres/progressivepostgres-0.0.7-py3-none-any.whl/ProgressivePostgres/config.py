# src/ZeitgleichClient/config.py

import os
from .logger import setup_logger

# Default config values
DEFAULT_DB_HOST = "localhost"
DEFAULT_DB_PORT = "5432"
DEFAULT_DB_NAME = "timescale"
DEFAULT_DB_USER = "postgres"
DEFAULT_DB_PASSWORD = None
DEFAULT_DB_AUTOCOMMIT = True

ALLOWED_LOG_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR"}
DEFAULT_LOG_LEVEL = "DEBUG"

DEFAULT_ORIGIN_SPLIT_CHAR = "/"
DEFAULT_ORIGIN_JOIN_CHAR = "/"
DEFAULT_TIMESTAMP_COLUMN = "timestamp"
DEFAULT_VALUE_COLUMN = "value"
DEFAULT_CREATE_TABLES_IF_NOT_EXIST = True

ALLOWED_EXTRA_COLUMNS_HANDLING = {"ignore", "error", "append"}
DEFAULT_EXTRA_COLUMNS_HANDLING = "append"

class Config:
    """
    Configuration class for a Timescale/Zeitgleich client.
    """
    def __init__(self, env_prefix: str = "TS"):
        self.env_prefix = env_prefix.upper()

        self.db_host = os.getenv(f"{self.env_prefix}_DB_HOST", DEFAULT_DB_HOST)
        self.db_port = os.getenv(f"{self.env_prefix}_DB_PORT", DEFAULT_DB_PORT)
        self.db_name = os.getenv(f"{self.env_prefix}_DB_NAME", DEFAULT_DB_NAME)
        self.db_user = os.getenv(f"{self.env_prefix}_DB_USER", DEFAULT_DB_USER)
        self.db_password = os.getenv(f"{self.env_prefix}_DB_PASS", DEFAULT_DB_PASSWORD)
        self.db_autocommit = str(os.getenv(f"{self.env_prefix}_DB_AUTOCOMMIT", DEFAULT_DB_AUTOCOMMIT)).lower() in ['true','1','yes']

        log_level = os.getenv(f"{self.env_prefix}_LOG_LEVEL", DEFAULT_LOG_LEVEL).upper()
        if log_level not in ALLOWED_LOG_LEVELS:
            raise ValueError(f"Invalid LOG_LEVEL '{log_level}', must be one of {ALLOWED_LOG_LEVELS}")
        self.log_level = log_level

        self.origin_split_char = os.getenv(f"{self.env_prefix}_ORIGIN_SPLIT_CHAR", DEFAULT_ORIGIN_SPLIT_CHAR)
        self.origin_join_char = os.getenv(f"{self.env_prefix}_ORIGIN_JOIN_CHAR", DEFAULT_ORIGIN_JOIN_CHAR)
        self.timestamp_column = os.getenv(f"{self.env_prefix}_TIMESTAMP_COLUMN", DEFAULT_TIMESTAMP_COLUMN)
        self.value_column = os.getenv(f"{self.env_prefix}_VALUE_COLUMN", DEFAULT_VALUE_COLUMN)
        self.create_tables_if_not_exist = str(os.getenv(f"{self.env_prefix}_CREATE_TABLES_IF_NOT_EXIST", DEFAULT_CREATE_TABLES_IF_NOT_EXIST)).lower() in ['true','1','yes']

        extra_handling = os.getenv(f"{self.env_prefix}_EXTRA_COLUMNS_HANDLING", DEFAULT_EXTRA_COLUMNS_HANDLING).lower()
        if extra_handling not in ALLOWED_EXTRA_COLUMNS_HANDLING:
            raise ValueError(f"Invalid EXTRA_COLUMNS_HANDLING '{extra_handling}', must be in {ALLOWED_EXTRA_COLUMNS_HANDLING}")
        self.extra_columns_handling = extra_handling

        from .logger import setup_logger
        self.logger = setup_logger("CONFIG_" + self.env_prefix, level=self.log_level)
        self.logger.debug(self)

    def __repr__(self):
        return (f"ProgressivePostgresConfig("
                f"db_host={self.db_host}, db_port={self.db_port}, db_name={self.db_name}, "
                f"db_user={self.db_user}, log_level={self.log_level}, "
                f"timestamp_column={self.timestamp_column}, value_column={self.value_column}, "
                f"extra_columns_handling={self.extra_columns_handling} )")
