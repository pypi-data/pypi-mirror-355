"""
Settings screen for Aurras TUI.
"""

from pathlib import Path
from typing import Dict, Any

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, Button, Switch, Input, Select
from textual.binding import Binding

from ..themes.theme_manager import BUILTIN_THEMES
from ...themes.manager import get_theme, get_available_themes, set_current_theme
from ...core.settings import load_settings, save_settings, Settings
from ...core.settings.updater import SettingsUpdater


class SettingsScreen(Screen):
    """Screen for configuring Aurras settings."""

    BINDINGS = [
        Binding("escape", "app.pop_screen", "Back"),
        Binding("s", "save_settings", "Save"),
        Binding("r", "reset_settings", "Reset"),
        Binding("f", "factory_reset", "Factory Reset", show=False),
    ]

    def compose(self) -> ComposeResult:
        """Compose the settings screen layout."""
        yield Header()

        with Container(id="settings-container"):
            yield Static("Settings", id="settings-title", classes="panel-title")

            with Vertical(id="settings-sections"):
                # Theme settings - put this first for visibility
                with Container(id="theme-settings", classes="settings-section"):
                    yield Static("Theme", classes="settings-section-title")

                    with Horizontal(classes="setting-row"):
                        yield Static("Theme:", classes="setting-label")
                        # Get themes from the themes system and builtin TUI themes
                        all_themes = list(
                            set(get_available_themes()) | set(BUILTIN_THEMES.keys())
                        )
                        yield Select(
                            [(theme, theme) for theme in sorted(all_themes)],
                            value=self.app.current_theme_name
                            if hasattr(self.app, "current_theme_name")
                            else "galaxy",
                            id="theme",
                        )

                    with Horizontal(classes="setting-row"):
                        yield Static("Dark Mode:", classes="setting-label")
                        yield Switch(value=True, id="dark-mode")

                # Playback settings
                with Container(id="playback-settings", classes="settings-section"):
                    yield Static("Playback", classes="settings-section-title")

                    with Horizontal(classes="setting-row"):
                        yield Static("Show Video:", classes="setting-label")
                        yield Switch(
                            value=self._get_setting_value(
                                "appearance_settings.display_video"
                            )
                            == "yes",
                            id="show-video",
                        )

                    with Horizontal(classes="setting-row"):
                        yield Static("Show Lyrics:", classes="setting-label")
                        yield Switch(
                            value=self._get_setting_value(
                                "appearance_settings.display_lyrics"
                            )
                            == "yes",
                            id="show-lyrics",
                        )

                    with Horizontal(classes="setting-row"):
                        yield Static("Max Volume:", classes="setting-label")
                        yield Input(
                            value=self._get_setting_value("maximum_volume", "130"),
                            id="max-volume",
                        )

                    with Horizontal(classes="setting-row"):
                        yield Static("Default Volume:", classes="setting-label")
                        yield Input(
                            value=self._get_setting_value("default_volume", "100"),
                            id="default-volume",
                        )

                # Download settings
                with Container(id="download-settings", classes="settings-section"):
                    yield Static("Downloads", classes="settings-section-title")

                    with Horizontal(classes="setting-row"):
                        yield Static("Download Path:", classes="setting-label")
                        yield Input(
                            value=self._get_setting_value(
                                "download_path", "~/Music/Aurras"
                            ),
                            id="download-path",
                        )

                    with Horizontal(classes="setting-row"):
                        yield Static("Download Format:", classes="setting-label")
                        yield Select(
                            [("MP3", "mp3"), ("FLAC", "flac"), ("WAV", "wav")],
                            value=self._get_setting_value("download_format", "mp3"),
                            id="download-format",
                        )

                    with Horizontal(classes="setting-row"):
                        yield Static("Download Bitrate:", classes="setting-label")
                        yield Select(
                            [
                                ("Auto", "auto"),
                                ("128kbps", "128"),
                                ("192kbps", "192"),
                                ("256kbps", "256"),
                                ("320kbps", "320"),
                            ],
                            value=self._get_setting_value("download_bitrate", "auto"),
                            id="download-bitrate",
                        )

                # Backup settings
                with Container(id="backup-settings", classes="settings-section"):
                    yield Static("Backup", classes="settings-section-title")

                    with Horizontal(classes="setting-row"):
                        yield Static("Enable Backups:", classes="setting-label")
                        yield Switch(
                            value=self._get_setting_value("backup.enable_backups")
                            == "yes",
                            id="enable-backups",
                        )

                    with Horizontal(classes="setting-row"):
                        yield Static("Auto Backup:", classes="setting-label")
                        yield Switch(
                            value=self._get_setting_value("backup.automatic_backups")
                            == "yes",
                            id="auto-backup",
                        )

                    with Horizontal(classes="setting-row"):
                        yield Static("Backup Interval (days):", classes="setting-label")
                        yield Input(
                            value=self._get_setting_value(
                                "backup.backup_interval_days", "7"
                            ),
                            id="backup-frequency",
                        )

                    with Horizontal(classes="setting-row"):
                        yield Static("Backup Location:", classes="setting-label")
                        yield Input(
                            value=self._get_setting_value(
                                "backup.backup_location", "default"
                            ),
                            id="backup-location",
                        )

                # System settings
                with Container(id="system-settings", classes="settings-section"):
                    yield Static("System", classes="settings-section-title")

                    with Horizontal(classes="setting-row"):
                        yield Static("Hardware Acceleration:", classes="setting-label")
                        yield Switch(
                            value=self._get_setting_value(
                                "enable_hardware_acceleration"
                            )
                            == "yes",
                            id="hw-accel",
                        )

                    with Horizontal(classes="setting-row"):
                        yield Static("Media Keys Support:", classes="setting-label")
                        yield Switch(
                            value=self._get_setting_value("enable_media_keys") == "yes",
                            id="media-keys",
                        )

                    with Horizontal(classes="setting-row"):
                        yield Static("Auto Updates:", classes="setting-label")
                        yield Switch(
                            value=self._get_setting_value("enable_auto_updates")
                            == "yes",
                            id="auto-updates",
                        )

                    with Horizontal(classes="setting-row"):
                        yield Static("Update Check (hours):", classes="setting-label")
                        yield Input(
                            value=self._get_setting_value("update_check_hours", "168"),
                            id="update-interval",
                        )

            with Horizontal(id="settings-actions"):
                yield Button("Save", id="save-settings", variant="primary")
                yield Button("Reset", id="reset-settings")
                yield Button("Factory Reset", id="factory-reset")

        yield Footer()

    def on_mount(self):
        """Handle mounting of the settings screen."""
        self.app.sub_title = "Settings & Preferences"
        self._load_current_settings()

    def _get_setting_value(self, key: str, default: str = "") -> str:
        """
        Get a setting value from the current settings.

        Args:
            key: The setting key in snake_case format
            default: Default value if setting is not found

        Returns:
            The setting value as a string
        """
        try:
            settings = load_settings()

            # Access nested settings using dot notation
            parts = key.split(".")
            current = settings

            for part in parts:
                if hasattr(current, part):
                    current = getattr(current, part)
                else:
                    return default

            return str(current)
        except Exception:
            return default

    def _load_current_settings(self):
        """Load current settings into the form."""
        try:
            # Load theme setting
            if hasattr(self.app, "current_theme_name"):
                theme_select = self.query_one("#theme", Select)
                theme_select.value = self.app.current_theme_name

            # Load other settings
            settings = load_settings()

            # We already set defaults in compose, but this is a backup
            # in case we need to refresh the settings screen

        except Exception as e:
            self.notify(f"Error loading settings: {e}", severity="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        button_id = event.button.id

        if button_id == "save-settings":
            self.action_save_settings()

        elif button_id == "reset-settings":
            self.action_reset_settings()

        elif button_id == "factory-reset":
            self.action_factory_reset()

    def on_select_changed(self, event):
        """Handle select field changes."""
        if event.select.id == "theme":
            self._preview_theme(event.select.value)

    def _preview_theme(self, theme_name):
        """Preview a theme when selected."""
        if hasattr(self.app, "switch_theme") and theme_name in BUILTIN_THEMES:
            self.app.switch_theme(theme_name)
            self.notify(f"Theme set to {theme_name}")

    def action_save_settings(self) -> None:
        """Save current settings."""
        try:
            settings = load_settings()

            # Read and save theme settings
            theme_select = self.query_one("#theme", Select)
            theme_name = theme_select.value

            # Update appearance settings
            updater = SettingsUpdater("appearance_settings.theme")
            updater.update_directly(theme_name)

            if hasattr(self.app, "switch_theme"):
                self.app.switch_theme(theme_name)

            # Update other settings
            self._save_switch_setting("show-video", "appearance_settings.display_video")
            self._save_switch_setting(
                "show-lyrics", "appearance_settings.display_lyrics"
            )
            self._save_input_setting("max-volume", "maximum_volume")
            self._save_input_setting("default-volume", "default_volume")
            self._save_input_setting("download-path", "download_path")
            self._save_select_setting("download-format", "download_format")
            self._save_select_setting("download-bitrate", "download_bitrate")
            self._save_switch_setting("enable-backups", "backup.enable_backups")
            self._save_switch_setting("auto-backup", "backup.automatic_backups")
            self._save_input_setting("backup-frequency", "backup.backup_interval_days")
            self._save_input_setting("backup-location", "backup.backup_location")
            self._save_switch_setting("hw-accel", "enable_hardware_acceleration")
            self._save_switch_setting("media-keys", "enable_media_keys")
            self._save_switch_setting("auto-updates", "enable_auto_updates")
            self._save_input_setting("update-interval", "update_check_hours")

            self.notify("Settings saved successfully")

        except Exception as e:
            self.notify(f"Error saving settings: {e}", severity="error")

    def _save_switch_setting(self, widget_id: str, setting_key: str) -> None:
        """Save a switch widget value to a setting."""
        try:
            widget = self.query_one(f"#{widget_id}", Switch)
            value = "yes" if widget.value else "no"

            updater = SettingsUpdater(setting_key)
            updater.update_directly(value)
        except Exception as e:
            self.notify(f"Error saving {setting_key}: {e}", severity="error")

    def _save_input_setting(self, widget_id: str, setting_key: str) -> None:
        """Save an input widget value to a setting."""
        try:
            widget = self.query_one(f"#{widget_id}", Input)

            updater = SettingsUpdater(setting_key)
            updater.update_directly(widget.value)
        except Exception as e:
            self.notify(f"Error saving {setting_key}: {e}", severity="error")

    def _save_select_setting(self, widget_id: str, setting_key: str) -> None:
        """Save a select widget value to a setting."""
        try:
            widget = self.query_one(f"#{widget_id}", Select)

            updater = SettingsUpdater(setting_key)
            updater.update_directly(widget.value)
        except Exception as e:
            self.notify(f"Error saving {setting_key}: {e}", severity="error")

    def action_reset_settings(self) -> None:
        """Reset settings to their saved values."""
        self._load_current_settings()
        self.notify("Settings have been reset to saved values")

    def action_factory_reset(self) -> None:
        """Reset all settings to factory defaults."""
        try:
            # Create default settings
            default_settings = Settings()
            save_settings(default_settings)

            # Reset the form
            self._load_current_settings()

            # Theme reset
            theme_select = self.query_one("#theme", Select)
            theme_select.value = "galaxy"
            if hasattr(self.app, "switch_theme"):
                self.app.switch_theme("galaxy")

            self.notify("All settings have been reset to factory defaults")
        except Exception as e:
            self.notify(f"Error resetting settings: {e}", severity="error")
