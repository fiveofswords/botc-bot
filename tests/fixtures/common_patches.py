"""
Common patches for testing the Blood on the Clocktower Discord bot.

This module provides common patches and patch sets to simplify
test setup and ensure consistent mocking behavior across tests.

Patch Types:
- Functions ending in "_patches" return dictionaries for manual patching
- Functions ending in "_patches_combined" return lists of patch objects for ExitStack
- Full setup functions for complete bot initialization scenarios

Naming conventions:
- Use ExitStack with _patches_combined functions for multiple patches
- Dictionary patches are for specific targeted mocking scenarios
- All patch functions use consistent parameter naming and documentation
"""

from contextlib import ExitStack
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# Core patch collections

def backup_patches_combined():
    """Return patches that disable backup functionality."""
    return [
        patch('utils.game_utils.backup', return_value=None),
        patch('utils.game_utils.remove_backup', return_value=None),
    ]


def file_operation_patches_combined():
    """Return patches that disable file system operations."""
    return [
        patch('os.path.exists', return_value=False),
        patch('os.makedirs'),
        patch('os.remove'),
        patch('pickle.dump'),
        patch('pickle.load'),
        patch('builtins.open')
    ]


def discord_message_patches():
    """Return patches that mock Discord message sending."""
    return {
        'utils.message_utils.safe_send': AsyncMock(),
        'utils.message_utils.safe_send_dm': AsyncMock()
    }


def discord_reaction_patches_combined():
    """Return patches that mock Discord reaction handling."""
    return [
        patch('discord.Reaction', MagicMock()),
        patch('discord.RawReactionActionEvent', MagicMock())
    ]


def game_function_patches():
    """Return patches for core Game class methods."""
    return {
        'bot_impl.Game.start_day': AsyncMock(),
        'bot_impl.Game.end': AsyncMock(),
        'bot_impl.Day.open_pms': AsyncMock(),
        'bot_impl.Day.open_noms': AsyncMock(),
        'bot_impl.Day.close_pms': AsyncMock(),
        'bot_impl.Day.close_noms': AsyncMock(),
        'bot_impl.Day.nomination': AsyncMock(),
        'bot_impl.Day.end': AsyncMock(),
        'bot_impl.Vote.vote': AsyncMock(),
        'bot_impl.Vote.preset_vote': AsyncMock()
    }


# Composite patch collections

@pytest.fixture(autouse=True)
def disable_backup():
    """Automatically disables backup functionality for all tests."""
    patches = backup_patches_combined()
    with ExitStack() as stack:
        for p in patches:
            stack.enter_context(p)
        yield


def base_bot_patches():
    """Return base patches needed for most bot functionality."""
    return {
        'bot_impl.backup': AsyncMock(),
        'utils.message_utils.safe_send': AsyncMock(),
        'utils.message_utils.safe_send_dm': AsyncMock()
    }


# Removed redundant common_patches() - use specific patch functions instead


def command_execution_patches(mock_discord_setup=None):
    """Return patches commonly needed for command execution tests."""
    patches = base_bot_patches().copy()
    
    if mock_discord_setup:
        patches['bot_client.client'] = mock_discord_setup['client']

    return patches


def hand_status_patches(mock_discord_setup):
    """Return patches commonly needed for hand status testing."""
    patches = base_bot_patches().copy()
    patches.update({
        'bot_client.client': mock_discord_setup['client'],
        'game.update_seating_order_message': AsyncMock(),
    })
    return patches


def vote_execution_patches(vote=None, game=None):
    """Return patches commonly needed for vote execution tests."""
    patches = base_bot_patches().copy()

    if vote:
        patches.update({
            'bot_impl.get_current_vote': vote,
            'bot_impl.get_active_vote': vote,
            'bot_impl.get_vote': vote,
            'bot_impl.find_vote': vote,
        })

    if game:
        patches['game.update_seating_order_message'] = AsyncMock()

    return patches


