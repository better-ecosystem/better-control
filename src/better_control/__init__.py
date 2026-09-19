import importlib.metadata
import os
import subprocess
import sys
import signal
import threading
import argparse

import gi  # type: ignore
from setproctitle import setproctitle

from better_control.utils.logger import LogLevel, Logger
from better_control.utils.settings import Config
from better_control.utils import translations

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gtk, GLib  # type: ignore

from better_control.ui.main_window import BetterControl
from better_control.utils.dependencies import check_all_dependencies
from better_control.tools.bluetooth import restore_last_sink
from better_control.ui.css.animations import load_animations_css


def process_language(args: argparse.Namespace, logger: Logger, config: Config):
    settings = config.load()
    available_languages = ["en", "es", "pt", "fr", "id", "it", "tr", "de", "ru"]

    if args.lang is not None:
        lang = args.lang
        if lang not in available_languages:
            print(f"\033[1;31mError: Invalid language code '{lang}'\033[0m")
            print("Falling back to English (en)")
            print(f"Available languages: {', '.join(available_languages)}")
            logger.log(
                LogLevel.Warn,
                f"Invalid language code '{lang}'. Falling back to default(en)",
            )
            lang = "en"
        settings["language"] = lang

        config.save()
        logger.log(LogLevel.Info, f"Language set to: {lang}")
    else:
        lang = settings.get("language", "default")
        if lang not in (available_languages + ["default"]):
            lang = "en"
            settings["language"] = lang
            config.save()
            logger.log(
                LogLevel.Warn,
                f"Invalid language '{lang}' in settings. Falling back to default(en)",
            )

    logger.log(LogLevel.Info, f"Loaded language setting from settings: {lang}")
    trans = translations.get_translations(logger, lang)
    return trans


def apply_environment_variables() -> None:
    os.environ["PYTHONUNBUFFERED"] = "1"
    os.environ["DBUS_FATAL_WARNINGS"] = "0"
    os.environ["GST_GL_XINITTHREADS"] = "1"
    os.environ["G_SLICE"] = "always-malloc"
    os.environ["MALLOC_CHECK_"] = "2"
    os.environ["MALLOC_PERTURB_"] = "0"


def set_window_floating_rules(logger: Logger) -> None:
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
            logger.log(LogLevel.Warn, f"Failed to set hyprland window rule: {e}")
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
            logger.log(LogLevel.Warn, f"Failed to set sway window rule: {e}")


def launch_main_window(
    args: argparse.Namespace, logger: Logger, trans: translations.Translation
) -> None:
    logger.log(LogLevel.Info, "Creating main window")
    win = BetterControl(trans, args, logger)
    logger.log(LogLevel.Info, "Main window created successfully")

    setproctitle("better-control")
    GLib.idle_add(lambda: restore_last_sink(logger))

    if args.size is not None:
        if "x" not in args.size:
            logger.log(LogLevel.Error, "Invalid window size")
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
            logger.log(LogLevel.Info, "Loaded animations CSS asynchronously")
        except Exception as e:
            logger.log(
                LogLevel.Warn, f"Failed to load animations CSS asynchronously: {e}"
            )

    threading.Thread(target=load_animations_async, daemon=True).start()

    try:
        Gtk.main()
    except KeyboardInterrupt:
        logger.log(LogLevel.Info, "Keyboard interrupt detected, exiting...")
        Gtk.main_quit()
        sys.exit(0)
    except Exception as e:
        logger.log(LogLevel.Error, f"Error in GTK main loop: {e}")
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

    Config.add_arguments(parser)
    Logger.add_arguments(parser)
    translations.add_arguments(parser)

    args = parser.parse_args()

    if args.version:
        print(f"{meta['Name']} {meta['Version']}")
        sys.exit(0)

    logger = Logger(args)
    logger.log(LogLevel.Info, "Starting Better Control")
    config = Config(logger, args)

    trans = process_language(args, logger, config)

    def check_dependencies_async():
        try:
            if not args.force and not check_all_dependencies(logger):
                logger.log(
                    LogLevel.Error,
                    "Missing required dependencies. Please install them and try again or use -f to force start.",
                )
        except Exception as e:
            logger.log(LogLevel.Error, f"Dependency check error: {e}")

    threading.Thread(target=check_dependencies_async, daemon=True).start()

    try:
        launch_main_window(args, logger, trans)
    except Exception as e:
        logger.log(LogLevel.Error, f"Fatal error starting application: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
