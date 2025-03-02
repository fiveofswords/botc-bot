"""
Command testing helpers for the Blood on the Clocktower Discord bot.

This module provides helper functions for testing commands, including
functions to simulate command execution for both storyteller
and player commands.
"""

from unittest.mock import AsyncMock, patch

from tests.fixtures.discord_mocks import MockMessage


async def create_command_message(content, channel, author, guild=None):
    """Create a message object for command testing."""
    return MockMessage(
        message_id=1000,
        content=content,
        channel=channel,
        author=author,
        guild=guild
    )


async def execute_command(command_function, message):
    """Execute a command with the given message."""
    # Patch multiple functions needed for commands to work
    with patch('bot_impl.backup'), \
            patch('utils.message_utils.safe_send', new_callable=AsyncMock) as mock_utils_safe_send, \
            patch('bot_impl.safe_send', new_callable=AsyncMock) as mock_safe_send:
        # Execute the command
        await command_function(message)

        # Create a combined mock that appears called if either real mock was called
        combined_mock = AsyncMock()
        combined_mock.called = mock_utils_safe_send.called or mock_safe_send.called
        # Copy call details from whichever mock was called
        if mock_utils_safe_send.called:
            combined_mock.call_args_list = mock_utils_safe_send.call_args_list
            combined_mock.call_args = mock_utils_safe_send.call_args
        elif mock_safe_send.called:
            combined_mock.call_args_list = mock_safe_send.call_args_list
            combined_mock.call_args = mock_safe_send.call_args

        return combined_mock


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

    message = await create_command_message(
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

    message = await create_command_message(
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
    message = await create_command_message(
        content=f"@vote {vote_type}",
        channel=voter.user.guild.get_channel(200),  # town square
        author=voter.user,
        guild=voter.user.guild
    )

    # Mock the vote method
    original_vote = vote.vote
    vote.vote = AsyncMock()

    # Mock get_player function to return the voter
    with patch('bot_impl.get_player', return_value=voter):
        with patch('bot_impl.backup', return_value=None), patch('bot_impl.safe_send', new_callable=AsyncMock):
            # Process the message
            await cmd_function(message)

    # Return the mock for assertion checking
    return vote.vote
