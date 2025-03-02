"""
Tests for backup, load, and remove_backup functions in bot_impl.py
"""

from unittest.mock import patch, MagicMock, mock_open, AsyncMock

import pytest

import global_vars
from bot_impl import backup, load, remove_backup, Game, Script
from tests.test_bot_integration import mock_discord_setup


@pytest.mark.asyncio
async def test_backup():
    """Test the backup function."""
    # Setup mocks
    mock_game = MagicMock()
    # Use a side_effect with a list to return the attributes we want
    dir_mock = MagicMock(side_effect=lambda: ["seatingOrder", "seatingOrderMessage", "script"])
    mock_game.__dir__ = dir_mock
    mock_game.seatingOrder = []
    mock_game.seatingOrderMessage = MagicMock(id=12345)
    mock_game.script = Script([])

    # Mock global variables
    original_game = global_vars.game
    global_vars.game = mock_game

    # Mock file operations
    with patch('builtins.open', mock_open()) as mock_file:
        with patch('dill.dump') as mock_dump:
            # Call the function under test
            backup("test_backup.pckl")

            # Verify file is opened for each attribute
            assert mock_file.call_count == 3  # Once for objects list + once per attribute

            # Verify dill.dump is called with correct arguments
            assert mock_dump.call_count == 3  # Once for objects list + once per attribute

    # Restore global variable
    global_vars.game = original_game


@pytest.mark.asyncio
async def test_backup_null_game():
    """Test the backup function with NULL_GAME."""
    # Mock global variables
    original_game = global_vars.game
    global_vars.game = None

    # Mock file operations
    with patch('builtins.open', mock_open()) as mock_file:
        with patch('dill.dump') as mock_dump:
            # Call the function under test
            backup("test_backup.pckl")

            # Verify file operations are not performed
            mock_file.assert_not_called()
            mock_dump.assert_not_called()

    # Restore global variable
    global_vars.game = original_game


@pytest.mark.asyncio
async def test_load(mock_discord_setup):
    """Test the load function."""
    # Setup
    mock_channel = mock_discord_setup['channels']['town_square']
    mock_message = MagicMock()
    mock_channel.fetch_message = AsyncMock(return_value=mock_message)

    # Mock file operations
    with patch('os.path.isfile', return_value=True):
        with patch('builtins.open', mock_open()) as mock_file:
            with patch('dill.load') as mock_load:
                # Configure mock_load to return test values
                mock_load.side_effect = [
                    ["seatingOrder", "seatingOrderMessage", "script"],  # First load: object list
                    [],  # seatingOrder
                    12345,  # seatingOrderMessage (message ID)
                    Script([])  # script
                ]

                # Call the function under test
                game = await load("test_backup.pckl")

                # Verify file is opened for reading
                assert mock_file.call_count == 4  # Once for objects list + once per attribute

                # Verify dill.load is called
                assert mock_load.call_count == 4  # Once for objects list + once per attribute

                # Verify game attributes
                assert isinstance(game, Game)
                assert game.seatingOrder == []
                assert game.seatingOrderMessage == mock_message
                assert isinstance(game.script, Script)


@pytest.mark.asyncio
async def test_load_missing_file():
    """Test the load function with a missing file component."""
    # Mock file operations
    with patch('os.path.isfile') as mock_isfile:
        with patch('builtins.open', mock_open()) as mock_file:
            with patch('dill.load') as mock_load:
                # Configure mock_isfile to return False for one attribute file
                mock_isfile.side_effect = lambda path: False if "seatingOrderMessage" in path else True

                # Configure mock_load to return test values
                mock_load.return_value = ["seatingOrder", "seatingOrderMessage", "script"]

                # Call the function under test
                game = await load("test_backup.pckl")

                # Verify result is None (incomplete backup)
                assert game is None


@pytest.mark.asyncio
async def test_remove_backup():
    """Test the remove_backup function."""
    # Setup
    mock_game = MagicMock()
    # Use a side_effect with a list to return the attributes we want
    dir_mock = MagicMock(side_effect=lambda: ["seatingOrder", "seatingOrderMessage", "script"])
    mock_game.__dir__ = dir_mock
    # Set mock attributes so getattr works
    mock_game.seatingOrder = []
    mock_game.seatingOrderMessage = MagicMock()
    mock_game.script = MagicMock()

    # Mock global variables
    original_game = global_vars.game
    global_vars.game = mock_game

    # Mock file operations
    with patch('os.remove') as mock_remove:
        # Call the function under test
        remove_backup("test_backup.pckl")

        # Verify os.remove is called for each file
        mock_remove.assert_any_call("test_backup.pckl")

        # Check that at least one attribute file was removed
        attribute_calls = [
            call for call in mock_remove.call_args_list
            if any(attr in call[0][0] for attr in ["seatingOrder", "seatingOrderMessage", "script"])
        ]
        assert len(attribute_calls) > 0, "No attribute files were removed"

    # Restore global variable
    global_vars.game = original_game
