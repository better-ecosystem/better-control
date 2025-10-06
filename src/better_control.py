#!/usr/bin/env python3

import os
import subprocess
from typing import Any
import gi  # type: ignore
import sys
from setproctitle import setproctitle
import signal
from utils.arg_parser import ArgParse
from utils.logger import LogLevel, Logger
from utils.settings import load_settings, ensure_config_dir, save_settings
from utils.translations import get_translations

# Initialize GTK before imports
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gtk, GLib  # type: ignore

from ui.main_window import BetterControl
from utils.dependencies import check_all_dependencies
from tools.bluetooth import restore_last_sink
from ui.css.animations import load_animations_css


def signal_handler(sig, frame):
    """Immediately kill the process on signal"""
    import os

    os._exit(0)


def main():
    # Register all critical signals
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGSEGV, signal_handler)
    signal.signal(signal.SIGABRT, signal_handler)

    # Initialize GTK safety net
    Gtk.init_check()
    if not Gtk.init_check()[0]:
        sys.stderr.write("Failed to initialize GTK\n")
        sys.exit(1)

    # Initialize environment
    os.environ['PYTHONUNBUFFERED'] = '1'
    os.environ['DBUS_FATAL_WARNINGS'] = '0'
    os.environ['GST_GL_XINITTHREADS'] = '1'
    os.environ['G_SLICE'] = 'always-malloc'
    os.environ['MALLOC_CHECK_'] = '2'
    os.environ['MALLOC_PERTURB_'] = '0'

    arg_parser = ArgParse(sys.argv)

    if arg_parser.find_arg(("-h", "--help")):
        arg_parser.print_help_msg(sys.stdout)
        sys.exit(0)

    logger = Logger(arg_parser)
    logger.log(LogLevel.Info, "Starting Better Control")

    setup_environment_and_dirs(logger)

    lang, txt = load_language_and_translations(arg_parser, logger)

    # Deferred loading of animations CSS until after main window is shown
    # load_animations_css()
    # logger.log(LogLevel.Info, "Loaded animations CSS")

    # Start dependency check asynchronously to avoid blocking startup
    import threading

    def check_dependencies_async():
        try:
            if (
                not arg_parser.find_arg(("-f", "--force"))
                and not check_all_dependencies(logger)
            ):
                logger.log(
                    LogLevel.Error,
                    "Missing required dependencies. Please install them and try again or use -f to force start.",
                )
                # Optionally, show a GTK dialog warning here
        except Exception as e:
            logger.log(LogLevel.Error, f"Dependency check error: {e}")

    threading.Thread(target=check_dependencies_async, daemon=True).start()

    try:
        launch_application(arg_parser, logger, txt)
    except Exception as e:
        logger.log(LogLevel.Error, f"Fatal error starting application: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


def setup_environment_and_dirs(logger):
    ensure_config_dir(logger)

    try:
        temp_dir = os.path.join("/tmp", "better-control")
        os.makedirs(temp_dir, exist_ok=True)
        logger.log(LogLevel.Info, f"Created temporary directory at {temp_dir}")
    except Exception as e:
        logger.log(LogLevel.Error, f"Error creating temporary directory: {e}")


def load_language_and_translations(arg_parser, logger):
    settings = load_settings(logger)
    available_languages = ["en", "es", "pt", "fr", "id", "it", "tr", "de", "ru"]

    if arg_parser.find_arg(("-L", "--lang")):
        lang = arg_parser.option_arg(("-L", "--lang"))
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
        save_settings(settings, logger)
        logger.log(LogLevel.Info, f"Language set to: {lang}")
    else:
        lang = settings.get("language", "default")
        if lang not in (available_languages + ["default"]):
            lang = "en"
            settings["language"] = lang
            save_settings(settings, logger)
            logger.log(
                LogLevel.Warn,
                f"Invalid language '{lang}' in settings. Falling back to default(en)",
            )
    logger.log(LogLevel.Info, f"Loaded language setting from settings: {lang}")
    # cast to Any to satisfy the argument type diagnostic
    txt = get_translations(logger, lang)  # type: ignore
    return lang, txt


def launch_application(arg_parser, logger, txt):
    import time

    time.sleep(0.1)

    logger.log(LogLevel.Info, "Creating main window")
    win = BetterControl(txt, arg_parser, logger)
    logger.log(LogLevel.Info, "Main window created successfully")

    setproctitle("better-control")

    def run_audio_operation():
        restore_last_sink(logger)

    GLib.idle_add(run_audio_operation)

    option: Any = []
    if arg_parser.find_arg(("-s", "--size")):
        optarg = arg_parser.option_arg(("-s", "--size"))
        if optarg is None or 'x' not in optarg:
            logger.log(LogLevel.Error, "Invalid window size")
            sys.exit(1)
        else:
            option = optarg.split('x')
    else:
        option = [900, 600]

    win.set_default_size(int(option[0]), int(option[1]))
    win.resize(int(option[0]), int(option[1]))
    win.connect("destroy", Gtk.main_quit)
    win.show_all()

    import threading

    def set_window_floating_rules():
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

    threading.Thread(target=set_window_floating_rules, daemon=True).start()

    # Load animations CSS asynchronously after window is shown
    def load_animations_async():
        try:
            load_animations_css()
            logger.log(LogLevel.Info, "Loaded animations CSS asynchronously")
        except Exception as e:
            logger.log(LogLevel.Warn, f"Failed to load animations CSS asynchronously: {e}")

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


def parse_arguments():
    arg_parser = ArgParse(sys.argv)

    if arg_parser.find_arg(("-h", "--help")):
        arg_parser.print_help_msg(sys.stdout)
        sys.exit(0)

    return arg_parser


def setup_logging(arg_parser):
    logger = Logger(arg_parser)
    logger.log(LogLevel.Info, "Starting Better Control")
    return logger


def setup_temp_directory(logger):
    ensure_config_dir(logger)
    try:
        temp_dir = os.path.join("/tmp", "better-control")
        os.makedirs(temp_dir, exist_ok=True)
        logger.log(LogLevel.Info, f"Created temporary directory at {temp_dir}")
    except Exception as e:
        logger.log(LogLevel.Error, f"Error creating temporary directory: {e}")


def process_language(arg_parser, logger):
    settings = load_settings(logger)
    available_languages = ["en", "es", "pt", "fr", "id", "it", "tr", "de", "ru"]

    if arg_parser.find_arg(("-L", "--lang")):
        lang = arg_parser.option_arg(("-L", "--lang"))
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
        save_settings(settings, logger)
        logger.log(LogLevel.Info, f"Language set to: {lang}")
    else:
        lang = settings.get("language", "default")
        if lang not in (available_languages + ["default"]):
            lang = "en"
            settings["language"] = lang
            save_settings(settings, logger)
            logger.log(
                LogLevel.Warn,
                f"Invalid language '{lang}' in settings. Falling back to default(en)",
            )

    logger.log(LogLevel.Info, f"Loaded language setting from settings: {lang}")
    # cast to Any to satisfy the argument type diagnostic
    txt = get_translations(logger, lang)  # type: ignore
    return txt


def apply_environment_variables():
    # Initialize environment variables
    os.environ['PYTHONUNBUFFERED'] = '1'
    os.environ['DBUS_FATAL_WARNINGS'] = '0'
    os.environ['GST_GL_XINITTHREADS'] = '1'
    os.environ['G_SLICE'] = 'always-malloc'
    os.environ['MALLOC_CHECK_'] = '2'
    os.environ['MALLOC_PERTURB_'] = '0'


def launch_main_window(arg_parser, logger, txt):
    logger.log(LogLevel.Info, "Creating main window")
    win = BetterControl(txt, arg_parser, logger)
    logger.log(LogLevel.Info, "Main window created successfully")

    setproctitle("better-control")

    def run_audio_operation():
        restore_last_sink(logger)

    GLib.idle_add(run_audio_operation)

    option: Any = []
    if arg_parser.find_arg(("-s", "--size")):
        optarg = arg_parser.option_arg(("-s", "--size"))
        if optarg is None or 'x' not in optarg:
            logger.log(LogLevel.Error, "Invalid window size")
            sys.exit(1)
        else:
            option = optarg.split('x')
    else:
        option = [900, 600]

    win.set_default_size(int(option[0]), int(option[1]))
    win.resize(int(option[0]), int(option[1]))
    win.connect("destroy", Gtk.main_quit)
    win.show_all()

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
            logger.log(
                LogLevel.Warn, f"Failed to set hyprland window rule: {e}"
            )
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
            logger.log(
                LogLevel.Warn, f"Failed to set sway window rule: {e}"
            )

    try:
        Gtk.main()
    except KeyboardInterrupt:
        logger.log(LogLevel.Info, "Keyboard interrupt detected, exiting...")
        Gtk.main_quit()
        sys.exit(0)
    except Exception as e:
        logger.log(LogLevel.Error, f"Error in GTK main loop: {e}")
        sys.exit(1)


def initialize_and_start():
    # Register signals again to be safe
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    apply_environment_variables()

    arg_parser = parse_arguments()

    logger = setup_logging(arg_parser)

    setup_temp_directory(logger)

    txt = process_language(arg_parser, logger)

    # Asynchronous dependency check to avoid blocking startup
    import threading

    def check_dependencies_async():
        try:
            if (
                not arg_parser.find_arg(("-f", "--force"))
                and not check_all_dependencies(logger)
            ):
                logger.log(
                    LogLevel.Error,
                    "Missing required dependencies. Please install them and try again or use -f to force start.",
                )
                # Optionally, show a GTK dialog warning here
        except Exception as e:
            logger.log(LogLevel.Error, f"Dependency check error: {e}")

    threading.Thread(target=check_dependencies_async, daemon=True).start()

    try:
        launch_main_window(arg_parser, logger, txt)
    except Exception as e:
        logger.log(LogLevel.Error, f"Fatal error starting application: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    initialize_and_start()
