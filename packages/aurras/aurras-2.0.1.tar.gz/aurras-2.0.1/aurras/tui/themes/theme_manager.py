"""
Theme management system for Aurras TUI.

This module provides integration with the unified theme system
and maintains backward compatibility with the Textual theme mechanism.
"""

from pathlib import Path
from typing import Dict, Optional, NamedTuple
import logging
import yaml

from textual.theme import Theme as TextualTheme

from aurras.themes.tui_adapter import get_available_textual_themes

log = logging.getLogger("aurras.themes")

# Re-export the functionality from the main theme system
BUILTIN_THEMES: Dict[str, TextualTheme] = get_available_textual_themes()


class UserThemeLoadResult(NamedTuple):
    """Result of loading user themes."""

    themes: Dict[str, TextualTheme]
    failures: list[tuple[Path, Exception]]


def load_user_themes(theme_dir: Path) -> UserThemeLoadResult:
    """
    Load user themes from a directory.

    Args:
        theme_dir: Directory containing theme YAML files

    Returns:
        UserThemeLoadResult with loaded themes and any failures
    """
    themes = {}
    failures = []

    if not theme_dir.exists():
        return UserThemeLoadResult(themes, failures)

    # Load YAML theme files
    for extension in ["yaml", "yml"]:
        for path in theme_dir.glob(f"*.{extension}"):
            try:
                theme = load_user_theme(path)
                if theme:
                    themes[theme.name] = theme
            except Exception as e:
                failures.append((path, e))

    return UserThemeLoadResult(themes, failures)


def load_user_theme(path: Path) -> Optional[TextualTheme]:
    """
    Load a user theme from a file.

    Args:
        path: Path to the theme YAML file

    Returns:
        Textual theme or None if loading failed

    Raises:
        Various exceptions if the theme file is invalid
    """
    if not path.exists():
        return None

    try:
        with open(path, "r") as f:
            theme_data = yaml.safe_load(f)
    except Exception as e:
        log.error(f"Error loading theme {path}: {e}")
        raise

    if not isinstance(theme_data, dict):
        raise ValueError(f"Theme file {path} must contain a YAML object")

    if "name" not in theme_data:
        raise ValueError(f"Theme file {path} must contain a 'name' field")

    try:
        # If the theme has a compatible format with our unified system, convert it
        if all(k in theme_data for k in ["name", "display_name", "description"]):
            # This looks like a unified theme format - convert it
            from aurras.themes.theme_manager import ThemeDefinition, ThemeColor

            # Extract color data
            colors = {}
            if "colors" in theme_data:
                for name, value in theme_data["colors"].items():
                    if isinstance(value, dict) and "hex" in value:
                        colors[name] = ThemeColor(
                            hex=value["hex"], gradient=value.get("gradient")
                        )
                    elif isinstance(value, str):
                        colors[name] = ThemeColor(hex=value)

            # Create a theme definition
            unified_theme = ThemeDefinition(
                name=theme_data["name"],
                display_name=theme_data["display_name"],
                description=theme_data["description"],
                dark_mode=theme_data.get("dark_mode", True),
                **colors,
            )

            # Convert to Textual theme
            from aurras.themes.tui_adapter import get_textual_theme

            return get_textual_theme(unified_theme.name)
        else:
            # Handle legacy Textual theme format
            from aurras.tui.themes.legacy_converter import convert_legacy_theme

            return convert_legacy_theme(theme_data)

    except Exception as e:
        log.error(f"Error parsing theme {path}: {e}")
        raise
