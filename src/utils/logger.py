import datetime
from enum import Enum
from io import TextIOWrapper
import os
import re
import sys
import traceback
from sys import stderr, stdout
import time
from typing import Dict, List, Optional, Pattern, Tuple

CRASH_LOG_DIR = os.path.join(
    os.environ.get("XDG_CACHE_HOME", os.path.expanduser("~/.cache")),
    "better-control",
    "crashes"
)

def emergency_log(message: str, stack: str = "") -> None:
    """Emergency logging for crashes"""
    try:
        os.makedirs(CRASH_LOG_DIR, exist_ok=True)
        crash_file = os.path.join(
            CRASH_LOG_DIR,
            f"crash_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        )
        with open(crash_file, "w") as f:
            f.write(f"CRASH: {message}\n")
            f.write(f"Python: {sys.version}\n")
            f.write(f"Stack:\n{stack}\n")
    except:
        pass

from utils.arg_parser import parse_args 
from utils.pair import Pair
from tools.terminal import term_support_color


class LogLevel(Enum):
    Debug = 3
    Info = 2
    Warn = 1
    Error = 0


def get_current_time():
    now = datetime.datetime.now()
    ms = int((time.time() * 1000) % 1000)
    return f"{now.minute:02}:{now.second:02}:{ms:03}"


class Logger:
    def __init__(self, arg_parser: dict) -> None:
        log_info: Pair[bool, Optional[str]] = Pair(False, None)

        # Check if log argument is present in the args dictionary
        if "log" in arg_parser or arg_parser.get('verbose'):
            log_info.first = True
            log_info.second = arg_parser.get('log')
            
        # Check if redaction is enabled via --redact flag
        self.__should_redact: bool = arg_parser.get('redact', False)

        self.__should_log: bool = log_info.first or arg_parser.get('verbose', False)
        self.__log_level: int = (
            int(log_info.second)
            if (log_info.second is not None) and (log_info.second.isdigit())
            else 3
        )
        self.__add_color: bool = term_support_color()
        self.__log_file_name: str = (
            log_info.second
            if (log_info.second is not None) and (not log_info.second.isdigit())
            else ""
        )
        self.__labels: Dict[LogLevel, Pair[str, str]] = {
            LogLevel.Info: Pair(
                "\x1b[1;37m[\x1b[1;32mINFO\x1b[1;37m]:\x1b[0;0;0m", "[INFO]:"
            ),
            LogLevel.Error: Pair(
                "\x1b[1;37m[\x1b[1;31mERROR\x1b[1;37m]:\x1b[0;0;0m", "[ERROR]:"
            ),
            LogLevel.Debug: Pair(
                "\x1b[1;37m[\x1b[1;36mDEBUG\x1b[1;37m]:\x1b[0;0;0m", "[DEBUG]:"
            ),
            LogLevel.Warn: Pair(
                "\x1b[1:37m[\x1b[1;33mWARNING\x1b[1;37m]:\x1b[0;0;0m", "[WARNING]:"
            ),
        }
        
        # Define patterns for sensitive information to redact
        self.__redaction_patterns = [
            # WiFi network names/SSIDs
            (r'(Connecting to WiFi network: )([^\s]+)', r'\1[REDACTED-WIFI]'),
            (r'(Connected to )([^\s]+)( using saved connection)', r'\1[REDACTED-WIFI]\3'),
            
            # Device identifiers and names (audio, bluetooth, etc.)
            (r'(Current active output sink: )(.*)', r'\1[REDACTED-DEVICE]'),
            (r'(Current active input source: )(.*)', r'\1[REDACTED-DEVICE]'),
            (r'(Adding output sink: )([^\(]+)(\(.*\))', r'\1[REDACTED-DEVICE-ID] \3'),
            (r'(Adding input source: )([^\(]+)(\(.*\))', r'\1[REDACTED-DEVICE-ID] \3'),
            
            # User and machine identifiers
            (r'(application\.process\.user = ")[^"]+(\")', r'\1[REDACTED-USER]\2'),
            (r'(application\.process\.host = ")[^"]+(\")', r'\1[REDACTED-HOSTNAME]\2'),
            (r'(application\.process\.machine_id = ")[^"]+(\")', r'\1[REDACTED-MACHINE-ID]\2'),
            
            # Personal names and identifiers
            (r'(Connecting to )([A-Z][a-z]+ [A-Z][a-z]+)(\.\.\.)', r'\1[REDACTED-NAME]\3'),
            
            # Password related info (if present)
            (r'(password=)[^\s,;\'\"]+', r'\1[REDACTED-PASSWORD]'),
            (r'(password="?)[^"\']+("?)', r'\1[REDACTED-PASSWORD]\2'),
            (r'(psk="?)[^"\']+("?)', r'\1[REDACTED-PASSWORD]\2'),
            
            # Specific media/content identifiers
            (r'(media\.name = ")[^"]+(\")', r'\1[REDACTED-MEDIA]\2'),
            
            # Tokens and authentication
            (r'(token=)[^\s]+', r'\1[REDACTED-TOKEN]'),
            (r'(auth[-_]?token=)[^\s]+', r'\1[REDACTED-TOKEN]'),
        ]

        # Initialize log file attribute
        self.__log_file = None

        if self.__log_file_name != "":
            if self.__log_file_name.isdigit():
                digit: int = int(self.__log_file_name)

                if digit in range(4):
                    self.__log_level = digit
                else:
                    self.log(LogLevel.Error, "Invalid log level provided")
            elif not self.__log_file_name.isdigit():
                if not os.path.isfile(self.__log_file_name):
                    self.__log_file = open(self.__log_file_name, "x")
                else:
                    self.__log_file = open(self.__log_file_name, "a")
            else:
                self.log(LogLevel.Error, "Invalid option for argument log")

    def __del__(self):
        if hasattr(self, '_Logger__log_file') and self.__log_file is not None:
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
            redacted_message = re.sub(pattern, replacement, redacted_message, flags=re.IGNORECASE)
            
        return redacted_message

    def log(self, log_level: LogLevel, message: str):
        """Logs messages to a stream based on user arg

        Args:
            log_level (LogLevel): the log level, which consists of Debug, Info, Warn, Error
            message (str): the log message
        """
        # Redact sensitive information
        redacted_message = self.__redact_sensitive_info(message)
        
        label = (
            self.__labels[log_level].first
            if self.__add_color
            else self.__labels[log_level].second
        )

        fmt = f"{get_current_time()} {label} {redacted_message}"

        self.__last_log_msg = fmt

        if log_level != LogLevel.Error and self.__should_log == False:
            return

        if self.__log_file_name != "":
            self.__log_to_file(fmt)
            print(fmt, file=stderr)
        elif log_level == LogLevel.Warn and self.__log_level < 3:
            print(fmt, file=stdout)
        elif log_level == LogLevel.Info and self.__log_level < 2:
            print(fmt, file=stdout)
        elif log_level == LogLevel.Debug and self.__log_level < 1:
            print(fmt, file=stdout)

    def get_last_log_msg(self) -> str:
        return self.__last_log_msg

    def __log_to_file(self, message: str):
        if not hasattr(self, '_Logger__log_file') or self.__log_file is None:
            return

        print(message, file=self.__log_file)
