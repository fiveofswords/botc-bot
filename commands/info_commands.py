"""Information and utility commands (info, time, etc.)."""
import discord

from commands.help_types import HelpSection, UserType
from commands.registry import registry
from utils import message_utils


@registry.command(
    name="ping",
    description={
        UserType.PLAYER: "Test command to check if the bot is responding to a Player",
        UserType.STORYTELLER: "Test command to check if the bot is responding to a Storyteller"
    },
    help_sections=[HelpSection.MISC],
    user_types=[UserType.ALL]
)
async def ping_command(message: discord.Message, argument: str):
    """Ping command for testing."""
    await message_utils.safe_send(message.channel, "Pong!")


@registry.command(
    name="test",
    description="Test command to verify new command system works",
    help_sections=[HelpSection.MISC],
    user_types=[UserType.STORYTELLER]
)
async def test_command(message: discord.Message, argument: str):
    """Test command to verify new command system works."""
    await message_utils.safe_send(message.channel, f"New command system working! Argument: {argument}")
