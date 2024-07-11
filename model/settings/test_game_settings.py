import unittest
from model.settings.game_settings import GameSettings
import model.settings.game_settings
import os


class TestGameSettings(unittest.TestCase):

    def setUp(self):
        self.original_filename = model.settings.game_settings._SETTINGS_FILENAME
        model.settings.game_settings._SETTINGS_FILENAME = 'test_settings.json'
        self.game_settings = GameSettings()
        self.test_filename = model.settings.game_settings._SETTINGS_FILENAME

    def tearDown(self):
        if os.path.exists(self.test_filename):
            os.remove(self.test_filename)
        model.settings.game_settings._SETTINGS_FILENAME = self.original_filename

    def test_init(self):
        self.assertDictEqual(self.game_settings._settings, {})

    def test_set_st_channel(self):
        self.game_settings.set_st_channel(1, 12345)
        self.assertEqual(self.game_settings._settings[1], {"st_channel": 12345})

    def test_get_st_channel(self):
        self.game_settings._settings[1] = {"st_channel": 12345}
        self.assertEqual(self.game_settings.get_st_channel(1), 12345)

    def test_clear_st_channel(self):
        self.game_settings._settings[1] = {"st_channel": 12345}
        self.game_settings.clear_st_channel(1)
        self.assertNotIn("st_channel", self.game_settings._settings[1])

    def test_update_settings_update_setting(self):
        self.game_settings._update_settings(1, {"volume": 50})
        self.game_settings._update_settings(1, {"volume": 100})
        self.assertEqual(self.game_settings._settings[1], {"volume": 100})

    def test_update_settings_additional_setting(self):
        self.game_settings._update_settings(1, {"volume": 50})
        self.game_settings._update_settings(1, {"surface_area": 25})
        self.assertEqual(self.game_settings._settings[1], {"volume": 50, "surface_area": 25})

    def test_save_and_load(self):
        self.game_settings.set_st_channel(1, 12345)
        self.game_settings.save_to_file()
        loaded_settings = GameSettings.load_from_file()
        self.assertEqual(self.game_settings._settings, loaded_settings._settings)


if __name__ == '__main__':
    unittest.main()
