"""Voting and nomination related commands."""

import discord

from commands.command_enums import HelpSection, UserType, GamePhase
from commands.registry import registry, CommandArgument


@registry.command(
    name="cancelnomination",
    description="cancels the previous nomination",
    help_sections=[HelpSection.MISC],
    user_types=[UserType.STORYTELLER],
    required_phases=[GamePhase.DAY],  # Day only
    implemented=False
)
async def cancelnomination_command(message: discord.Message, argument: str):
    """Cancel the current nomination and vote."""
    raise NotImplementedError("Registry implementation not ready - using bot_impl")


@registry.command(
    name="handup",
    description="Raise your hand during a vote",
    help_sections=[HelpSection.PLAYER],
    user_types=[UserType.PLAYER],
    required_phases=[GamePhase.DAY],  # Day only
    implemented=False
)
async def handup_command(message: discord.Message, argument: str):
    """Raise your hand during a vote."""
    raise NotImplementedError("Registry implementation not ready - using bot_impl")


@registry.command(
    name="handdown",
    description="Lower your hand during a vote",
    help_sections=[HelpSection.PLAYER],
    user_types=[UserType.PLAYER],
    required_phases=[GamePhase.DAY],  # Day only
    implemented=False
)
async def handdown_command(message: discord.Message, argument: str):
    """Lower your hand during a vote."""
    raise NotImplementedError("Registry implementation not ready - using bot_impl")


@registry.command(
    name="vote",
    description={
        UserType.STORYTELLER: "votes for the current player",
        UserType.PLAYER: "votes on an ongoing nomination"
    },
    help_sections=[HelpSection.DAY, HelpSection.PLAYER],
    user_types=[UserType.PLAYER, UserType.STORYTELLER],
    arguments={
        UserType.STORYTELLER: [],  # No arguments for storytellers
        UserType.PLAYER: [CommandArgument(("yes", "no"))]
    },
    required_phases=[GamePhase.DAY],  # Day only
    implemented=False
)
async def vote_command(message: discord.Message, argument: str):
    """Cast your vote (yes/no) if it's your turn."""
    raise NotImplementedError("Registry implementation not ready - using bot_impl")


@registry.command(
    name="presetvote",
    description="submits a preset vote. will not work if it is your turn to vote. not recommended -- contact the storytellers instead",
    help_sections=[HelpSection.PLAYER],
    user_types=[UserType.PLAYER, UserType.STORYTELLER],
    aliases=["prevote"],
    arguments=[CommandArgument(("yes", "no"))],
    required_phases=[GamePhase.DAY],  # Day only
    implemented=False
)
async def presetvote_command(message: discord.Message, argument: str):
    """Set a preset vote for the next voting round."""
    raise NotImplementedError("Registry implementation not ready - using bot_impl")




@registry.command(
    name="cancelpreset",
    description="Cancel preset vote for yourself (player) or anyone (storyteller)",
    help_sections=[HelpSection.PLAYER],
    user_types=[UserType.PLAYER, UserType.STORYTELLER],
    required_phases=[GamePhase.DAY],  # Day only
    implemented=False
)
async def cancelpreset_command(message: discord.Message, argument: str):
    """Cancel preset vote for yourself (player) or anyone (storyteller)."""
    raise NotImplementedError("Registry implementation not ready - using bot_impl")


@registry.command(
    name="cancelprevote",
    description="cancels an existing prevote",
    help_sections=[HelpSection.PLAYER],
    user_types=[UserType.PLAYER, UserType.STORYTELLER],
    required_phases=[GamePhase.DAY],  # Day only
    implemented=False
)
async def cancelprevote_command(message: discord.Message, argument: str):
    """Cancel preset vote for yourself (player) or anyone (storyteller)."""
    raise NotImplementedError("Registry implementation not ready - using bot_impl")


@registry.command(
    name="defaultvote",
    description="will always vote vote in time minutes. if no arguments given, deletes existing defaults.",
    help_sections=[HelpSection.PLAYER],
    user_types=[UserType.PLAYER],
    arguments=[CommandArgument("vote=no", optional=True), CommandArgument("time=60", optional=True)],
    required_phases=[GamePhase.DAY],  # Day only
    implemented=False
)
async def defaultvote_command(message: discord.Message, argument: str):
    """Set/remove default vote and optional duration."""
    raise NotImplementedError("Registry implementation not ready - using bot_impl")


@registry.command(
    name="adjustvotes",
    description="Amnesiac multiplies another player's vote",
    help_sections=[HelpSection.MISC],
    user_types=[UserType.STORYTELLER],
    arguments=[CommandArgument("amnesiac"), CommandArgument("target"), CommandArgument("multiplier")],
    required_phases=[GamePhase.DAY],  # Day only
    aliases=["adjustvote"],
    implemented=False
)
async def adjustvotes_command(message: discord.Message, argument: str):
    """Amnesiac multiplies another player's vote."""
    raise NotImplementedError("Registry implementation not ready - using bot_impl")


@registry.command(
    name="nominate",
    description="nominates player",
    help_sections=[HelpSection.PLAYER],
    user_types=[UserType.PLAYER, UserType.STORYTELLER],
    arguments=[CommandArgument("player")],
    required_phases=[GamePhase.DAY],  # Day only
    implemented=False
)
async def nominate_command(message: discord.Message, argument: str):
    """Nominate another player for execution."""
    raise NotImplementedError("Registry implementation not ready - using bot_impl")


@registry.command(
    name="skip",
    description="Skip your nomination turn",
    help_sections=[HelpSection.PLAYER],
    user_types=[UserType.PLAYER, UserType.STORYTELLER],
    required_phases=[GamePhase.DAY],  # Day only
    implemented=False
)
async def skip_command(message: discord.Message, argument: str):
    """Skip your nomination turn."""
    raise NotImplementedError("Registry implementation not ready - using bot_impl")
