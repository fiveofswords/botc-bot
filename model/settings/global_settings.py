from __future__ import annotations

from dataclasses import dataclass

from ._base_settings import _BaseSettings

_SETTINGS_FILENAME = '../preferences.json'


@dataclass
class GlobalSettings:
    _settings: _BaseSettings
    """Class to store and manage game settings.  """

    def __init__(self, settings):
        self._settings = settings

    # ==============================
    # Aliases
    # ==============================
    def get_alias(self, player_id: int, alias: str):
        """Get an alias for a player."""
        aliases: dict[str, str] = self._settings.get_settings(player_id, "aliases") or {}
        return aliases.get(alias)

    def set_alias(self, player_id: int, alias: str, command: str) -> GlobalSettings:
        """Set or update an alias for a player, merging with existing aliases."""
        # Retrieve current aliases or initialize an empty dictionary if none exist
        current_aliases = self._settings.get_settings(player_id, "aliases") or {}
        # Add or update the new alias
        current_aliases[alias] = command
        # Update the player's settings with the modified aliases dictionary
        self._settings.update_settings(player_id, {'aliases': current_aliases})
        return self

    # ==============================
    # Default Votes
    # ==============================

    def get_default_vote(self, player_id: int) -> tuple[bool, int]:
        """Get the default vote for a player as a tuple if one is set.  Returns None if none is set."""
        settings = self._settings.get_settings(player_id, 'defaultvote')
        return (bool(settings[0]), int(settings[1])) if settings else None

    def set_default_vote(self, player_id: int, default_vote: bool, duration: int) -> GlobalSettings:
        """Set the default vote for a player."""
        self._settings.update_settings(player_id, {'defaultvote': [bool(default_vote), int(duration)]})
        return self

    def clear_default_vote(self, player_id: int) -> GlobalSettings:
        """Set the default vote for a player."""
        self._settings.clear_setting(player_id, 'defaultvote')
        return self

    # ==============================
    # Serialization/Deserialization
    # ==============================

    def save(self) -> GlobalSettings:
        """Save settings to a JSON file."""
        self._settings.save()
        return self

    @classmethod
    def load(cls):
        """Load settings from a JSON file and return a new GameSettings object."""
        return cls(_BaseSettings.load(_SETTINGS_FILENAME))
