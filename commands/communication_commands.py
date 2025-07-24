"""Communication control commands for managing PMs and nominations."""

import discord

import global_vars
from commands.command_enums import HelpSection, UserType, GamePhase
from commands.registry import registry, CommandArgument
from model import game
from utils import game_utils


@registry.command(
    name="openpms",
    description="opens pms",
    help_sections=[HelpSection.DAY],
    user_types=[UserType.STORYTELLER],
    required_phases=[GamePhase.DAY],  # Day only
)
async def openpms_command(message: discord.Message, argument: str):
    """Open private messages for the day."""
    await global_vars.game.days[-1].open_pms()
    if global_vars.game is not game.NULL_GAME:
        game_utils.backup("current_game.pckl")


@registry.command(
    name="closepms",
    description="closes pms",
    help_sections=[HelpSection.DAY],
    user_types=[UserType.STORYTELLER],
    required_phases=[GamePhase.DAY],  # Day only
)
async def closepms_command(message: discord.Message, argument: str):
    """Close private messages for the day."""
    await global_vars.game.days[-1].close_pms()
    if global_vars.game is not game.NULL_GAME:
        game_utils.backup("current_game.pckl")


@registry.command(
    name="opennoms",
    description="opens nominations",
    help_sections=[HelpSection.DAY],
    user_types=[UserType.STORYTELLER],
    required_phases=[GamePhase.DAY],  # Day only
)
async def opennoms_command(message: discord.Message, argument: str):
    """Open nominations for the day."""
    await global_vars.game.days[-1].open_noms()
    if global_vars.game is not game.NULL_GAME:
        game_utils.backup("current_game.pckl")


@registry.command(
    name="closenoms",
    description="closes nominations",
    help_sections=[HelpSection.DAY],
    user_types=[UserType.STORYTELLER],
    required_phases=[GamePhase.DAY],  # Day only
)
async def closenoms_command(message: discord.Message, argument: str):
    """Close nominations for the day."""
    await global_vars.game.days[-1].close_noms()
    if global_vars.game is not game.NULL_GAME:
        game_utils.backup("current_game.pckl")


@registry.command(
    name="open",
    description="opens pms and nominations",
    help_sections=[HelpSection.DAY],
    user_types=[UserType.STORYTELLER],
    required_phases=[GamePhase.DAY],  # Day only
)
async def open_command(message: discord.Message, argument: str):
    """Open both private messages and nominations for the day."""
    await global_vars.game.days[-1].open_pms()
    await global_vars.game.days[-1].open_noms()
    if global_vars.game is not game.NULL_GAME:
        game_utils.backup("current_game.pckl")


@registry.command(
    name="close",
    description="closes pms and nominations",
    help_sections=[HelpSection.DAY],
    user_types=[UserType.STORYTELLER],
    required_phases=[GamePhase.DAY],  # Day only
)
async def close_command(message: discord.Message, argument: str):
    """Close both private messages and nominations for the day."""
    await global_vars.game.days[-1].close_pms()
    await global_vars.game.days[-1].close_noms()
    if global_vars.game is not game.NULL_GAME:
        game_utils.backup("current_game.pckl")


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
