"""
Common patches for testing the Blood on the Clocktower Discord bot.

This module provides common patches and patch sets to simplify
test setup and ensure consistent mocking behavior across tests.
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
        'bot_impl.safe_send': AsyncMock(),
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


def common_patches():
    """Return common patches needed for most tests."""
    patches = {}
    for p in backup_patches():
        if hasattr(p, 'target'):
            patches[p.target] = p.new

    patches['safe_send'] = AsyncMock()
    patches['bot_client.client'] = MagicMock()

    return patches


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
