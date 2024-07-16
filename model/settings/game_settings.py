from __future__ import annotations

from dataclasses import dataclass

from ._base_settings import _BaseSettings

_SETTINGS_FILENAME = 'settings.json'


@dataclass
class GameSettings:
    _settings: _BaseSettings
    """Class to store and manage game settings.  """

    def __init__(self, settings=None):
        self._settings = settings

    # ==============================
    # ST Room Settings
    # ==============================
    def set_st_channel(self, player_id: int, channel_id: int) -> None:
        """Set the channel ID for the ST room for a specific player."""
        self._settings.update_settings(player_id, {"st_channel": channel_id})

    def get_st_channel(self, player_id: int) -> int:
        """Get the channel ID for the ST room for a specific player."""
        return self._settings.get_settings(player_id, "st_channel")

    def clear_st_channel(self, player_id: int) -> None:
        """Clear the channel ID for the ST room for a specific player."""
        self._settings.clear_setting(player_id, "st_channel")

    # ==============================
    # Serialization/Deserialization
    # ==============================

    def save(self) -> None:
        """Save settings to a JSON file."""
        self._settings.save()

    @classmethod
    def load(cls) -> GameSettings:
        """Load settings from a JSON file and return a new GameSettings object."""
        return cls(_BaseSettings.load(_SETTINGS_FILENAME))
