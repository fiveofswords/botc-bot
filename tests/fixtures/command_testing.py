"""
Command testing helpers for the Blood on the Clocktower Discord bot.

This module provides helper functions for testing commands, including
functions to simulate command execution for both storyteller
and player commands.
"""

from contextlib import contextmanager
from unittest.mock import AsyncMock, patch

from tests.fixtures.discord_mocks import MockMessage


async def execute_command(command_function, message):
    """Execute a command with the given message."""
    # Patch multiple functions needed for commands to work
    with patch('bot_impl.backup'), \
            patch('utils.message_utils.safe_send', new_callable=AsyncMock) as mock_safe_send:
        # Execute the command
        await command_function(message)

        return mock_safe_send


async def run_command_player(command, args, player, channel, command_function):
    """
    Execute a player command for testing.
    
    Args:
        command: The command name without the @ (e.g., 'vote')
        args: The command arguments as a string
        player: The player object from setup_test_game
        channel: The channel object from mock_discord_setup
        command_function: The function to call with the message
        
    Returns:
        The mock safe_send object for verifying calls
    """
    content = f"@{command}"
    if args:
        content = f"{content} {args}"

    message = MockMessage(
        content=content,
        channel=channel,
        author=player.user,
        guild=player.user.guild
    )

    return await execute_command(command_function, message)


async def run_command_storyteller(command, args, st_player, channel, command_function):
    """
    Execute a storyteller command for testing.
    
    Args:
        command: The command name without the @ (e.g., 'startday')
        args: The command arguments as a string
        st_player: The storyteller player object from setup_test_game
        channel: The channel object from mock_discord_setup
        command_function: The function to call with the message
        
    Returns:
        The mock safe_send object for verifying calls
    """
    content = f"@{command}"
    if args:
        content = f"{content} {args}"

    message = MockMessage(
        content=content,
        channel=channel,
        author=st_player.user
    )

    # Set guild to None to simulate a DM when testing storyteller commands
    message.guild = None

    return await execute_command(command_function, message)


async def run_command_vote(vote_type, voter, vote, cmd_function=None):
    """
    Execute a vote command for testing.
    
    Args:
        vote_type: The vote type ('yes', 'no', etc.)
        voter: The player voting
        vote: The Vote object
        cmd_function: The command function to call (defaults to on_message)
        
    Returns:
        The AsyncMock for the vote method
    """
    from bot_impl import on_message

    cmd_function = cmd_function or on_message

    # Create a vote message
    message = MockMessage(
        content=f"@vote {vote_type}",
        channel=voter.user.guild.get_channel(200),  # town square
        author=voter.user,
        guild=voter.user.guild
    )

    # Mock the vote method
    original_vote = vote.vote
    vote.vote = AsyncMock()

    # Mock get_player function to return the voter
    with patch('bot_impl.get_player', return_value=voter), \
            patch('bot_impl.backup', return_value=None), \
            patch('utils.message_utils.safe_send', new_callable=AsyncMock):
            # Process the message
            await cmd_function(message)

    # Return the mock for assertion checking
    return vote.vote


# Enhanced helper functions for common test patterns


@contextmanager
def patch_hand_status_testing(game, mock_discord_setup, additional_patches=None):
    """Context manager for hand status testing patches."""
    from tests.fixtures.common_patches import hand_status_patches

    patches = hand_status_patches(mock_discord_setup)
    if additional_patches:
        patches.update(additional_patches)

    with patch.multiple('', **patches) as mocks:
        # Set up common mock behavior
        if 'utils.message_utils.safe_send' in mocks:
            mock_channel = AsyncMock()
            mocks['utils.message_utils.safe_send'].return_value.channel = mock_channel

        yield mocks


@contextmanager
def patch_vote_testing(vote, game, mock_discord_setup, additional_patches=None):
    """Context manager for vote testing patches."""
    from tests.fixtures.common_patches import vote_execution_patches

    patches = vote_execution_patches(vote, game)
    patches['bot_impl.client'] = mock_discord_setup['client']

    if additional_patches:
        patches.update(additional_patches)

    with patch.multiple('', **patches) as mocks:
        yield mocks


async def execute_command_with_wait_for(command_function, message, mock_discord_setup, wait_for_responses=None):
    """
    Execute a command that uses client.wait_for with predefined responses.
    
    Args:
        command_function: The command function to execute
        message: The MockMessage to send
        mock_discord_setup: The Discord mock setup
        wait_for_responses: List of MockMessage objects to return for wait_for calls
    """
    if wait_for_responses:
        if len(wait_for_responses) == 1:
            mock_discord_setup['client'].wait_for = AsyncMock(return_value=wait_for_responses[0])
        else:
            mock_discord_setup['client'].wait_for = AsyncMock(side_effect=wait_for_responses)

    # Use individual patches for command execution
    with patch('bot_impl.backup', AsyncMock()), \
            patch('utils.message_utils.safe_send', AsyncMock()), \
            patch('bot_impl.client', mock_discord_setup['client']):
        await command_function(message)


async def test_hand_command(command, player, mock_discord_setup, game,
                            expected_hand_state, hand_choice=None, prevote_choice=None):
    """
    Test a hand command (handup/handdown) with optional prevote interaction.
    
    Args:
        command: The command name ("handup" or "handdown") 
        player: The player executing the command
        mock_discord_setup: Discord mock setup
        game: The game object
        expected_hand_state: Expected final hand_raised state
        hand_choice: Choice for hand status prompt ("up"/"down")
        prevote_choice: Choice for prevote prompt ("yes"/"no"/"cancel")
    
    Returns:
        Dict with mock objects for assertions
    """
    # Create the command message
    message = MockMessage(
        content=f"@{command}",
        channel=player.user.dm_channel,
        author=player.user
    )

    # Set up wait_for responses
    responses = []
    if prevote_choice:
        responses.append(MockMessage(content=prevote_choice, author=player.user, channel=AsyncMock()))
    if hand_choice:
        responses.append(MockMessage(content=hand_choice, author=player.user, channel=AsyncMock()))

    # Execute with proper patching
    with patch_hand_status_testing(game, mock_discord_setup, {'bot_impl.get_player': player}) as mocks:
        await execute_command_with_wait_for(
            command_function=None,  # Will need to import on_message
            message=message,
            mock_discord_setup=mock_discord_setup,
            wait_for_responses=responses
        )

    return mocks
