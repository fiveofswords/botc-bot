"""
Tests for info commands integration with the command registry through bot_impl.

This module tests that debug_commands (ping, test) can be called via the registry
through bot_impl's on_message handler.
"""

from unittest.mock import AsyncMock, patch

import pytest

import global_vars
from bot_impl import on_message
from commands.registry import registry
from tests.fixtures.discord_mocks import mock_discord_setup, MockMessage
from tests.fixtures.game_fixtures import setup_test_game


@pytest.mark.asyncio
async def test_ping_command_via_registry(mock_discord_setup, setup_test_game):
    """Test that @ping command can be called via the registry through bot_impl."""
    # Set up global variables for this test
    global_vars.game = setup_test_game['game']
    global_vars.channel = mock_discord_setup['channels']['town_square']

    # Create a DM ping command message (registry commands only work in DMs)
    message = MockMessage(
        content="@ping",
        channel=mock_discord_setup['members']['alice'].dm_channel,
        author=mock_discord_setup['members']['alice'],
        guild=None  # DM channels have no guild
    )

    # Test the command execution with individual patches
    with patch('bot_impl.backup', AsyncMock()), \
            patch('utils.message_utils.safe_send', AsyncMock()) as mock_safe_send, \
            patch('bot_impl.client', mock_discord_setup['client']):
        await on_message(message)

        # Verify that safe_send was called with "Pong!"
        mock_safe_send.assert_called_once_with(
            message.channel, "Pong!"
        )


@pytest.mark.asyncio
async def test_test_command_via_registry(mock_discord_setup, setup_test_game):
    """Test that @test command can be called via the registry through bot_impl."""
    # Set up global variables for this test
    global_vars.game = setup_test_game['game']
    global_vars.channel = mock_discord_setup['channels']['town_square']

    # Create a DM test command message with an argument (registry commands only work in DMs)
    message = MockMessage(
        content="@test hello world",
        channel=mock_discord_setup['members']['alice'].dm_channel,
        author=mock_discord_setup['members']['alice'],
        guild=None  # DM channels have no guild
    )

    # Test the command execution with individual patches
    with patch('bot_impl.backup', AsyncMock()), \
            patch('utils.message_utils.safe_send', AsyncMock()) as mock_safe_send, \
            patch('bot_impl.client', mock_discord_setup['client']):
        await on_message(message)

        # Verify that safe_send was called with the expected message
        mock_safe_send.assert_called_once_with(
            message.channel, "New command system working! Argument: hello world"
        )


@pytest.mark.asyncio
async def test_test_command_no_arguments_via_registry(mock_discord_setup, setup_test_game):
    """Test that @test command works without arguments via the registry."""
    # Set up global variables for this test
    global_vars.game = setup_test_game['game']
    global_vars.channel = mock_discord_setup['channels']['town_square']

    # Create a DM test command message without arguments (registry commands only work in DMs)
    message = MockMessage(
        content="@test",
        channel=mock_discord_setup['members']['alice'].dm_channel,
        author=mock_discord_setup['members']['alice'],
        guild=None  # DM channels have no guild
    )

    # Test the command execution with individual patches
    with patch('bot_impl.backup', AsyncMock()), \
            patch('utils.message_utils.safe_send', AsyncMock()) as mock_safe_send, \
            patch('bot_impl.client', mock_discord_setup['client']):
        await on_message(message)

        # Verify that safe_send was called with empty argument
        mock_safe_send.assert_called_once_with(
            message.channel, "New command system working! Argument: "
        )


@pytest.mark.asyncio
async def test_unregistered_command_returns_false():
    """Test that unregistered commands return False from registry."""
    # Create a mock message
    message = MockMessage(
        content="",
        channel=AsyncMock(),
        author=AsyncMock()
    )

    # Test non-existent command
    result = await registry.handle_command("nonexistent", message, "")
    assert result is False  # Command was not handled


@pytest.mark.asyncio
async def test_info_commands_in_dm_channel(mock_discord_setup, setup_test_game):
    """Test that info commands work in DM channels."""
    # Set up global variables for this test
    global_vars.game = setup_test_game['game']
    global_vars.channel = mock_discord_setup['channels']['town_square']

    # Create a DM message for ping command
    message = MockMessage(
        content="@ping",
        channel=mock_discord_setup['members']['alice'].dm_channel,
        author=mock_discord_setup['members']['alice'],
        guild=None  # DM channels have no guild
    )

    # Test the command execution with individual patches
    with patch('bot_impl.backup', AsyncMock()), \
            patch('utils.message_utils.safe_send', AsyncMock()) as mock_safe_send, \
            patch('bot_impl.client', mock_discord_setup['client']):
        await on_message(message)

        # Verify that safe_send was called with "Pong!"
        mock_safe_send.assert_called_once_with(
            message.channel, "Pong!"
        )


