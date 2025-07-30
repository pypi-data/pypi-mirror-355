import logging
import reprlib
import sys
from logging import CRITICAL, DEBUG, ERROR, INFO, WARNING
from typing import Any, Optional, Set

from pydantic_settings import BaseSettings, SettingsConfigDict

__all__ = ["DEBUG", "CRITICAL", "ERROR", "INFO", "WARNING"]


class LogSettings(BaseSettings):
    level: int = logging.INFO
    format: str = (
        "%(asctime)s - RagChat:%(levelname)s: %(filename)s:%(lineno)d - %(message)s"
    )
    date_format: str = "%H:%M:%S"
    file_path: Optional[str] = None

    model_config = SettingsConfigDict(case_sensitive=False, env_prefix="LOG_")


# ANSI color codes
COLORS = {
    "RESET": "\033[0m",
    "RED": "\033[91m",
    "GREEN": "\033[92m",
    "YELLOW": "\033[93m",
    "BLUE": "\033[94m",
    "MAGENTA": "\033[95m",
    "CYAN": "\033[96m",
    "WHITE": "\033[97m",
}

# Map log levels to colors
LEVEL_COLORS = {
    logging.DEBUG: COLORS["BLUE"],
    logging.INFO: COLORS["GREEN"],
    logging.WARNING: COLORS["YELLOW"],
    logging.ERROR: COLORS["RED"],
    logging.CRITICAL: COLORS["MAGENTA"],
}


# Configure reprlib for abbreviated representations
_repr = reprlib.Repr()
_repr.maxlist = 4  # Show at most 4 elements from lists
_repr.maxstring = 100  # Limit string length
_repr.maxdict = 4  # Show at most 4 key-value pairs from dictionaries
_repr.maxset = 4  # Show at most 4 elements from sets
_repr.maxtuple = 4  # Show at most 4 elements from tuples
_repr.maxfrozenset = 4  # Show at most 4 elements from frozensets
_repr.maxdeque = 4  # Show at most 4 elements from deques
_repr.maxarray = 4  # Show at most 4 elements from arrays


def abbrev(obj: Any) -> str:
    """Create an abbreviated string representation of an object."""
    return _repr.repr(obj)


class ColoredFormatter(logging.Formatter):
    """Custom formatter that adds colors to log messages based on their level."""

    def format(self, record: logging.LogRecord) -> str:
        # Get the original formatted message
        message = super().format(record)

        # Find the position of the level in the message
        level_str = record.levelname
        # Handle potential case where levelname isn't found directly
        try:
            timestamp_and_logger = message.split(level_str)[0]
            rest_of_message = message[len(timestamp_and_logger) + len(level_str) :]
        except ValueError:
            # Fallback if levelname isn't exactly in the formatted string
            timestamp_and_logger = ""
            rest_of_message = message

        # Apply color to the timestamp, logger name, and level
        color = LEVEL_COLORS.get(record.levelno, COLORS["RESET"])
        colored_message = (
            f"{color}{timestamp_and_logger}{level_str}{COLORS['RESET']}"
            f"{rest_of_message}"
        )

        return colored_message


_managed_loggers: Set[logging.Logger] = set()

_initial_settings = LogSettings()
_default_format = _initial_settings.format
_default_date_format = _initial_settings.date_format
_default_file_path = _initial_settings.file_path


def get_logger(name: str) -> logging.Logger:
    """
    Retrieves or creates a logger, configuring it with a colored console handler
    and an optional file handler. It sets `propagate=False` and tracks the logger
    for later configuration updates. The logger's level is not set by this function.
    """
    logger = logging.getLogger(name)

    if logger in _managed_loggers:
        return logger

    logger.propagate = False

    has_console_handler = any(
        isinstance(h, logging.StreamHandler) and h.stream == sys.stdout
        for h in logger.handlers
    )
    if not has_console_handler:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(
            ColoredFormatter(_default_format, _default_date_format)
        )
        logger.addHandler(console_handler)

    log_file_path = _default_file_path
    if log_file_path:
        has_file_handler = any(
            isinstance(h, logging.FileHandler) and h.baseFilename == log_file_path
            for h in logger.handlers
        )
        if not has_file_handler:
            file_handler = logging.FileHandler(log_file_path)
            file_handler.setFormatter(
                logging.Formatter(_default_format, _default_date_format)
            )
            logger.addHandler(file_handler)

    _managed_loggers.add(logger)

    return logger


def configure_logging(level: Optional[int] = None, configure_root: bool = True) -> None:
    """
    Applies logging configuration (level, format, date format) from `LogSettings`
    to all managed loggers and their handlers. It also updates the root logger
    if `configure_root` is `True`. This function should be called after
    environment variables are loaded to ensure settings are applied.

    Args:
        level: An optional logging level to override the level from settings/env vars.
        configure_root: If True, also configures the root logger.
    """
    settings = LogSettings()

    effective_level = level if level is not None else settings.level

    global _default_file_path
    _default_file_path = settings.file_path

    logging.info(
        f"Reconfiguring {len(_managed_loggers)} managed loggers with level {effective_level} ({logging.getLevelName(effective_level)})"
    )

    for logger in _managed_loggers:
        logger.setLevel(effective_level)
        for handler in logger.handlers:
            is_our_console = (
                isinstance(handler, logging.StreamHandler)
                and handler.stream == sys.stdout
            )
            is_our_file = (
                isinstance(handler, logging.FileHandler)
                and settings.file_path
                and handler.baseFilename == settings.file_path
            )

            if is_our_console or is_our_file:
                handler.setLevel(effective_level)

                new_formatter: Optional[ColoredFormatter | logging.Formatter] = None
                if is_our_console:
                    new_formatter = ColoredFormatter(
                        settings.format, settings.date_format
                    )
                elif is_our_file:
                    new_formatter = logging.Formatter(
                        settings.format, settings.date_format
                    )

                if new_formatter:
                    handler.setFormatter(new_formatter)

    if configure_root:
        logging.getLogger().setLevel(effective_level)
