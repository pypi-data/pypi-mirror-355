"""
Legacy theme converter for Textual themes.

This module handles conversion from legacy theme formats to our unified system.
"""

from typing import Dict, Any, Optional
import logging
import uuid

from textual.theme import Theme as TextualTheme

logger = logging.getLogger(__name__)


def convert_legacy_theme(theme_data: Dict[str, Any]) -> Optional[TextualTheme]:
    """
    Convert a legacy Textual theme format to a TextualTheme object.

    Args:
        theme_data: Dictionary with theme data in legacy format

    Returns:
        TextualTheme object or None if conversion failed
    """
    try:
        # Extract basic theme args
        theme_args = {
            "name": theme_data.get("name", f"legacy_theme_{uuid.uuid4().hex[:8]}"),
        }

        # Handle required fields
        if "primary" in theme_data:
            theme_args["primary"] = theme_data["primary"]
        else:
            logger.warning(
                "Legacy theme missing required 'primary' color, using default"
            )
            theme_args["primary"] = "#FFFFFF"

        # Add dark mode
        theme_args["dark"] = theme_data.get("dark", True)

        # Add other color fields
        color_fields = [
            "secondary",
            "background",
            "surface",
            "panel",
            "warning",
            "error",
            "success",
            "accent",
        ]

        for field in color_fields:
            if field in theme_data:
                theme_args[field] = theme_data[field]

        # Handle theme variables
        if "variables" in theme_data:
            theme_args["variables"] = theme_data["variables"]

        # Create the Textual theme
        return TextualTheme(**theme_args)

    except Exception as e:
        logger.error(f"Error converting legacy theme: {e}")
        return None


def convert_textual_to_unified(theme: TextualTheme) -> Dict[str, Any]:
    """
    Convert a Textual theme to a unified theme format dict.

    Args:
        theme: Textual theme to convert

    Returns:
        Dictionary in unified theme format
    """
    # Create base theme data
    unified_data = {
        "name": theme.name.upper(),
        "display_name": theme.name.title(),
        "description": f"Converted from Textual theme '{theme.name}'",
        "dark_mode": getattr(theme, "dark", True),
        "colors": {},
    }

    # Convert primary colors
    if hasattr(theme, "primary"):
        unified_data["colors"]["primary"] = {"hex": theme.primary}

    if hasattr(theme, "secondary"):
        unified_data["colors"]["secondary"] = {"hex": theme.secondary}

    if hasattr(theme, "accent"):
        unified_data["colors"]["accent"] = {"hex": theme.accent}

    # Convert background colors
    if hasattr(theme, "background"):
        unified_data["colors"]["background"] = {"hex": theme.background}

    if hasattr(theme, "surface"):
        unified_data["colors"]["surface"] = {"hex": theme.surface}

    if hasattr(theme, "panel"):
        unified_data["colors"]["panel"] = {"hex": theme.panel}

    # Convert status colors
    if hasattr(theme, "success"):
        unified_data["colors"]["success"] = {"hex": theme.success}

    if hasattr(theme, "warning"):
        unified_data["colors"]["warning"] = {"hex": theme.warning}

    if hasattr(theme, "error"):
        unified_data["colors"]["error"] = {"hex": theme.error}

    # Convert variables
    if hasattr(theme, "variables"):
        vars_dict = theme.variables.copy() if theme.variables else {}

        # Extract text colors from variables
        if "text" in vars_dict:
            unified_data["colors"]["text"] = {"hex": vars_dict.pop("text")}

        if "text-muted" in vars_dict:
            unified_data["colors"]["text_muted"] = {"hex": vars_dict.pop("text-muted")}

        # Handle border color
        if "border-color" in vars_dict:
            unified_data["colors"]["border"] = {"hex": vars_dict.pop("border-color")}

    return unified_data
