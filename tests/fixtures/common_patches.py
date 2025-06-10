"""
Common patches for testing the Blood on the Clocktower Discord bot.

This module provides common patches and patch sets to simplify
test setup and ensure consistent mocking behavior across tests.

Naming conventions:
- Functions ending in "_patches" return dictionaries of patches
- Functions ending in "_patches_combined" return lists of patch objects
- All patch functions use consistent parameter naming and documentation
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# Core patch collections

def backup_patches():
    """Return patches that disable backup functionality."""
    return [
        patch('bot_impl.backup', return_value=None),
        patch('bot_impl.remove_backup', return_value=None),
    ]


def file_operation_patches():
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


def discord_reaction_patches():
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
    patches = backup_patches()
    with patch.multiple('', **{p.target: p.new for p in patches}):
        yield


def base_bot_patches():
    """Return base patches needed for most bot functionality."""
    return {
        'bot_impl.backup': AsyncMock(),
        **discord_message_patches()
    }


def common_patches():
    """Return common patches needed for most tests."""
    patches = {}
    for p in backup_patches():
        if hasattr(p, 'target'):
            patches[p.target] = p.new

    patches['safe_send'] = AsyncMock()
    patches['bot_client.client'] = MagicMock()

    return patches


def command_execution_patches(mock_discord_setup=None):
    """Return patches commonly needed for command execution tests."""
    patches = {
        'bot_impl.backup': AsyncMock(),
        'utils.message_utils.safe_send': AsyncMock(),
    }

    if mock_discord_setup:
        patches['bot_impl.client'] = mock_discord_setup['client']

    return patches


def hand_status_patches(game, mock_discord_setup):
    """Return patches commonly needed for hand status testing."""
    return {
        'bot_impl.backup': AsyncMock(),
        'utils.message_utils.safe_send': AsyncMock(),
        'bot_impl.client': mock_discord_setup['client'],
        'game.update_seating_order_message': AsyncMock(),
    }


def vote_execution_patches(vote=None, game=None):
    """Return patches commonly needed for vote execution tests."""
    patches = {
        'bot_impl.backup': AsyncMock(),
        'utils.message_utils.safe_send': AsyncMock(),
    }

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
    return {
        'bot_impl.backup': AsyncMock(),
        'utils.message_utils.safe_send': AsyncMock(),
        'bot_impl.client': mock_discord_setup['client'],
        'bot_impl.select_player': AsyncMock(),
        'bot_impl.update_presence': AsyncMock(),
    }


def patch_file_operations():
    """Return patches that disable all file operations."""
    return [
        *backup_patches(),
        *file_operation_patches()
    ]


def patch_discord_send():
    """Return patches that mock Discord message sending."""
    return discord_message_patches()


def patch_discord_reactions():
    """Return patches that mock Discord reaction handling."""
    return discord_reaction_patches()


def patch_game_functions():
    """Return patches for core Game class methods."""
    return game_function_patches()
