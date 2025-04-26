"""
Translation manager for Better Control

This module manages loading and switching between different language translations.
"""

import os
import importlib
from logging import Logger
from typing import Protocol, Optional, Dict, Type

from utils.logger import LogLevel

class Translation(Protocol):
    """Base protocol for all translations in the application.

    This provides type hints without needing to import all language classes.
    All language classes should implement these properties and methods.
    """
    # Common properties that all translations must have
    msg_desc: str
    msg_app_url: str
    msg_usage: str

    # Tab names
    msg_tab_volume: str
    msg_tab_wifi: str
    msg_tab_bluetooth: str
    msg_tab_battery: str
    msg_tab_display: str
    msg_tab_power: str
    msg_tab_autostart: str
    msg_tab_usbguard: str
    
    # Common UI elements
    loading: str
    loading_tabs: str
    close: str
    enable: str
    disable: str

class TranslationManager:
    """Manages loading and switching between language translations"""
    
    _registered_languages: Dict[str, Type[Translation]] = {}
    _language_names: Dict[str, str] = {
        "en": "English",
        "es": "Español",
        "pt": "Português",
        "fr": "Français",
        "id": "Bahasa Indonesia",
        "hi": "हिन्दी"
    }
    
    @classmethod
    def register_language(cls, lang_code: str, language_class: Type[Translation]) -> None:
        """Register a language class with its code
        
        Args:
            lang_code: Language code (en, es, pt, etc.)
            language_class: The language class to register
        """
        cls._registered_languages[lang_code] = language_class
    
    @classmethod
    def get_available_languages(cls) -> Dict[str, str]:
        """Get a dictionary of available language codes and their names
        
        Returns:
            Dict mapping language codes to their display names
        """
        # Only return languages that are actually registered
        return {code: name for code, name in cls._language_names.items() 
                if code in cls._registered_languages}
    
    @classmethod
    def load_all_languages(cls, logging: Optional[Logger] = None) -> None:
        """Dynamically load all language modules from the languages directory
        
        Args:
            logging: Optional logger to log the loading process
        """
        if logging:
            logging.log(LogLevel.Info, "Loading language modules...")
        
        # Get the directory where language modules are stored
        languages_dir = os.path.join(os.path.dirname(__file__), "languages")
        if not os.path.exists(languages_dir):
            if logging:
                logging.log(LogLevel.Error, f"Languages directory not found: {languages_dir}")
            return
        
        # Look for Python files in the languages directory
        for filename in os.listdir(languages_dir):
            if filename.endswith('.py') and not filename.startswith('__'):
                module_name = filename[:-3]  # Remove .py extension
                try:
                    # Import the module dynamically
                    module = importlib.import_module(f"translations.languages.{module_name}")
                    if logging:
                        logging.log(LogLevel.Info, f"Loaded language module: {module_name}")
                except ImportError as e:
                    if logging:
                        logging.log(LogLevel.Error, f"Failed to load language module {module_name}: {e}")
    
    @classmethod
    def _map_system_lang_to_code(cls, system_lang: str, logger: Optional[Logger] = None) -> str:
        """Helper function to map system language to supported code and optionally log mapping"""
        if system_lang.startswith("es"):
            if logger:
                logger.log(LogLevel.Info, f"System language '{system_lang}' mapped to Spanish (es)")
            return "es"
        elif system_lang.startswith("pt"):
            if logger:
                logger.log(LogLevel.Info, f"System language '{system_lang}' mapped to Portuguese (pt)")
            return "pt"
        elif system_lang.startswith("fr"):
            if logger:
                logger.log(LogLevel.Info, f"System language '{system_lang}' mapped to French (fr)")
            return "fr"
        elif system_lang.startswith("id"):
            if logger:
                logger.log(LogLevel.Info, f"System language '{system_lang}' mapped to Indonesian (id)")
            return "id"
        elif system_lang.startswith("hi"):
            if logger:
                logger.log(LogLevel.Info, f"System language '{system_lang}' mapped to Hindi (hi)")
            return "hi"
        else:
            if logger:
                logger.log(LogLevel.Info, f"System language '{system_lang}' not supported, falling back to English (en)")
            return "en"
    
    @classmethod
    def get_translation(cls, logging: Optional[Logger] = None, lang: str = "en") -> Translation:
        """Load the language according to the selected language
        
        Args:
            logging: Optional logger for logging translation loading process
            lang: Language code ('en', 'es', 'pt', 'fr', 'id', 'hi', 'default')
                  'default' will use the system's $LANG environment variable
        
        Returns:
            Translation: Translation object for the selected language
        """
        # Make sure languages are loaded
        if not cls._registered_languages:
            cls.load_all_languages(logging)
        
        # Handle 'default' option by checking system's LANG environment variable
        if lang == "default":
            env_lang = os.environ.get("LANG")
            if env_lang is None:
                # No LANG env var set, fall back to English immediately
                system_lang_code = "en"
                if logging:
                    logging.log(LogLevel.Info, "Environment variable LANG not set, falling back to English")
            else:
                # LANG env var exists
                parts = env_lang.split("_")
                system_lang_code = parts[0].lower()
                if logging:
                    logging.log(LogLevel.Info, f"Using system language: {system_lang_code} from $LANG={env_lang}")
            lang = cls._map_system_lang_to_code(system_lang_code, logging)
        
        if logging:
            logging.log(LogLevel.Info, f"Using language: {lang}")
        
        # Get the language class and instantiate it
        language_class = cls._registered_languages.get(lang)
        if language_class is None:
            if logging:
                logging.log(LogLevel.Warning, f"Language '{lang}' not found, falling back to English")
            language_class = cls._registered_languages.get("en")
            # If even English is not found, raise an error
            if language_class is None:
                if logging:
                    logging.log(LogLevel.Error, "English language not found, this shouldn't happen!")
                raise ValueError("No languages registered, something is wrong with the setup")
        
        return language_class()