"""Player state management commands for controlling player status."""

import discord

import global_vars
import model
from commands.command_enums import HelpSection, UserType, GamePhase
from commands.registry import registry, CommandArgument
from utils import message_utils, player_utils, game_utils


@registry.command(
    name="execute",
    description="executes player",
    help_sections=[HelpSection.COMMON, HelpSection.GAMESTATE],
    user_types=[UserType.STORYTELLER],
    arguments=[CommandArgument("player")],
    required_phases=[GamePhase.DAY, GamePhase.NIGHT],  # Any phase
    implemented=False
)
async def execute_command(message: discord.Message, argument: str):
    """Execute a player (special kill, e.g. via vote)."""
    raise NotImplementedError("Registry implementation not ready - using bot_impl")


@registry.command(
    name="revive",
    description="revives player",
    help_sections=[HelpSection.GAMESTATE],
    user_types=[UserType.STORYTELLER],
    arguments=[CommandArgument("player")],
    required_phases=[GamePhase.DAY, GamePhase.NIGHT],  # Any phase
    implemented=False
)
async def revive_command(message: discord.Message, argument: str):
    """Revive a dead player."""
    raise NotImplementedError("Registry implementation not ready - using bot_impl")


@registry.command(
    name="givedeadvote",
    description="adds a dead vote for player",
    help_sections=[HelpSection.GAMESTATE],
    user_types=[UserType.STORYTELLER],
    arguments=[CommandArgument("player")],
    required_phases=[GamePhase.DAY, GamePhase.NIGHT],  # Any phase
    implemented=False
)
async def givedeadvote_command(message: discord.Message, argument: str):
    """Give a dead vote to a player."""
    raise NotImplementedError("Registry implementation not ready - using bot_impl")


@registry.command(
    name="removedeadvote",
    description="removes a dead vote from player. not necessary for ordinary usage",
    help_sections=[HelpSection.GAMESTATE],
    user_types=[UserType.STORYTELLER],
    arguments=[CommandArgument("player")],
    required_phases=[GamePhase.DAY, GamePhase.NIGHT],  # Any phase
    implemented=False
)
async def removedeadvote_command(message: discord.Message, argument: str):
    """Remove a dead vote from a player."""
    raise NotImplementedError("Registry implementation not ready - using bot_impl")


@registry.command(
    name="changerole",
    description="changes player's role",
    help_sections=[HelpSection.GAMESTATE],
    user_types=[UserType.STORYTELLER],
    arguments=[CommandArgument("player")],
    required_phases=[GamePhase.DAY, GamePhase.NIGHT],  # Any phase
    implemented=False
)
async def changerole_command(message: discord.Message, argument: str):
    """Change a player's role."""
    raise NotImplementedError("Registry implementation not ready - using bot_impl")


@registry.command(
    name="changealignment",
    description="changes player's alignment",
    help_sections=[HelpSection.GAMESTATE],
    user_types=[UserType.STORYTELLER],
    arguments=[CommandArgument("player")],
    required_phases=[GamePhase.DAY, GamePhase.NIGHT],  # Any phase
    implemented=False
)
async def changealignment_command(message: discord.Message, argument: str):
    """Change a player's alignment."""
    raise NotImplementedError("Registry implementation not ready - using bot_impl")


@registry.command(
    name="changeability",
    description="changes player's ability, if applicable to their character (ex apprentice)",
    help_sections=[HelpSection.GAMESTATE],
    user_types=[UserType.STORYTELLER],
    arguments=[CommandArgument("player")],
    required_phases=[GamePhase.DAY, GamePhase.NIGHT],  # Any phase
    implemented=False
)
async def changeability_command(message: discord.Message, argument: str):
    """Add a new ability to a player."""
    raise NotImplementedError("Registry implementation not ready - using bot_impl")


@registry.command(
    name="removeability",
    description="clears a player's modified ability, if applicable to their character (ex cannibal)",
    help_sections=[HelpSection.GAMESTATE],
    user_types=[UserType.STORYTELLER],
    arguments=[CommandArgument("player")],
    required_phases=[GamePhase.DAY, GamePhase.NIGHT],  # Any phase
    implemented=False
)
async def removeability_command(message: discord.Message, argument: str):
    """Remove a modified ability from a player."""
    raise NotImplementedError("Registry implementation not ready - using bot_impl")


@registry.command(
    name="checkin",
    description="Marks players as checked in for tonight. Resets each day.",
    help_sections=[HelpSection.MISC],
    user_types=[UserType.STORYTELLER],
    arguments=[CommandArgument("players")],
    required_phases=[GamePhase.NIGHT],  # Night only
    implemented=False
)
async def checkin_command(message: discord.Message, argument: str):
    """Mark players as checked in."""
    raise NotImplementedError("Registry implementation not ready - using bot_impl")


