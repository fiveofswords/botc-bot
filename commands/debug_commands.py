"""Information and utility commands (info, time, etc.)."""

import discord

from commands.command_enums import HelpSection, UserType
from commands.registry import registry, CommandArgument
from utils import message_utils


@registry.command(
    name="ping",
    description={
        UserType.STORYTELLER: "Test command to check if the bot is responding to a Storyteller",
        UserType.OBSERVER: "Test command to check if the bot is responding to an Observer",
        UserType.PLAYER: "Test command to check if the bot is responding to a Player",
        UserType.PUBLIC: "Test command to check if the bot is responding",
    },
    help_sections=[HelpSection.MISC],
    user_types=[UserType.STORYTELLER, UserType.OBSERVER, UserType.PLAYER, UserType.PUBLIC],
)
async def ping_command(message: discord.Message, argument: str):
    """Ping command for testing."""
    await message_utils.safe_send(message.channel, "Pong!")


@registry.command(
    name="test",
    description="Test command to verify new command system works",
    help_sections=[HelpSection.MISC],
    user_types=[UserType.STORYTELLER],
    arguments=[CommandArgument("arguments...", optional=True)])
async def test_command(message: discord.Message, argument: str):
    """Test command to verify new command system works."""
    await message_utils.safe_send(message.channel, f"New command system working! Argument: {argument}")
