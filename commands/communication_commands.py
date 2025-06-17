"""Communication control commands for managing PMs and nominations."""

import discord

from commands.command_enums import HelpSection, UserType, GamePhase
from commands.registry import registry, CommandArgument


@registry.command(
    name="openpms",
    description="opens pms",
    help_sections=[HelpSection.DAY],
    user_types=[UserType.STORYTELLER],
    required_phases=[GamePhase.DAY],  # Day only
    implemented=False
)
async def openpms_command(message: discord.Message, argument: str):
    """Open private messages for the day."""
    raise NotImplementedError("Registry implementation not ready - using bot_impl")


@registry.command(
    name="closepms",
    description="closes pms",
    help_sections=[HelpSection.DAY],
    user_types=[UserType.STORYTELLER],
    required_phases=[GamePhase.DAY],  # Day only
    implemented=False
)
async def closepms_command(message: discord.Message, argument: str):
    """Close private messages for the day."""
    raise NotImplementedError("Registry implementation not ready - using bot_impl")


@registry.command(
    name="opennoms",
    description="opens nominations",
    help_sections=[HelpSection.DAY],
    user_types=[UserType.STORYTELLER],
    required_phases=[GamePhase.DAY],  # Day only
    implemented=False
)
async def opennoms_command(message: discord.Message, argument: str):
    """Open nominations for the day."""
    raise NotImplementedError("Registry implementation not ready - using bot_impl")


@registry.command(
    name="closenoms",
    description="closes nominations",
    help_sections=[HelpSection.DAY],
    user_types=[UserType.STORYTELLER],
    required_phases=[GamePhase.DAY],  # Day only
    implemented=False
)
async def closenoms_command(message: discord.Message, argument: str):
    """Close nominations for the day."""
    raise NotImplementedError("Registry implementation not ready - using bot_impl")


@registry.command(
    name="open",
    description="opens pms and nominations",
    help_sections=[HelpSection.DAY],
    user_types=[UserType.STORYTELLER],
    required_phases=[GamePhase.DAY],  # Day only
    implemented=False
)
async def open_command(message: discord.Message, argument: str):
    """Open both private messages and nominations for the day."""
    raise NotImplementedError("Registry implementation not ready - using bot_impl")


@registry.command(
    name="close",
    description="closes pms and nominations",
    help_sections=[HelpSection.DAY],
    user_types=[UserType.STORYTELLER],
    required_phases=[GamePhase.DAY],  # Day only
    implemented=False
)
async def close_command(message: discord.Message, argument: str):
    """Close both private messages and nominations for the day."""
    raise NotImplementedError("Registry implementation not ready - using bot_impl")


@registry.command(
    name="pm",
    description="sends player a message",
    help_sections=[HelpSection.PLAYER],
    user_types=[UserType.PLAYER],
    aliases=["message"],
    arguments=[CommandArgument("player")],
    required_phases=[GamePhase.DAY],  # Day only
    implemented=False
)
async def pm_command(message: discord.Message, argument: str):
    """Send a direct message (whisper) to another player."""
    raise NotImplementedError("Registry implementation not ready - using bot_impl")
