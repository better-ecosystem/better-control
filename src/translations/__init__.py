"""
Translation module for Better Control

This module handles loading and managing translations for the application.
Languages are stored in separate files within the languages directory.
"""

from .translation_manager import TranslationManager, Translation

__all__ = ['TranslationManager', 'Translation']