def storyteller_command_patches(mock_discord_setup):
    """Return patches commonly needed for storyteller command tests."""
    patches = base_bot_patches().copy()
    patches.update({
        'bot_client.client': mock_discord_setup['client'],
        'bot_impl.select_player': AsyncMock(),
        'bot_impl.update_presence': AsyncMock(),
    })
    return patches


def file_operations_patches_combined():
    """Return patches that disable all file operations."""
    return [
        *backup_patches_combined(),
        *file_operation_patches_combined()
    ]


def config_patches(mock_discord_setup):
    """Return patches for bot_impl.config values using mock Discord objects."""
    return {
        'bot_impl.config.SERVER_ID': mock_discord_setup['guild'].id,
        'bot_impl.config.GAME_CATEGORY_ID': mock_discord_setup['categories']['game'].id,
        'bot_impl.config.HANDS_CHANNEL_ID': mock_discord_setup['channels']['hands'].id,
        'bot_impl.config.OBSERVER_CHANNEL_ID': mock_discord_setup['channels']['observer'].id,
        'bot_impl.config.INFO_CHANNEL_ID': mock_discord_setup['channels']['info'].id,
        'bot_impl.config.WHISPER_CHANNEL_ID': mock_discord_setup['channels']['whisper'].id,
        'bot_impl.config.TOWN_SQUARE_CHANNEL_ID': mock_discord_setup['channels']['town_square'].id,
        'bot_impl.config.OUT_OF_PLAY_CATEGORY_ID': mock_discord_setup['categories']['out_of_play'].id,
        'bot_impl.config.CHANNEL_SUFFIX': "test",
        'bot_impl.config.PLAYER_ROLE': "Player",
        'bot_impl.config.STORYTELLER_ROLE': "Storyteller"
    }


def full_bot_setup_patches_combined(mock_discord_setup, with_backup=False, backup_game=None):
    """Return complete list of patches needed for bot initialization tests."""
    patches = []

    # Base patches
    patches.extend(backup_patches_combined())
    patches.extend([
        patch('utils.message_utils.safe_send', AsyncMock()),
        patch('utils.message_utils.safe_send_dm', AsyncMock()),
        patch('bot_client.client', mock_discord_setup['client']),
    ])

    # Config patches
    patches.extend([
        patch('bot_impl.config.SERVER_ID', mock_discord_setup['guild'].id),
        patch('bot_impl.config.GAME_CATEGORY_ID', mock_discord_setup['categories']['game'].id),
        patch('bot_impl.config.HANDS_CHANNEL_ID', mock_discord_setup['channels']['hands'].id),
        patch('bot_impl.config.OBSERVER_CHANNEL_ID', mock_discord_setup['channels']['observer'].id),
        patch('bot_impl.config.INFO_CHANNEL_ID', mock_discord_setup['channels']['info'].id),
        patch('bot_impl.config.WHISPER_CHANNEL_ID', mock_discord_setup['channels']['whisper'].id),
        patch('bot_impl.config.TOWN_SQUARE_CHANNEL_ID', mock_discord_setup['channels']['town_square'].id),
        patch('bot_impl.config.OUT_OF_PLAY_CATEGORY_ID', mock_discord_setup['categories']['out_of_play'].id),
        patch('bot_impl.config.CHANNEL_SUFFIX', "test"),
        patch('bot_impl.config.PLAYER_ROLE', "Player"),
        patch('bot_impl.config.STORYTELLER_ROLE', "Storyteller"),
    ])

    # Backup file handling
    if with_backup:
        patches.extend([
            patch('os.path.isfile', return_value=True),
            patch('utils.game_utils.load', return_value=backup_game)
        ])
    else:
        patches.append(patch('os.path.isfile', return_value=False))

    return patches

# Removed unused full_bot_setup_context fixture - use full_bot_setup_patches_combined directly with ExitStack
