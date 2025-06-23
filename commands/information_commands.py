"""Information and utility commands for game status and settings."""

import discord

from commands.command_enums import HelpSection, UserType, GamePhase
from commands.registry import registry, CommandArgument


@registry.command(
    name="clear",
    description="returns whitespace",
    help_sections=[HelpSection.PLAYER],
    user_types=[UserType.STORYTELLER, UserType.OBSERVER, UserType.PLAYER, UserType.PUBLIC],
    required_phases=[],  # No game needed
    implemented=False
)
async def clear_command(message: discord.Message, argument: str):
    """Clear the chat window with blank lines."""
    raise NotImplementedError("Registry implementation not ready - using bot_impl")


@registry.command(
    name="notactive",
    description="lists players who are yet to speak",
    help_sections=[HelpSection.MISC],
    user_types=[UserType.STORYTELLER],
    required_phases=[GamePhase.DAY],  # Day only
    implemented=False
)
async def notactive_command(message: discord.Message, argument: str):
    """List players who have not spoken today."""
    raise NotImplementedError("Registry implementation not ready - using bot_impl")


@registry.command(
    name="tocheckin",
    description="lists players who are yet to check in",
    help_sections=[HelpSection.PLAYER],
    user_types=[UserType.STORYTELLER],
    required_phases=[GamePhase.NIGHT],  # Night only
    implemented=False
)
async def tocheckin_command(message: discord.Message, argument: str):
    """List players who have not checked in for the night."""
    raise NotImplementedError("Registry implementation not ready - using bot_impl")


@registry.command(
    name="cannominate",
    description="lists players who are yet to nominate or skip",
    help_sections=[HelpSection.PLAYER],
    user_types=[UserType.STORYTELLER, UserType.OBSERVER, UserType.PLAYER, UserType.PUBLIC],
    required_phases=[GamePhase.DAY],  # Day only
    implemented=False
)
async def cannominate_command(message: discord.Message, argument: str):
    """List players who have not nominated or skipped."""
    raise NotImplementedError("Registry implementation not ready - using bot_impl")


@registry.command(
    name="canbenominated",
    description="lists players who are yet to be nominated",
    help_sections=[HelpSection.PLAYER],
    user_types=[UserType.STORYTELLER, UserType.OBSERVER, UserType.PLAYER, UserType.PUBLIC],
    required_phases=[GamePhase.DAY],  # Day only
    implemented=False
)
async def canbenominated_command(message: discord.Message, argument: str):
    """List players who can still be nominated."""
    raise NotImplementedError("Registry implementation not ready - using bot_impl")


@registry.command(
    name="enabletally",
    description="enables display of whisper counts",
    help_sections=[HelpSection.CONFIGURE],
    user_types=[UserType.STORYTELLER],
    required_phases=[GamePhase.DAY, GamePhase.NIGHT],  # Any phase
    implemented=False
)
async def enabletally_command(message: discord.Message, argument: str):
    """Enable display of whisper message counts."""
    raise NotImplementedError("Registry implementation not ready - using bot_impl")


@registry.command(
    name="disabletally",
    description="disables display of whisper counts",
    help_sections=[HelpSection.CONFIGURE],
    user_types=[UserType.STORYTELLER],
    required_phases=[GamePhase.DAY, GamePhase.NIGHT],  # Any phase
    implemented=False
)
async def disabletally_command(message: discord.Message, argument: str):
    """Disable display of whisper message counts."""
    raise NotImplementedError("Registry implementation not ready - using bot_impl")


@registry.command(
    name="resetseats",
    description="Reset the seating chart to the current order",
    help_sections=[HelpSection.MISC],
    user_types=[UserType.STORYTELLER],
    required_phases=[GamePhase.DAY, GamePhase.NIGHT],  # Any phase
    implemented=False
)
async def resetseats_command(message: discord.Message, argument: str):
    """Reset the seating chart to the current order."""
    raise NotImplementedError("Registry implementation not ready - using bot_impl")


@registry.command(
    name="messagetally",
    description="Report message count tallies between pairs of players since a particular message. CAUTION: This prints publicly.",
    help_sections=[HelpSection.INFO],
    user_types=[UserType.STORYTELLER],
    arguments=[CommandArgument("message_id")],
    required_phases=[GamePhase.DAY, GamePhase.NIGHT],  # Any phase
    implemented=False
)
async def messagetally_command(message: discord.Message, argument: str):
    """Report message count tallies between pairs of players since a particular message."""
    raise NotImplementedError("Registry implementation not ready - using bot_impl")


