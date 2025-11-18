#!/usr/bin/env python3

import json
import os
from utils.arg_parser import ArgParse
from utils.logger import LogLevel, Logger
from utils.tab_name import tab_name_from_arguments

CONFIG_DIR = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
CONFIG_PATH = os.path.join(CONFIG_DIR, "better-control")
SETTINGS_FILE = os.path.join(CONFIG_PATH, "settings.json")
TAB_FILE = os.path.join(CONFIG_PATH, "tab.txt")

def ensure_config_dir(logging: Logger) -> None:
    """Ensure the config directory exists

    Args:
        logging (Logger): Logger instance
    """
    try:
        logging.log(LogLevel.Info, f"Ensuring config directory exists at {CONFIG_PATH}")
        os.makedirs(CONFIG_PATH, exist_ok=True)
        logging.log(LogLevel.Info, "Config directory check complete")
    except Exception as e:
        logging.log(LogLevel.Error, f"Error creating config directory: {e}")

def load_settings(logging: Logger) -> dict:
    """Load settings from the settings file with validation"""
    ensure_config_dir(logging)
    default_settings = {
        "visibility": {},
        "positions": {},
        "usbguard_hidden_devices": [],
        "language": "en",
        "vertical_tabs": False,
        "vertical_tabs_icon_only": False
    }

    if not os.path.exists(SETTINGS_FILE):
        logging.log(LogLevel.Info, "Using default settings (file not found)")
        return default_settings

    try:
        with open(SETTINGS_FILE, 'r') as f:
            content = f.read().strip()
            if not content.startswith('{'):
                content = '{' + content  # Fix malformed JSON
            settings = json.loads(content)
            logging.log(LogLevel.Info, f"Loaded settings from {SETTINGS_FILE}")

        if not isinstance(settings, dict):
            logging.log(LogLevel.Warn, "Invalid settings format - using defaults")
            return default_settings

        for key in default_settings:
            if key not in settings:
                settings[key] = default_settings[key]
                logging.log(LogLevel.Info, f"Added missing setting: {key}")

        return settings

    except Exception as e:
        logging.log(LogLevel.Error, f"Error loading settings: {e}")
        return default_settings

def save_settings(settings: dict, logging: Logger) -> bool:
    """Save settings to the settings file with atomic write and validation"""
    try:
        ensure_config_dir(logging)

        if not isinstance(settings, dict):
            logging.log(LogLevel.Error, "Invalid settings - not a dictionary")
            return False

        default_settings = {
            "visibility": {},
            "positions": {},
            "usbguard_hidden_devices": [],
            "language": "en",
            "vertical_tabs": False,
            "vertical_tabs_icon_only": False
        }
        for key in default_settings:
            if key not in settings:
                settings[key] = default_settings[key]

        temp_path = SETTINGS_FILE + '.tmp'
        with open(temp_path, 'w') as f:
            json.dump(settings, f, indent=4)


        with open(temp_path, 'r') as f:
            json.load(f)

        os.replace(temp_path, SETTINGS_FILE)
        logging.log(LogLevel.Info, f"Settings saved successfully to {SETTINGS_FILE}")
        return True

    except Exception as e:
        logging.log(LogLevel.Error, f"Error saving settings: {e}")
        try:
            if 'temp_path' in locals() and os.path.exists(temp_path):
                os.unlink(temp_path)
        except:
            pass
        return False

def read_tab_from_file():
    if os.path.exists(TAB_FILE):
        with open(TAB_FILE, 'r', encoding='utf-8') as file:
            arg_parser = ArgParse(["better-control"] + file.read().split(" "))
            return tab_name_from_arguments(arg_parser)
