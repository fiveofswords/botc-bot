"""
Tests for settings functionality in the Blood on the Clocktower bot.

These tests focus on the settings classes and their behaviors.
"""

import json
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest
import pytest_asyncio

from model.settings.game_settings import GameSettings
from model.settings.global_settings import GlobalSettings


@pytest_asyncio.fixture
async def setup_temp_files():
    """Set up temporary files for settings tests."""
    # Create temporary directories for settings files
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create game settings file
        game_settings_path = os.path.join(temp_dir, "game_settings.json")
        game_settings = {
            "st_channels": {
                "1": 101,
                "2": 102,
                "3": 103
            },
            "seating_channel": 201,
            "default_whisper_mode": "neighbors"
        }
        with open(game_settings_path, "w") as f:
            json.dump(game_settings, f)

        # Create global settings file
        global_settings_path = os.path.join(temp_dir, "global_settings.json")
        global_settings = {
            "default_votes": {
                "1": {"vote": True, "timeout": 300},
                "2": {"vote": False, "timeout": 600}
            }
        }
        with open(global_settings_path, "w") as f:
            json.dump(global_settings, f)

        # Return paths for tests to use
        yield {
            "game_settings_path": game_settings_path,
            "global_settings_path": global_settings_path
        }


@pytest.mark.asyncio
async def test_game_settings_load(setup_temp_files):
    """Test loading game settings from file."""
    # Patch the _SETTINGS_FILENAME constant
    with patch('model.settings._base_settings._BaseSettings.load') as mock_load:
        # Set up mock return
        mock_settings = MagicMock()
        mock_settings.get_settings.side_effect = lambda player_id, setting: {
            (1, "st_channel"): 101,
            (2, "st_channel"): 102,
            (3, "st_channel"): 103,
        }.get((player_id, setting))
        mock_load.return_value = mock_settings

        # Load the settings
        settings = GameSettings.load()

        # Verify settings were loaded correctly
        assert settings.get_st_channel(1) == 101
        assert settings.get_st_channel(2) == 102
        assert settings.get_st_channel(3) == 103

        # Verify non-existent user returns None
        assert settings.get_st_channel(4) is None


@pytest.mark.asyncio
async def test_game_settings_save(setup_temp_files):
    """Test saving game settings to file."""
    # Create mock settings and base settings
    mock_base_settings = MagicMock()
    settings = GameSettings(mock_base_settings)

    # Call the save method
    settings.save()

    # Verify save was called on the base settings
    mock_base_settings.save.assert_called_once()


@pytest.mark.asyncio
async def test_global_settings_load(setup_temp_files):
    """Test loading global settings from file."""
    # Patch the _BaseSettings.load method
    with patch('model.settings._base_settings._BaseSettings.load') as mock_load:
        # Set up mock return
        mock_settings = MagicMock()
        mock_settings.get_settings.side_effect = lambda player_id, setting: {
            (1, "defaultvote"): [True, 300],
            (2, "defaultvote"): [False, 600]
        }.get((player_id, setting))
        mock_load.return_value = mock_settings

        # Load the settings
        settings = GlobalSettings.load()

        # Verify settings were loaded correctly
        default_vote = settings.get_default_vote(1)
        assert default_vote[0] is True
        assert default_vote[1] == 300

        default_vote = settings.get_default_vote(2)
        assert default_vote[0] is False
        assert default_vote[1] == 600

        # Verify non-existent user returns None
        assert settings.get_default_vote(3) is None


@pytest.mark.asyncio
async def test_global_settings_save(setup_temp_files):
    """Test saving global settings to file."""
    # Create mock settings and base settings
    mock_base_settings = MagicMock()
    settings = GlobalSettings(mock_base_settings)

    # Call the save method
    settings.save()

    # Verify save was called on the base settings
    mock_base_settings.save.assert_called_once()


@pytest.mark.asyncio
async def test_global_settings_clear_default_vote():
    """Test clearing default vote settings."""
    # Create mock settings and base settings
    mock_base_settings = MagicMock()
    settings = GlobalSettings(mock_base_settings)

    # Call the clear method
    settings.clear_default_vote(1)

    # Verify clear_setting was called on the base settings
    mock_base_settings.clear_setting.assert_called_once_with(1, "defaultvote")


@pytest.mark.asyncio
async def test_game_settings_set_st_channel():
    """Test setting ST channel in game settings."""
    # Create mock settings and base settings
    mock_base_settings = MagicMock()
    settings = GameSettings(mock_base_settings)

    # Set ST channel
    settings.set_st_channel(1, 101)

    # Verify update_settings was called on the base settings
    mock_base_settings.update_settings.assert_called_once_with(1, {"st_channel": 101})


@pytest.mark.asyncio
async def test_global_settings_set_default_vote():
    """Test setting default vote in global settings."""
    # Create mock settings and base settings
    mock_base_settings = MagicMock()
    settings = GlobalSettings(mock_base_settings)

    # Set default vote
    settings.set_default_vote(1, True, 300)

    # Verify update_settings was called on the base settings
    mock_base_settings.update_settings.assert_called_once_with(1, {'defaultvote': [True, 300]})


@pytest.mark.asyncio
async def test_global_settings_get_alias():
    """Test getting alias from global settings."""
    # Create mock settings
    mock_base_settings = MagicMock()
    mock_base_settings.get_settings.return_value = {"test": "command"}
    settings = GlobalSettings(mock_base_settings)

    # Get alias
    result = settings.get_alias(1, "test")

    # Verify get_settings was called and result is correct
    mock_base_settings.get_settings.assert_called_once_with(1, "aliases")
    assert result == "command"


@pytest.mark.asyncio
async def test_global_settings_set_alias():
    """Test setting alias in global settings."""
    # Create mock settings
    mock_base_settings = MagicMock()
    mock_base_settings.get_settings.return_value = {"existing": "command"}
    settings = GlobalSettings(mock_base_settings)

    # Set alias
    settings.set_alias(1, "test", "new_command")

    # Verify get_settings and update_settings were called correctly
    mock_base_settings.get_settings.assert_called_once_with(1, "aliases")
    mock_base_settings.update_settings.assert_called_once_with(1, {
        'aliases': {"existing": "command", "test": "new_command"}})


@pytest.mark.asyncio
async def test_global_settings_clear_alias():
    """Test clearing alias in global settings."""
    # Create mock settings
    mock_base_settings = MagicMock()
    mock_base_settings.get_settings.return_value = {"existing": "command", "test": "to_remove"}
    settings = GlobalSettings(mock_base_settings)

    # Set alias
    settings.clear_alias(1, "test")

    # Verify get_settings and update_settings were called correctly
    mock_base_settings.get_settings.assert_called_once_with(1, "aliases")
    mock_base_settings.update_settings.assert_called_once_with(1, {
        'aliases': {"existing": "command"}})