@registry.command(
    name="history",
    description={
        UserType.STORYTELLER: "views the message history between player1 and player2, or all messages for player1",
        UserType.OBSERVER: "views the message history between player1 and player2, or all messages for player1",
        UserType.PLAYER: "views your message history with player"
    },
    help_sections=[HelpSection.INFO, HelpSection.PLAYER],
    user_types=[UserType.STORYTELLER, UserType.OBSERVER, UserType.PLAYER],
    arguments={
        UserType.STORYTELLER: [CommandArgument("player1"), CommandArgument("player2", optional=True)],
        UserType.OBSERVER: [CommandArgument("player1"), CommandArgument("player2", optional=True)],
        UserType.PLAYER: [CommandArgument("player")]
    },
    required_phases=[GamePhase.DAY, GamePhase.NIGHT],  # Any phase
    implemented=False
)
async def history_command(message: discord.Message, argument: str):
    """Show message history for a player or conversation between two players."""
    raise NotImplementedError("Registry implementation not ready - using bot_impl")


@registry.command(
    name="search",
    description={
        UserType.STORYTELLER: "views all messages containing content",
        UserType.OBSERVER: "views all messages containing content",
        UserType.PLAYER: "views all of your messages containing content"
    },
    help_sections=[HelpSection.INFO, HelpSection.PLAYER],
    user_types=[UserType.STORYTELLER, UserType.OBSERVER, UserType.PLAYER],
    arguments=[CommandArgument("content")],
    required_phases=[GamePhase.DAY, GamePhase.NIGHT],  # Any phase
    implemented=False
)
async def search_command(message: discord.Message, argument: str):
    """Search messages for text (all messages for ST/Observer, own messages for Player)."""
    raise NotImplementedError("Registry implementation not ready - using bot_impl")


@registry.command(
    name="whispers",
    description={
        UserType.STORYTELLER: "view a count of messages for the player per day",
        UserType.PLAYER: "view a count of your messages with other players per day"
    },
    help_sections=[HelpSection.INFO, HelpSection.PLAYER],
    user_types=[UserType.STORYTELLER, UserType.PLAYER],
    arguments={
        UserType.STORYTELLER: [CommandArgument("player")],
        UserType.PLAYER: []  # No arguments for players
    },
    required_phases=[GamePhase.DAY, GamePhase.NIGHT],  # Any phase
    implemented=False
)
async def whispers_command(message: discord.Message, argument: str):
    """Show whisper counts (requires player for ST, shows own for Player)."""
    raise NotImplementedError("Registry implementation not ready - using bot_impl")


@registry.command(
    name="info",
    description="views game information about player",
    help_sections=[HelpSection.INFO],
    user_types=[UserType.STORYTELLER],
    arguments=[CommandArgument("player")],
    required_phases=[GamePhase.DAY, GamePhase.NIGHT],  # Any phase
    implemented=False
)
async def info_command(message: discord.Message, argument: str):
    """Show detailed info about a player (character, alignment, votes, etc)."""
    raise NotImplementedError("Registry implementation not ready - using bot_impl")


@registry.command(
    name="votehistory",
    description="views all nominations and votes for those nominations",
    help_sections=[HelpSection.INFO],
    user_types=[UserType.STORYTELLER],
    required_phases=[GamePhase.DAY, GamePhase.NIGHT],  # Any phase
    implemented=False
)
async def votehistory_command(message: discord.Message, argument: str):
    """Show all nominations and votes for all days."""
    raise NotImplementedError("Registry implementation not ready - using bot_impl")


@registry.command(
    name="grimoire",
    description="views the grimoire",
    help_sections=[HelpSection.INFO],
    user_types=[UserType.STORYTELLER],
    required_phases=[GamePhase.DAY, GamePhase.NIGHT],  # Any phase
    implemented=False
)
async def grimoire_command(message: discord.Message, argument: str):
    """Show the current grimoire (all player roles/status)."""
    raise NotImplementedError("Registry implementation not ready - using bot_impl")


@registry.command(
    name="lastactive",
    description="Show last active times for all players",
    help_sections=[HelpSection.INFO],
    user_types=[UserType.STORYTELLER, UserType.OBSERVER],
    required_phases=[GamePhase.DAY, GamePhase.NIGHT],  # Any phase
    implemented=False
)
async def lastactive_command(message: discord.Message, argument: str):
    """Show last active times for all players."""
    raise NotImplementedError("Registry implementation not ready - using bot_impl")