@pytest.mark.asyncio
async def test_info_commands_case_insensitive(mock_discord_setup, setup_test_game):
    """Test that info commands are case insensitive (bot_impl converts to lowercase)."""
    # Set up global variables for this test
    global_vars.game = setup_test_game['game']
    global_vars.channel = mock_discord_setup['channels']['town_square']

    # Create a DM message with uppercase command (registry commands only work in DMs)
    message = MockMessage(
        content="@PING",
        channel=mock_discord_setup['members']['alice'].dm_channel,
        author=mock_discord_setup['members']['alice'],
        guild=None  # DM channels have no guild
    )

    # Test the command execution - should work since bot_impl converts commands to lowercase
    with patch('bot_impl.backup', AsyncMock()), \
            patch('utils.message_utils.safe_send', AsyncMock()) as mock_safe_send, \
            patch('bot_impl.client', mock_discord_setup['client']):
        await on_message(message)

        # The uppercase command should be handled by the registry (converted to lowercase)
        # so safe_send should be called for the ping response
        mock_safe_send.assert_called_once_with(
            message.channel, "Pong!"
        )


@pytest.mark.asyncio
async def test_info_commands_with_extra_whitespace(mock_discord_setup, setup_test_game):
    """Test that info commands handle extra whitespace properly."""
    # Set up global variables for this test
    global_vars.game = setup_test_game['game']
    global_vars.channel = mock_discord_setup['channels']['town_square']

    # Create a DM test command message with extra spaces (registry commands only work in DMs)
    message = MockMessage(
        content="@test    hello    world   ",
        channel=mock_discord_setup['members']['alice'].dm_channel,
        author=mock_discord_setup['members']['alice'],
        guild=None  # DM channels have no guild
    )

    # Test the command execution with individual patches
    with patch('bot_impl.backup', AsyncMock()), \
            patch('utils.message_utils.safe_send', AsyncMock()) as mock_safe_send, \
            patch('bot_impl.client', mock_discord_setup['client']):
        await on_message(message)

        # Verify that safe_send was called with the full argument string (including spaces)
        mock_safe_send.assert_called_once_with(
            message.channel, "New command system working! Argument:    hello    world   "
        )


@pytest.mark.asyncio
async def test_registry_prevents_legacy_command_processing(mock_discord_setup, setup_test_game):
    """Test that when registry handles a command, legacy command processing is bypassed."""
    # Set up global variables for this test
    global_vars.game = setup_test_game['game']
    global_vars.channel = mock_discord_setup['channels']['town_square']

    # Create a DM ping command message (registry commands only work in DMs)
    message = MockMessage(
        content="@ping",
        channel=mock_discord_setup['members']['alice'].dm_channel,
        author=mock_discord_setup['members']['alice'],
        guild=None  # DM channels have no guild
    )

    # Mock a function that would be called in legacy command processing
    # to verify it's not reached when registry handles the command
    with patch('bot_impl.backup', AsyncMock()), \
            patch('utils.message_utils.safe_send', AsyncMock()) as mock_safe_send, \
            patch('bot_impl.client', mock_discord_setup['client']), \
            patch('model.settings.global_settings.GlobalSettings.load') as mock_global_settings:
        # Set up the mock to avoid issues with the settings load
        mock_settings_instance = mock_global_settings.return_value
        mock_settings_instance.get_alias.return_value = None

        await on_message(message)

        # Verify the registry command was handled
        mock_safe_send.assert_called_once_with(
            message.channel, "Pong!"
        )

        # Verify that GlobalSettings.load was called for alias checking 
        # (this happens before registry handling)
        mock_global_settings.assert_called_once()


@pytest.mark.asyncio
async def test_registry_commands_only_work_in_dms(mock_discord_setup, setup_test_game):
    """Test that registry commands only work in DM channels, not in guild channels."""
    # Set up global variables for this test
    global_vars.game = setup_test_game['game']
    global_vars.channel = mock_discord_setup['channels']['town_square']

    # Create a guild ping command message
    message = MockMessage(
        content="@ping",
        channel=mock_discord_setup['channels']['town_square'],
        author=mock_discord_setup['members']['alice'],
        guild=mock_discord_setup['guild']  # Guild message
    )

    # Test the command execution with individual patches
    with patch('bot_impl.backup', AsyncMock()), \
            patch('utils.message_utils.safe_send', AsyncMock()) as mock_safe_send, \
            patch('bot_impl.client', mock_discord_setup['client']):
        await on_message(message)

        # The ping command should NOT be handled by the registry in guild channels
        # so safe_send should not be called for the ping response
        calls = mock_safe_send.call_args_list
        pong_calls = [call for call in calls if len(call[0]) > 1 and call[0][1] == "Pong!"]
        assert len(pong_calls) == 0
