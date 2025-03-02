import os

from model.settings._base_settings import _BaseSettings
from model.settings.game_settings import GameSettings

TEST_SETTINGS_FILENAME = 'test_settings.json'


class TestGameSettings:

    def setup_method(self):
        # Set up a GameSettings instance with some predefined settings
        self.game_settings = GameSettings(
            _BaseSettings(TEST_SETTINGS_FILENAME, {1: {"st_channel": 12345}}))

    def teardown_method(self):
        # Delete the preferences.json file after each test
        if os.path.exists(TEST_SETTINGS_FILENAME):
            os.remove(TEST_SETTINGS_FILENAME)

    def test_get_st_channel(self):
        assert self.game_settings.get_st_channel(1) == 12345
        assert self.game_settings.get_st_channel(2) is None

    def test_set_st_channel_new_player(self):
        self.game_settings.set_st_channel(2, 67890)
        assert self.game_settings.get_st_channel(2) == 67890

    def test_set_st_channel_existing_player(self):
        self.game_settings.set_st_channel(1, 67890)
        assert self.game_settings.get_st_channel(1) == 67890

    def test_get_unset_st_channel(self):
        assert self.game_settings.get_st_channel(2) is None

    def test_clear_st_channel(self):
        self.game_settings.clear_st_channel(1)
        assert self.game_settings.get_st_channel(1) is None

    def test_save_and_load(self):
        # Test saving and loading settings
        self.game_settings.save()
        loaded_settings = GameSettings.load(TEST_SETTINGS_FILENAME)
        assert self.game_settings == loaded_settings
