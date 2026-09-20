import argparse
import json
from logging import Logger
import os
from pathlib import Path
from typing import Any, Dict
from result import Result, Ok, Err

from better_control import utils


class Cache:
    @staticmethod
    def add_arguments(parser: argparse.ArgumentParser):
        parser.add_argument(
            "--cache-dir",
            type=Path,
            default=os.path.join(
                os.environ.get("$XDG_CACHE_HOME", os.path.expanduser("~/.cache")),
                "better-control",
            ),
            help="Override the default cache directory ($XDG_CACHE_HOME/better-control).",
        )

    def __init__(self, logger: Logger, args: argparse.Namespace):
        self.cache_dir: Path = args.cache_dir
        self.__logger = logger
        self.__cache_files: Dict[Path, Any]

        self.__logger.info(f"Using {self.cache_dir} as the cache directory.")

    def ensure_exists(self) -> None:
        os.makedirs(self.cache_dir, exist_ok=True)

    def get_file(self, name: str) -> Any:
        path = self.__construct_path_from_name(name)
        self.__logger.info(f"Opening cache file {path}.")

        if path in self.__cache_files:
            return self.__cache_files[path]

        if path.exists():
            with open(path) as file:
                self.__cache_files[path] = json.load(file)
            return self.__cache_files[path]

        self.__cache_files[path] = {}
        return self.__cache_files[path]

    def save_file(self, name: str) -> Result[None, None]:
        path = self.__construct_path_from_name(name)
        self.__logger.info(f"Saving cache file {path}")

        if path not in self.__cache_files:
            return Err(None)

        utils.write(path, lambda f: json.dump(self.__cache_files[path], f))
        return Ok(None)

    def __construct_path_from_name(self, name: str) -> Path:
        return Path(self.cache_dir.joinpath(f"{name}.json"))
