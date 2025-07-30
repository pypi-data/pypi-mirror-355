"""
Module to provide for very simple logging support.
"""

import argparse
import logging
from typing import Any, Dict, cast


class SimpleLogging:
    """
    Class to provide for very simple logging support.
    """

    __available_log_maps: Dict[str, int] = {
        "CRITICAL": logging.CRITICAL,
        "ERROR": logging.ERROR,
        "WARNING": logging.WARNING,
        "INFO": logging.INFO,
        "DEBUG": logging.DEBUG,
    }

    __new_handler = None
    __base_logger = None

    @staticmethod
    def initialize_logging(args: argparse.Namespace) -> None:
        """
        Initialize the logging subsytem using the arguments from the `add_standard_arguments` function.
        """

        SimpleLogging.__base_logger = logging.getLogger()
        SimpleLogging.__new_handler = None
        if args.log_file:
            SimpleLogging.__new_handler = logging.FileHandler(args.log_file)
            SimpleLogging.__new_handler.setLevel(
                SimpleLogging.__available_log_maps[args.log_level]
            )
            SimpleLogging.__base_logger.addHandler(SimpleLogging.__new_handler)
        else:
            SimpleLogging.__base_logger.setLevel(
                SimpleLogging.__available_log_maps[args.log_level]
            )

    @staticmethod
    def terminate_logging() -> None:
        """
        Terminate any logging setup in the `initialize_logging` function.
        """
        if SimpleLogging.__new_handler:
            SimpleLogging.__new_handler.close()
            SimpleLogging.__new_handler = None

    @staticmethod
    def __log_level_type(argument: Any) -> str:
        """
        Function to help argparse limit the valid log levels.
        """
        if argument in SimpleLogging.__available_log_maps:
            return cast(str, argument)
        raise ValueError(f"Value '{argument}' is not a valid log level.")

    @staticmethod
    def add_standard_arguments(
        parser: argparse.ArgumentParser, default_log_level: str
    ) -> None:
        """
        Add any required arguments for adding logging.
        """
        parser.add_argument(
            "--log-level",
            dest="log_level",
            action="store",
            default=default_log_level,
            help="minimum level for any log messages",
            type=SimpleLogging.__log_level_type,
            choices=list(SimpleLogging.__available_log_maps.keys()),
        )
        parser.add_argument(
            "--log-file",
            dest="log_file",
            action="store",
            help="destination file for log messages",
        )
