#!/usr/bin/env python3

import argparse
import json
import os
from copy import deepcopy
from pathlib import Path
from typing import Any
from better_control.utils.atomic_write import atomic_write
from better_control.utils.logger import LogLevel, Logger


class Config:
    DEFAULT_CONFIG: dict[str, Any] = {
        "visibility": {},
        "positions": {},
        "usbguard_hidden_devices": [],
        "language": "en",
        "vertical_tabs": False,
        "vertical_tabs_icon_only": False,
    }

    @staticmethod
    def add_arguments(parser: argparse.ArgumentParser) -> None:
        group = parser.add_argument_group("Configuration")
        group.add_argument(
            "--config-dir", type=Path, help="Override the config directory used."
        )

    def __init__(self, logger: Logger, args: argparse.Namespace):
        self.config_dir = Path()
        self.__logger = logger

        if args.config_dir != None:
            self.config_dir = args.config_dir
        else:
            xdg_config_home: str | None = os.environ.get("XDG_CONFIG_HOME")
            if xdg_config_home == None:
                xdg_config_home = os.path.expanduser("~/.config")
                self.__logger.log(
                    LogLevel.Warn,
                    f"$XDG_CONFIG_HOME is not set, using default value {xdg_config_home}",
                )
            self.config_dir = os.path.join(xdg_config_home, "better-control")

        self.__config_file = Path(os.path.join(self.config_dir, "settings.json"))

    def ensure_config_dir_exists(self) -> None:
        if os.path.exists(self.__config_file):
            return

        directory = self.__config_file.parent

        self.__logger.log(
            LogLevel.Info,
            f"Config directory ({directory}) doesn't exist, creating one.",
        )

        directory.mkdir(parents=True, exist_ok=True)

    def load(self) -> dict[str, Any]:
        self.__config: dict[str, Any] = deepcopy(Config.DEFAULT_CONFIG)

        if not self.__config_file.exists():
            return self.__config

        try:
            with open(self.__config_file, "r", encoding="utf-8") as f:
                settings = json.load(f)

            if not isinstance(settings, dict):
                self.__logger.log(LogLevel.Warn, "Invalid settings format, using defaults")
                return self.__config

            for key, default in Config.DEFAULT_CONFIG.items():
                if key not in settings:
                    settings[key] = default
                    self.__logger.log(LogLevel.Info, f"Added missing setting: {key}")

            self.__config = settings

            self.__logger.log(LogLevel.Info, f"Loaded settings from {self.__config_file}")

            return self.__config

        except (OSError, json.JSONDecodeError) as e:
            self.__logger.log(LogLevel.Error, f"Error loading settings: {e}")
            return self.__config

    def save(self) -> bool:
        try:
            for key, default in Config.DEFAULT_CONFIG.items():
                if key not in self.__config:
                    self.__config[key] = default

            self.ensure_config_dir_exists()
            atomic_write(self.__config_file, lambda f: json.dump(self.__config, f)) # type: ignore

            self.__logger.log(
                LogLevel.Info, f"Successfully saved settings to {self.__config_file}"
            )
            return True

        except Exception as e:
            self.__logger.log(LogLevel.Error, f"Error saving settings: {e}")
            return False
