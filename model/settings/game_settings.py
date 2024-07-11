import json

_SETTINGS_FILENAME = 'settings.json'


class GameSettings:
    _settings: dict[int, dict[str, any]]
    """Class to store and manage game settings.  """

    def __init__(self):
        self._settings = {}

    # ==============================
    # ST Room Settings
    # ==============================
    def set_st_channel(self, player_id: int, channel_id: int):
        """Set the channel ID for the ST room for a specific player."""
        self._update_settings(player_id, {"st_channel": channel_id})

    def get_st_channel(self, player_id: int):
        """Get the channel ID for the ST room for a specific player."""
        return self._get_settings(player_id, "st_channel")

    def clear_st_channel(self, player_id: int):
        """Clear the channel ID for the ST room for a specific player."""
        self._clear_setting(player_id, "st_channel")

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

    def save_to_file(self):
        """Save settings to a JSON file."""
        with open(_SETTINGS_FILENAME, 'w') as f:
            json.dump(self._settings, f)

    @staticmethod
    def load_from_file():
        """Load settings from a JSON file and return a new GameSettings object."""
        with open(_SETTINGS_FILENAME, 'r') as f:
            settings_data = json.load(f)
        # Convert keys from string to int
        normalized_data = {int(k): v for k, v in settings_data.items()}
        new_game_settings = GameSettings()
        new_game_settings._settings = normalized_data
        return new_game_settings
