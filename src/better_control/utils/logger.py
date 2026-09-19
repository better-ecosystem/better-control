import datetime
from enum import IntEnum
import os
from pathlib import Path
import re
from sys import stderr
import time
from typing import Dict, Tuple
import argparse
from better_control.tools.terminal import term_support_color



class LogLevel(IntEnum):
    Error = 4
    Warn = 3
    Info = 2
    Debug = 1

    @classmethod
    def from_arg(cls, value: str) -> "LogLevel":
        try:
            return cls[value.capitalize()]
        except KeyError:
            pass

        try:
            return cls(int(value))
        except ValueError, KeyError:
            names = ", ".join(m.name.lower() for m in cls)
            raise argparse.ArgumentTypeError(
                f"invalid log level {value!r} (choose from: {names})"
            )


def get_current_time():
    now = datetime.datetime.now()
    ms = int((time.time() * 1000) % 1000)
    return f"{now.minute:02}:{now.second:02}:{ms:03}"


class Logger:
    @staticmethod
    def add_arguments(parser: argparse.ArgumentParser) -> None:
        group = parser.add_argument_group("Logging")
        group.add_argument(
            "-l",
            "--log-level",
            type=LogLevel.from_arg,
            default=LogLevel.Error,
            help="Set the threshold log-level, defaults to error. (1-4)/(debug, info, warn, error)",
        )

        group.add_argument(
            "--log-file",
            type=Path,
            help="Set the file the logger should log into, override the log to stderr.",
        )

        group.add_argument(
            "-r",
            "--redact",
            action="store_true",
            help="Redact sensitive informations from the logs.",
        )

    def __init__(self, args: argparse.Namespace) -> None:
        self.__should_redact: bool = args.redact
        self.__log_level: LogLevel = args.log_level
        self.__log_file_path: Path | None = args.log_file

        self.__add_color: bool = term_support_color()
        self.__labels: Dict[LogLevel, Tuple[str, str]] = {
            LogLevel.Info: (
                "\033[1;37m[\033[1;32mINFO\033[1;37m]:\033[0;0;0m",
                "[INFO]:",
            ),
            LogLevel.Error: (
                "\033[1;37m[\033[1;31mERROR\033[1;37m]:\033[0;0;0m",
                "[ERROR]:",
            ),
            LogLevel.Debug: (
                "\033[1;37m[\033[1;36mDEBUG\033[1;37m]:\033[0;0;0m",
                "[DEBUG]:",
            ),
            LogLevel.Warn: (
                "\033[1:37m[\033[1;33mWARNING\033[1;37m]:\033[0;0;0m",
                "[WARNING]:",
            ),
        }

        self.__redaction_patterns = [
            # WiFi network names/SSIDs
            (r"(Connecting to WiFi network: )([^\s]+)", r"\1[REDACTED-WIFI]"),
            (
                r"(Connected to )([^\s]+)( using saved connection)",
                r"\1[REDACTED-WIFI]\3",
            ),
            # Device identifiers and names (audio, bluetooth, etc.)
            (r"(Current active output sink: )(.*)", r"\1[REDACTED-DEVICE]"),
            (r"(Current active input source: )(.*)", r"\1[REDACTED-DEVICE]"),
            (r"(Adding output sink: )([^\(]+)(\(.*\))", r"\1[REDACTED-DEVICE-ID] \3"),
            (r"(Adding input source: )([^\(]+)(\(.*\))", r"\1[REDACTED-DEVICE-ID] \3"),
            # User and machine identifiers
            (r'(application\.process\.user = ")[^"]+(\")', r"\1[REDACTED-USER]\2"),
            (r'(application\.process\.host = ")[^"]+(\")', r"\1[REDACTED-HOSTNAME]\2"),
            (
                r'(application\.process\.machine_id = ")[^"]+(\")',
                r"\1[REDACTED-MACHINE-ID]\2",
            ),
            # Personal names and identifiers
            (
                r"(Connecting to )([A-Z][a-z]+ [A-Z][a-z]+)(\.\.\.)",
                r"\1[REDACTED-NAME]\3",
            ),
            # Password related info (if present)
            (r"(password=)[^\s,;\'\"]+", r"\1[REDACTED-PASSWORD]"),
            (r'(password="?)[^"\']+("?)', r"\1[REDACTED-PASSWORD]\2"),
            (r'(psk="?)[^"\']+("?)', r"\1[REDACTED-PASSWORD]\2"),
            # Specific media/content identifiers
            (r'(media\.name = ")[^"]+(\")', r"\1[REDACTED-MEDIA]\2"),
            # Tokens and authentication
            (r"(token=)[^\s]+", r"\1[REDACTED-TOKEN]"),
            (r"(auth[-_]?token=)[^\s]+", r"\1[REDACTED-TOKEN]"),
        ]

        self.__log_file = None

        if self.__log_file_path != None:
            if not os.path.isfile(self.__log_file_path):
                self.__log_file = open(self.__log_file_path, "x")
            else:
                self.__log_file = open(self.__log_file_path, "a")

    def __del__(self):
        if hasattr(self, "_Logger__log_file") and self.__log_file is not None:
            self.__log_file.close()

    def __redact_sensitive_info(self, message: str) -> str:
        """Redacts sensitive information from log messages

        Args:
            message (str): The original log message

        Returns:
            str: The redacted log message
        """
        # Skip redaction if not enabled
        if not self.__should_redact:
            return message

        redacted_message = message

        # Apply each redaction pattern
        for pattern, replacement in self.__redaction_patterns:
            redacted_message = re.sub(
                pattern, replacement, redacted_message, flags=re.IGNORECASE
            )

        return redacted_message

    def log(self, log_level: LogLevel, message: str):
        """Logs messages to a stream based on user arg

        Args:
            log_level (LogLevel): the log level, which consists of Debug, Info, Warn, Error
            message (str): the log message
        """

        file = stderr

        if hasattr(self, "_Logger__log_file") and self.__log_file is not None:
            file = self.__log_file

        redacted_message = self.__redact_sensitive_info(message)

        label = (
            self.__labels[log_level][0]
            if self.__add_color
            else self.__labels[log_level][1]
        )

        fmt = f"{get_current_time()} {label} {redacted_message}"

        self.__last_log_msg = fmt

        if file == stderr and self.__log_level > log_level:
            return

        print(fmt, file=file)

    def get_last_log_msg(self) -> str:
        return self.__last_log_msg
