import os

from model.settings import GlobalSettings
from model.settings._base_settings import _BaseSettings

TEST_PREFERENCES_FILENAME = 'test_preferences.json'


class TestGlobalSettings:

    def setup_method(self):
        # Set up a GameSettings instance with some predefined settings
        self.global_settings = GlobalSettings(
            _BaseSettings(TEST_PREFERENCES_FILENAME,
                          {1: {'aliases': {'TestAlias': 'AliasedCommand'}, 'defaultvote': [True, 30]}}))

    def teardown_method(self):
        # Delete the preferences.json file after each test
        if os.path.exists(TEST_PREFERENCES_FILENAME):
            os.remove(TEST_PREFERENCES_FILENAME)

    def test_get_alias(self):
        assert self.global_settings.get_alias(1, 'TestAlias') == 'AliasedCommand'
        assert self.global_settings.get_alias(1, 'NonExistentAlias') is None

    def test_add_alias_new_player(self):
        self.global_settings.set_alias(2, 'NewAlias', "NewAliasedCommand")
        assert self.global_settings.get_alias(2, 'NewAlias') == "NewAliasedCommand"

    def test_add_alias_new_alias(self):
        self.global_settings.set_alias(1, 'NewAlias', "NewAliasedCommand")
        assert self.global_settings.get_alias(1, 'NewAlias') == "NewAliasedCommand"

    def test_add_alias_does_not_remove_old_alias(self):
        self.global_settings.set_alias(1, 'NewAlias', "NewAliasedCommand")
        assert self.global_settings.get_alias(1, 'TestAlias') == "AliasedCommand"

    def test_update_existing_alias(self):
        self.global_settings.set_alias(1, 'TestAlias', "NewAliasedCommand")
        assert self.global_settings.get_alias(1, 'TestAlias') == "NewAliasedCommand"

    def test_get_default_vote(self):
        assert self.global_settings.get_default_vote(1) == (True, 30)
        assert self.global_settings.get_default_vote(2) is None

    def test_set_default_vote_existing_user(self):
        self.global_settings.set_default_vote(1, False, 15)
        assert self.global_settings.get_default_vote(1) == (False, 15)

    def test_set_default_vote_new_user(self):
        self.global_settings.set_default_vote(2, False, 15)
        assert self.global_settings.get_default_vote(2) == (False, 15)

    def test_clear_default_vote(self):
        self.global_settings.clear_default_vote(1)
        assert self.global_settings.get_default_vote(1) is None

    def test_save_load(self):
        # Test saving and loading settings
        self.global_settings.save()
        loaded_settings = GlobalSettings.load(TEST_PREFERENCES_FILENAME)
        assert self.global_settings == loaded_settings
