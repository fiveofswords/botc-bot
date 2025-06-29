from __future__ import annotations

import json
from dataclasses import dataclass


@dataclass
class _BaseSettings:
    _filename: str
    _settings: dict[int, dict[str, any]]

    def __init__(self, filename, settings):
        self._filename = filename
        self._settings = settings

    # ==============================
    # Generic settings methods
    # ==============================
    def update_settings(self, player_id: int, dict_to_merge: dict):
        self._settings[player_id] = self._settings.get(player_id, {})
        self._settings[player_id].update(dict_to_merge)

    def get_settings(self, player_id: int, setting_name: str):
        return self._settings.get(player_id, {}).get(setting_name)

    def clear_setting(self, player_id: int, setting_name: str):
        player_settings = self._settings.get(player_id)
        if player_settings:
            player_settings.pop(setting_name, None)

    # ==============================
    # Serialization/Deserialization
    # ==============================
    def save(self):
        with open(self._filename, 'w') as f:
            json.dump(self._settings, f, indent=2)

    @classmethod
    def load(cls, filename) -> _BaseSettings:
        try:
            with open(filename, 'r') as f:
                settings_data = json.load(f)
        except FileNotFoundError:
            settings_data = {}
        # Convert keys from string to int
        normalized_data = {int(k): v for k, v in settings_data.items()}
        return cls(filename, normalized_data)