@registry.command(
    name="undocheckin",
    description="Marks players as not checked in for tonight.",
    help_sections=[HelpSection.MISC],
    user_types=[UserType.STORYTELLER],
    arguments=[CommandArgument("players")],
    required_phases=[GamePhase.NIGHT],  # Night only
    implemented=False
)
async def undocheckin_command(message: discord.Message, argument: str):
    """Mark players as not checked in."""
    raise NotImplementedError("Registry implementation not ready - using bot_impl")


@registry.command(
    name="makeinactive",
    description="marks player as inactive. must be done in all games player is participating in",
    help_sections=[HelpSection.MISC],
    user_types=[UserType.STORYTELLER],
    arguments=[CommandArgument("player")],
    required_phases=[GamePhase.DAY, GamePhase.NIGHT],  # Any phase
    implemented=False
)
async def makeinactive_command(message: discord.Message, argument: str):
    """Mark a player as inactive."""
    raise NotImplementedError("Registry implementation not ready - using bot_impl")


@registry.command(
    name="undoinactive",
    description="undoes an inactivity mark. must be done in all games player is participating in",
    help_sections=[HelpSection.MISC],
    user_types=[UserType.STORYTELLER],
    arguments=[CommandArgument("player")],
    required_phases=[GamePhase.DAY, GamePhase.NIGHT],  # Any phase
    implemented=False
)
async def undoinactive_command(message: discord.Message, argument: str):
    """Mark a player as active again."""
    raise NotImplementedError("Registry implementation not ready - using bot_impl")


@registry.command(
    name="addtraveler",
    description="adds player as a traveler",
    help_sections=[HelpSection.MISC],
    aliases=["addtraveller"],
    user_types=[UserType.STORYTELLER],
    arguments=[CommandArgument("player")],
    required_phases=[GamePhase.DAY, GamePhase.NIGHT],  # Any phase
    implemented=False
)
async def addtraveler_command(message: discord.Message, argument: str):
    """Add a player as a traveler."""
    raise NotImplementedError("Registry implementation not ready - using bot_impl")


@registry.command(
    name="removetraveler",
    description="removes traveler from the game",
    help_sections=[HelpSection.MISC],
    aliases=["removetraveller"],
    user_types=[UserType.STORYTELLER],
    arguments=[CommandArgument("traveler")],
    required_phases=[GamePhase.DAY, GamePhase.NIGHT],  # Any phase
    implemented=False
)
async def removetraveler_command(message: discord.Message, argument: str):
    """Remove a traveler from the game."""
    raise NotImplementedError("Registry implementation not ready - using bot_impl")


@registry.command(
    name="reseat",
    description="reseats the game",
    help_sections=[HelpSection.MISC],
    user_types=[UserType.STORYTELLER],
    required_phases=[GamePhase.DAY, GamePhase.NIGHT],  # Any phase
    implemented=False
)
async def reseat_command(message: discord.Message, argument: str):
    """Change the seating order."""
    raise NotImplementedError("Registry implementation not ready - using bot_impl")


@registry.command(
    name="swapseats",
    description="swaps two players' seats",
    help_sections=[HelpSection.MISC],
    user_types=[UserType.STORYTELLER],
    required_phases=[GamePhase.DAY, GamePhase.NIGHT],  # Any phase
    arguments=[CommandArgument("player1"), CommandArgument("player2")],
)
async def swapseats_command(message: discord.Message, argument: str):
    """Swaps the seats of two players."""
    player_names = argument.split()
    if len(player_names) != 2:
        await message_utils.safe_send(message.author, "There must be exactly two player arguments.")
        return

    game = global_vars.game

    async def get_player(player_name):
        return await player_utils.select_player(message.author, player_name, game.seatingOrder)

    player1, player2 = await get_player(player_names[0]), await get_player(player_names[1])
    if not player1 or not player2:
        return

    if player1.user.id == player2.user.id:
        await message_utils.safe_send(message.author, "You cannot swap a player with themselves.")
        return

    # Swap the players in the seating order
    new_seating = game.seatingOrder.copy()
    index1, index2 = new_seating.index(player1), new_seating.index(player2)
    new_seating[index1], new_seating[index2] = new_seating[index2], new_seating[index1]

    await game.reseat(new_seating)
    await message_utils.notify_storytellers_about_action(
        message.author, f"Swapped seats of {player1.user.name} and {player2.user.name}."
    )

    if game is not model.game.NULL_GAME:
        game_utils.backup("current_game.pckl")


@registry.command(
    name="welcome",
    description="Send welcome message to a player",
    help_sections=[HelpSection.MISC],
    user_types=[UserType.STORYTELLER],
    arguments=[CommandArgument("player")],
    required_phases=[],  # No game needed
    implemented=False
)
async def welcome_command(message: discord.Message, argument: str):
    """Send welcome message to a player."""
    raise NotImplementedError("Registry implementation not ready - using bot_impl")
