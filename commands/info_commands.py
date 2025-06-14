"""Information and utility commands (info, time, etc.)."""
import discord

from commands.registry import registry
from utils import message_utils


@registry.command("ping")
async def ping_command(message: discord.Message, argument: str):
    """Ping command for testing."""
    await message_utils.safe_send(message.channel, "Pong!")


@registry.command("test")
async def test_command(message: discord.Message, argument: str):
    """Test command to verify new command system works."""
    await message_utils.safe_send(message.channel, f"New command system working! Argument: {argument}")
