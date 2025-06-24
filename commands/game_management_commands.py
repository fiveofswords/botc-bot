"""Game management commands for controlling game state and player actions."""
import textwrap

import discord

import bot_client
import global_vars
import utils.game_utils
from commands.command_enums import HelpSection, UserType, GamePhase
from commands.registry import registry, CommandArgument
from model.game.whisper_mode import to_whisper_mode
from utils import message_utils


@registry.command(
    name="startday",
    description="starts the day, killing players",
    help_sections=[HelpSection.COMMON, HelpSection.PROGRESSION],
    user_types=[UserType.STORYTELLER],
    arguments=[CommandArgument("players...", optional=True)],
    required_phases=[GamePhase.NIGHT],  # Must be night to start day
    implemented=False,
)
async def startday_command(message: discord.Message, argument: str):
    """Start the day phase, optionally killing specified players."""
    raise NotImplementedError("Registry implementation not ready - using bot_impl")


@registry.command(
    name="endday",
    description="ends the day. if there is an execution, execute is preferred",
    help_sections=[HelpSection.COMMON, HelpSection.PROGRESSION],
    user_types=[UserType.STORYTELLER],
    required_phases=[GamePhase.DAY],  # Must be day to end day
    implemented=False
)
async def endday_command(message: discord.Message, argument: str):
    """End the day phase and move to night."""
    raise NotImplementedError("Registry implementation not ready - using bot_impl")


@registry.command(
    name="kill",
    description="kills player",
    help_sections=[HelpSection.COMMON, HelpSection.GAMESTATE],
    user_types=[UserType.STORYTELLER],
    arguments=[CommandArgument("player")],
    required_phases=[GamePhase.DAY, GamePhase.NIGHT],  # Any phase
    implemented=False
)
async def kill_command(message: discord.Message, argument: str):
    """Kill a player."""
    raise NotImplementedError("Registry implementation not ready - using bot_impl")


@registry.command(
    name="poison",
    description="poisons player",
    help_sections=[HelpSection.COMMON, HelpSection.GAMESTATE],
    user_types=[UserType.STORYTELLER],
    arguments=[CommandArgument("player")],
    required_phases=[GamePhase.DAY, GamePhase.NIGHT],  # Any phase
    implemented=False
)
async def poison_command(message: discord.Message, argument: str):
    """Poison a player (disable their ability)."""
    raise NotImplementedError("Registry implementation not ready - using bot_impl")


@registry.command(
    name="unpoison",
    description="unpoisons player",
    help_sections=[HelpSection.COMMON, HelpSection.GAMESTATE],
    user_types=[UserType.STORYTELLER],
    arguments=[CommandArgument("player")],
    required_phases=[GamePhase.DAY, GamePhase.NIGHT],  # Any phase
    implemented=False
)
async def unpoison_command(message: discord.Message, argument: str):
    """Remove poison from a player (re-enable their ability)."""
    raise NotImplementedError("Registry implementation not ready - using bot_impl")


@registry.command(
    name="startgame",
    description="starts the game",
    help_sections=[HelpSection.COMMON, HelpSection.PROGRESSION],
    user_types=[UserType.STORYTELLER],
    required_phases=[],  # No game needed (creates game)
    implemented=False
)
async def startgame_command(message: discord.Message, argument: str):
    """Start a new game."""
    raise NotImplementedError("Registry implementation not ready - using bot_impl")


@registry.command(
    name="endgame",
    description="ends the game, with winner team",
    help_sections=[HelpSection.COMMON, HelpSection.PROGRESSION],
    user_types=[UserType.STORYTELLER],
    arguments=[CommandArgument(("good", "evil", "tie"))],
    required_phases=[GamePhase.DAY, GamePhase.NIGHT],  # Any phase
    implemented=False
)
async def endgame_command(message: discord.Message, argument: str):
    """End the current game and announce winner."""
    raise NotImplementedError("Registry implementation not ready - using bot_impl")


