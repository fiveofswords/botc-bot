import os
import unittest

from model.settings import GlobalSettings, global_settings
from model.settings._base_settings import _BaseSettings


class TestGlobalSettings(unittest.TestCase):

    def setUp(self):
        # Set up a GameSettings instance with some predefined settings
        self.global_settings = GlobalSettings(
            _BaseSettings(global_settings._SETTINGS_FILENAME,
                          {1: {'aliases': {'TestAlias': 'AliasedCommand'}, 'defaultvote': [True, 30]}}))

    def tearDown(self):
        # Delete the preferences.json file after each test
        if os.path.exists(global_settings._SETTINGS_FILENAME):
            os.remove(global_settings._SETTINGS_FILENAME)

    def test_get_alias(self):
        self.assertEqual(self.global_settings.get_alias(1, 'TestAlias'), 'AliasedCommand')
        self.assertIsNone(self.global_settings.get_alias(1, 'NonExistentAlias'))

    def test_add_alias_new_player(self):
        self.global_settings.set_alias(2, 'NewAlias', "NewAliasedCommand")
        self.assertEqual(self.global_settings.get_alias(2, 'NewAlias'), "NewAliasedCommand")

    def test_add_alias_new_alias(self):
        self.global_settings.set_alias(1, 'NewAlias', "NewAliasedCommand")
        self.assertEqual(self.global_settings.get_alias(1, 'NewAlias'), "NewAliasedCommand")

    def test_add_alias_does_not_remove_old_alias(self):
        self.global_settings.set_alias(1, 'NewAlias', "NewAliasedCommand")
        self.assertEqual(self.global_settings.get_alias(1, 'TestAlias'), "AliasedCommand")

    def test_update_existing_alias(self):
        self.global_settings.set_alias(1, 'TestAlias', "NewAliasedCommand")
        self.assertEqual(self.global_settings.get_alias(1, 'TestAlias'), "NewAliasedCommand")

    def test_get_default_vote(self):
        self.assertEqual(self.global_settings.get_default_vote(1), (True, 30))
        self.assertIsNone(self.global_settings.get_default_vote(2))

    def test_set_default_vote_existing_user(self):
        self.global_settings.set_default_vote(1, False, 15)
        self.assertEqual(self.global_settings.get_default_vote(1), (False, 15))

    def test_set_default_vote_new_user(self):
        self.global_settings.set_default_vote(2, False, 15)
        self.assertEqual(self.global_settings.get_default_vote(2), (False, 15))

    def test_clear_default_vote(self):
        self.global_settings.clear_default_vote(1)
        self.assertIsNone(self.global_settings.get_default_vote(1))

    def test_save_load(self):
        # Test saving and loading settings
        self.global_settings.save()
        loaded_settings = GlobalSettings.load()
        self.assertEqual(self.global_settings, loaded_settings)


if __name__ == '__main__':
    unittest.main()
