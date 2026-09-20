import importlib.metadata
import logging
import os
import subprocess
import sys
import signal
import threading
import argparse

import gi  # type: ignore
from setproctitle import setproctitle

from better_control.cache import Cache
from better_control.config import Config
from better_control import translations
from better_control.dependencies import DependencyChecker

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gtk, GLib  # type: ignore

from better_control.ui.main_window import BetterControl
from better_control.tools.bluetooth import restore_last_sink
from better_control.ui.css.animations import load_animations_css


def process_language(args: argparse.Namespace, logger: logging.Logger, config: Config):
    settings = config.load()
    available_languages = ["en", "es", "pt", "fr", "id", "it", "tr", "de", "ru"]

    if args.lang is not None:
        lang = args.lang
        if lang not in available_languages:
            print(f"\033[1;31mError: Invalid language code '{lang}'\033[0m")
            print("Falling back to English (en)")
            print(f"Available languages: {', '.join(available_languages)}")
            logger.warning(
                f"Invalid language code '{lang}'. Falling back to default(en)",
            )
            lang = "en"
        settings["language"] = lang

        config.save()
        logger.info(f"Language set to: {lang}")
    else:
        lang = settings.get("language", "default")
        if lang not in (available_languages + ["default"]):
            lang = "en"
            settings["language"] = lang
            config.save()
            logger.warning(
                f"Invalid language '{lang}' in settings. Falling back to default(en)",
            )

    logger.info(f"Loaded language setting from settings: {lang}")
    trans = translations.get_translations(logger, lang)
    return trans


def add_logger_arguments(parser: argparse.ArgumentParser):
    group = parser.add_argument_group("Logging")
    group.add_argument(
        "--log-level",
        choices=["debug", "info", "warning", "error", "critical"],
        default="info",
        help="Set the logging threshold level (default: info)",
    )
    group.add_argument(
        "--log-file",
        type=str,
        default=None,
        metavar="PATH",
        help="Path to a file to log into. If omitted, logs go to stderr.",
    )


def get_logger(args: argparse.Namespace, name: str) -> logging.Logger:
    level = getattr(logging, args.log_level.upper(), logging.INFO)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.handlers.clear()  # avoid duplicate handlers on repeated calls

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    if args.log_file:
        handler: logging.Handler = logging.FileHandler(args.log_file, encoding="utf-8")
    else:
        handler = logging.StreamHandler(sys.stderr)

    handler.setLevel(level)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    logger.propagate = False
    return logger


def apply_environment_variables() -> None:
    os.environ["PYTHONUNBUFFERED"] = "1"
    os.environ["DBUS_FATAL_WARNINGS"] = "0"
    os.environ["GST_GL_XINITTHREADS"] = "1"
    os.environ["G_SLICE"] = "always-malloc"
    os.environ["MALLOC_CHECK_"] = "2"
    os.environ["MALLOC_PERTURB_"] = "0"


def set_window_floating_rules(logger: logging.Logger) -> None:
    xdg = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
    sway_sock = os.environ.get("SWAYSOCK", "").lower()

    if "hyprland" in xdg:
        try:
            subprocess.run(
                [
                    "hyprctl",
                    "keyword",
                    "windowrule",
                    "float,class:^(better_control.py)$",
                ],
                check=False,
            )
        except Exception as e:
            logger.warning(f"Failed to set hyprland window rule: {e}")
    elif "sway" in sway_sock:
        try:
            subprocess.run(
                [
                    "swaymsg",
                    "for_window",
                    '[app_id="^better_control.py$"]',
                    "floating",
                    "enable",
                ],
                check=False,
            )
        except Exception as e:
            logger.warning(f"Failed to set sway window rule: {e}")


def launch_main_window(
    args: argparse.Namespace, logger: logging.Logger, trans: translations.Translation
) -> None:
    logger.info("Creating main window")
    win = BetterControl(trans, args, logger)
    logger.info("Main window created successfully")

    setproctitle("better-control")
    GLib.idle_add(lambda: restore_last_sink(logger))

    if args.size is not None:
        if "x" not in args.size:
            logger.error("Invalid window size")
            sys.exit(1)
        width_str, height_str = args.size.split("x", 1)
    else:
        width_str, height_str = "900", "600"

    width, height = int(width_str), int(height_str)
    win.set_default_size(width, height)
    win.resize(width, height)
    win.connect("destroy", Gtk.main_quit)
    win.show_all()

    threading.Thread(
        target=set_window_floating_rules, args=(logger,), daemon=True
    ).start()

    def load_animations_async():
        try:
            load_animations_css()
            logger.info("Loaded animations CSS asynchronously")
        except Exception as e:
            logger.warning(f"Failed to load animations CSS asynchronously: {e}")

    threading.Thread(target=load_animations_async, daemon=True).start()

    try:
        Gtk.main()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt detected, exiting...")
        Gtk.main_quit()
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error in GTK main loop: {e}")
        sys.exit(1)


def main() -> None:
    signal.signal(signal.SIGINT, lambda _, __: os._exit(0))
    signal.signal(signal.SIGTERM, lambda _, __: os._exit(0))
    apply_environment_variables()

    meta = importlib.metadata.metadata("better-control")

    parser = argparse.ArgumentParser(
        prog=meta["Name"],
        description=meta["Summary"],
    )

    group = parser.add_argument_group("Application")
    group.add_argument(
        "-V", "--version", action="store_true", help="Print the version and exit."
    )
    group.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Forces startup even if runtime dependencies are not satisfied.",
    )
    group.add_argument("-s", "--size", default=None, help="Window size, e.g. 900x600")
    group.add_argument(
        "-L", "--lang", default=None, help="Language code (e.g. en, es, fr)"
    )

    add_logger_arguments(parser)
    Config.add_arguments(parser)
    Cache.add_arguments(parser)
    translations.add_arguments(parser)

    args = parser.parse_args()

    if args.version:
        print(f"{meta["Name"]} {meta["Version"]}\nCopyright (C) 2026 Better Ecosystem.")
        sys.exit(0)

    logger = get_logger(args, meta["Name"])
    logger.info("Starting Better Control")
    config = Config(logger, args)
    cache = Cache(logger, args)

    trans = process_language(args, logger, config)

    def check_dependencies_async():
        try:
            if not args.force:
                result = DependencyChecker.check_all()

                if result.is_ok():
                    return

                logger.error(
                    "Missing required dependencies. Please install them and try again or use -f to force start.",
                )
                for dep in result.unwrap_err():
                    logger.error(f"Missing dependency {dep.command}")
        except Exception as e:
            logger.error(f"Dependency check error: {e}")

    threading.Thread(target=check_dependencies_async, daemon=True).start()

    try:
        launch_main_window(args, logger, trans)
    except Exception as e:
        logger.error(f"Fatal error starting application: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