@registry.command(
    name="exile",
    description="exiles traveler",
    help_sections=[HelpSection.COMMON, HelpSection.GAMESTATE],
    user_types=[UserType.STORYTELLER],
    arguments=[CommandArgument("traveler")],
    required_phases=[GamePhase.DAY, GamePhase.NIGHT],  # Any phase
    implemented=False
)
async def exile_command(message: discord.Message, argument: str):
    """Exile a traveler from the game."""
    raise NotImplementedError("Registry implementation not ready - using bot_impl")


@registry.command(
    name="whispermode",
    description="sets whisper mode",
    help_sections=[HelpSection.CONFIGURE],
    user_types=[UserType.STORYTELLER],
    arguments=[CommandArgument(("all", "neighbors", "storytellers"))],
    required_phases=[GamePhase.DAY, GamePhase.NIGHT],  # Any phase
)
async def whispermode_command(message: discord.Message, argument: str):
    """Set whisper mode for the game."""
    new_mode = to_whisper_mode(argument)

    if new_mode:
        global_vars.game.whisper_mode = new_mode
        await utils.game_utils.update_presence(bot_client.client)
        #  for each gamemaster let them know
        await message_utils.notify_storytellers_about_action(
            message.author,
            f"has set whisper mode to {global_vars.game.whisper_mode}"
        )
    else:
        await message_utils.safe_send(message.author,
                                      "Invalid whisper mode: {}\nUsage is `@whispermode [all/neighbors/storytellers]`".format(
                                          argument))


@registry.command(
    name="setatheist",
    description="sets whether the atheist is on the script - this allows the storyteller to be nominated",
    help_sections=[HelpSection.CONFIGURE],
    user_types=[UserType.STORYTELLER],
    arguments=[CommandArgument(("true", "false"))],
    required_phases=[GamePhase.DAY, GamePhase.NIGHT],  # Any phase
)
async def setatheist_command(message: discord.Message, argument: str):
    """Set whether Atheist is on the script."""
    # argument is true or false
    global_vars.game.script.is_atheist = argument.lower() == "true" or argument.lower() == "t"
    #  message storytellers that atheist game is set to false
    await message_utils.notify_storytellers_about_action(
        message.author,
        f"{'enabled' if global_vars.game.script.is_atheist else 'disabled'} atheist mode"
    )


@registry.command(
    name="automatekills",
    description=textwrap.dedent("""\
    sets whether deaths are automated for certain characters (Riot, Golem, etc.).
    This is not recommended for most games, as more work is needed from the Storytellers
"""),
    help_sections=[HelpSection.CONFIGURE],
    user_types=[UserType.STORYTELLER],
    arguments=[CommandArgument(("true", "false"))],
    required_phases=[GamePhase.DAY, GamePhase.NIGHT],  # Any phase
)
async def automatekills_command(message: discord.Message, argument: str):
    """Set whether special kills are automated."""
    global_vars.game.has_automated_life_and_death = argument.lower() == "true" or argument.lower() == "t"
    await message_utils.notify_storytellers_about_action(
        message.author,
        f"{'enabled' if global_vars.game.has_automated_life_and_death else 'disabled'} automated life and death"
    )


@registry.command(
    name="setdeadline",
    description="sends a message with time in UTC as the deadline and opens nominations. The format can be HH:MM to specify a UTC time, or +HHhMMm to specify a relative time from now e.g. +3h15m; alternatively an epoch timestamp can be used - see https://www.epochconverter.com/",
    help_sections=[HelpSection.COMMON, HelpSection.DAY],
    user_types=[UserType.STORYTELLER],
    arguments=[CommandArgument("time")],
    required_phases=[GamePhase.DAY],  # Day only
    implemented=False
)
async def setdeadline_command(message: discord.Message, argument: str):
    """Set a deadline for nominations."""
    raise NotImplementedError("Registry implementation not ready - using bot_impl")
