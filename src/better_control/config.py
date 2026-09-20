#!/usr/bin/env python3

import argparse
import json
import os
from copy import deepcopy
from pathlib import Path
from typing import Any
from better_control import utils
from logging import Logger


class Config:
    DEFAULT_CONFIG: dict[str, Any] = {
        "visibility": {},
        "positions": {},
        "usbguard_hidden_devices": [],
        "language": "en",
        "vertical_tabs": False,
        "vertical_tabs_icon_only": False,
        "cache_dir": Path(
            os.path.join(
                os.environ.get("$XDG_CACHE_HOME", os.path.expanduser("~/.cache")),
                "better-control",
            )
        ),
    }

    @staticmethod
    def add_arguments(parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--config-dir",
            type=Path,
            default=os.path.join(
                os.environ.get("$XDG_CONFIG_HOME", os.path.expanduser("~/.config")),
                "better-control",
            ),
            help="Override the default config directory ($XDG_CONFIG_HOME/better-control).",
        )

    def __init__(self, logger: Logger, args: argparse.Namespace):
        self.config_dir = args.config_dir
        self.__logger = logger
        self.__config_file = Path(os.path.join(self.config_dir, "settings.json"))
        self.__logger.info(f"Using {self.config_dir} as the config directory.")

    def ensure_config_dir_exists(self) -> None:
        if os.path.exists(self.__config_file):
            return

        directory = self.__config_file.parent

        self.__logger.info(
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
                self.__logger.warning("Invalid settings format, using defaults")
                return self.__config

            for key, default in Config.DEFAULT_CONFIG.items():
                if key not in settings:
                    settings[key] = default
                    self.__logger.info(f"Added missing setting: {key}")

            self.__config = settings

            self.__logger.info(f"Loaded settings from {self.__config_file}")

            return self.__config

        except (OSError, json.JSONDecodeError) as e:
            self.__logger.error(f"Error loading settings: {e}")
            return self.__config

    def save(self) -> bool:
        try:
            for key, default in Config.DEFAULT_CONFIG.items():
                if key not in self.__config:
                    self.__config[key] = default

            self.ensure_config_dir_exists()
            utils.write(self.__config_file, lambda f: json.dump(self.__config, f))

            self.__logger.info(f"Successfully saved settings to {self.__config_file}")
            return True

        except Exception as e:
            self.__logger.error(f"Error saving settings: {e}")
            return False
