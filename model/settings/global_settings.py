import json

_SETTINGS_FILENAME = '../preferences.json'


class GlobalSettings:
    _settings: dict[int, dict[str, any]]
    """Class to store and manage game settings.  """

    def __init__(self, settings):
        self._settings = settings

    # ==============================
    # Aliases
    # ==============================
    def get_alias(self, player_id: int, alias: str):
        """Get an alias for a player."""
        aliases: dict[str, str] = self._get_settings(player_id, "aliases") or {}
        return aliases.get(alias)

    def set_alias(self, player_id: int, alias: str, command: str):
        """Set or update an alias for a player, merging with existing aliases."""
        # Retrieve current aliases or initialize an empty dictionary if none exist
        current_aliases = self._get_settings(player_id, "aliases") or {}
        # Add or update the new alias
        current_aliases[alias] = command
        # Update the player's settings with the modified aliases dictionary
        self._update_settings(player_id, {'aliases': current_aliases})

    # ==============================
    # Default Votes
    # ==============================

    def get_default_vote(self, player_id: int) -> tuple[bool, int]:
        """Get the default vote for a player as a tuple if one is set.  Returns None if none is set."""
        settings = self._get_settings(player_id, 'defaultvote')
        return (bool(settings[0]), int(settings[1])) if settings else None

    def set_default_vote(self, player_id: int, default_vote: bool, duration: int):
        """Set the default vote for a player."""
        self._update_settings(player_id, {'defaultvote': [bool(default_vote), int(duration)]})

    def clear_default_vote(self, player_id: int):
        """Set the default vote for a player."""
        self._clear_setting(player_id, 'defaultvote')

    # ==============================
    # Generic settings methods
    # ==============================

    def _update_settings(self, player_id: int, dict_to_merge: dict):
        """Update settings for a specific player, merging with existing settings if present."""
        if player_id in self._settings:
            # Merge existing settings with new settings
            self._settings[player_id].update(dict_to_merge)
        else:
            # Add new settings for the player
            self._settings[player_id] = dict_to_merge

    def _get_settings(self, player_id: int, setting_name: str):
        """Get a specific setting for a player."""
        return self._settings.get(player_id, {}).get(setting_name)

    def _clear_setting(self, player_id: int, setting_name: str):
        """Remove a specific setting for a player."""
        if player_id in self._settings:
            self._settings[player_id].pop(setting_name, None)

    # ==============================
    # Serialization/Deserialization
    # ==============================

    def save(self):
        """Save settings to a JSON file."""
        with open(_SETTINGS_FILENAME, 'w') as f:
            json.dump(self._settings, f, indent=2)

    @classmethod
    def load(cls):
        """Load settings from a JSON file and return a new GameSettings object."""
        try:
            with open(_SETTINGS_FILENAME, 'r') as f:
                settings_data = json.load(f)
        except FileNotFoundError:
            settings_data = {}

        # Convert keys from string to int
        normalized_data = {int(k): v for k, v in settings_data.items()}
        return cls(normalized_data)
