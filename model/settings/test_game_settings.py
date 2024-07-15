import unittest

from model.settings import game_settings
from model.settings._base_settings import _BaseSettings
from model.settings.game_settings import GameSettings

import os


class TestGameSettings(unittest.TestCase):

    def setUp(self):
        # Set up a GameSettings instance with some predefined settings
        self.game_settings = GameSettings(
            _BaseSettings(game_settings._SETTINGS_FILENAME, {1: {"st_channel": 12345}}))

    def tearDown(self):
        # Delete the preferences.json file after each test
        if os.path.exists(game_settings._SETTINGS_FILENAME):
            os.remove(game_settings._SETTINGS_FILENAME)

    def test_get_st_channel(self):
        self.assertEqual(self.game_settings.get_st_channel(1), 12345)
        self.assertIsNone(self.game_settings.get_st_channel(2))

    def test_set_st_channel_new_player(self):
        self.game_settings.set_st_channel(2, 67890)
        self.assertEqual(self.game_settings.get_st_channel(2), 67890)

    def test_set_st_channel_existing_player(self):
        self.game_settings.set_st_channel(1, 67890)
        self.assertEqual(self.game_settings.get_st_channel(1), 67890)

    def test_get_unset_st_channel(self):
        self.assertIsNone(self.game_settings.get_st_channel(2))

    def test_clear_st_channel(self):
        self.game_settings.clear_st_channel(1)
        self.assertIsNone(self.game_settings.get_st_channel(1))

    def test_save_and_load(self):
        # Test saving and loading settings
        self.game_settings.save()
        loaded_settings = GameSettings.load()
        self.assertEqual(self.game_settings, loaded_settings)


if __name__ == '__main__':
    unittest.main()
