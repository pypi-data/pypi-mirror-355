"""
Theme handling for the TUI interface.

This module provides integration with the unified theme system
defined in the aurras.themes package.
"""

from typing import Dict, Optional
import logging

from textual.theme import Theme as TextualTheme
from textual.widgets.text_area import TextAreaTheme

from aurras.themes import (
    get_theme,
    get_available_themes,
    get_current_theme,
    set_current_theme,
    ThemeDefinition,
)
from aurras.themes.tui_adapter import (
    get_textual_theme,
    get_available_textual_themes,
    get_text_area_theme,
)

logger = logging.getLogger(__name__)

# Re-export the main theme functions and classes
__all__ = [
    "get_textual_theme",
    "get_available_textual_themes",
    "get_text_area_theme",
    "get_theme",
    "get_available_themes",
    "get_current_theme",
    "set_current_theme",
    "BUILTIN_THEMES",
]

# Map of built-in textual themes - this is just a proxy to the unified system
BUILTIN_THEMES: Dict[str, TextualTheme] = get_available_textual_themes()
