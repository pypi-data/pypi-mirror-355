import logging
import os

from aiko_services.main.utilities.logger import (
    _LOG_FORMAT_DATETIME,
    _LOG_FORMAT_DEFAULT,
)

__all__ = ["configure_root_logger", "get_default_logger"]


def get_default_logger(name="hl_client"):
    """
    Return a child logger of the root. In each module/class, do:
        logger = get_logger(__name__)
    """
    return logging.getLogger(name)


def configure_root_logger(log_path, log_level="INFO"):
    root = logging.getLogger()

    if any("pytest" in type(h).__module__ for h in root.handlers):
        root.setLevel(log_level)
    else:
        if root.hasHandlers():
            root.handlers.clear()

        # Ensure log_path exists
        directory = os.path.dirname(log_path)
        os.makedirs(directory, exist_ok=True)

        if not os.path.exists(log_path):
            with open(log_path, "w") as file:
                file.write("")  # Creates an empty file

        # Setup File Handler
        file_handler = logging.FileHandler(log_path)
        formatter = logging.Formatter(
            _LOG_FORMAT_DEFAULT,
            datefmt=_LOG_FORMAT_DATETIME,
        )
        file_handler.setFormatter(formatter)

        # Setup Stream Handler
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)

        log_level_mapping = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL,
        }

        log_level = log_level_mapping.get(log_level)
        logging.basicConfig(level=log_level, handlers=[stream_handler, file_handler])


class ColourStr:
    HEADER = "\033[95m"

    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    ORANGE = "\033[93m"
    RED = "\033[91m"

    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"

    RESET = "\033[0m"

    @staticmethod
    def blue(s):
        return ColourStr.BLUE + s + ColourStr.RESET

    @staticmethod
    def cyan(s):
        return ColourStr.CYAN + s + ColourStr.RESET

    @staticmethod
    def green(s):
        return ColourStr.GREEN + s + ColourStr.RESET

    @staticmethod
    def red(s):
        return ColourStr.RED + s + ColourStr.RESET

    @staticmethod
    def bold(s):
        return ColourStr.BOLD + s + ColourStr.RESET

    @staticmethod
    def underline(s):
        return ColourStr.UNDERLINE + s + ColourStr.RESET
