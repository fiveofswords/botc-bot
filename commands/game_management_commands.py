"""Game management commands for controlling game state and player actions."""
import textwrap

import discord

import bot_client
import global_vars
import model
import model.characters
import model.game.whisper_mode
import time_utils
import utils.game_utils
from commands.command_enums import HelpSection, UserType, GamePhase
from commands.registry import registry, CommandArgument
from utils import message_utils, player_utils


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
)
async def kill_command(message: discord.Message, argument: str):
    """Kill a player."""
    person: model.Player = await player_utils.select_player(
        message.author, argument, global_vars.game.seatingOrder
    )
    if person is None:
        return

    if person.is_ghost:
        await message_utils.safe_send(message.author, "{} is already dead.".format(person.display_name))
        return

    await person.kill(force=True)
    if global_vars.game is not model.game.NULL_GAME:
        utils.game_utils.backup("current_game.pckl")


@registry.command(
    name="poison",
    description="poisons player",
    help_sections=[HelpSection.COMMON, HelpSection.GAMESTATE],
    user_types=[UserType.STORYTELLER],
    arguments=[CommandArgument("player")],
    required_phases=[GamePhase.DAY, GamePhase.NIGHT],  # Any phase
)
async def poison_command(message: discord.Message, argument: str):
    """Poison a player (disable their ability)."""
    person = await player_utils.select_player(
        message.author, argument, global_vars.game.seatingOrder
    )
    if person is None:
        return

    person.character.poison()
    await message_utils.notify_storytellers_about_action(message.author,
                                                         f"poisoned {person.display_name}")


@registry.command(
    name="unpoison",
    description="unpoisons player",
    help_sections=[HelpSection.COMMON, HelpSection.GAMESTATE],
    user_types=[UserType.STORYTELLER],
    arguments=[CommandArgument("player")],
    required_phases=[GamePhase.DAY, GamePhase.NIGHT],  # Any phase
)
async def unpoison_command(message: discord.Message, argument: str):
    """Remove poison from a player (re-enable their ability)."""
    person = await player_utils.select_player(
        message.author, argument, global_vars.game.seatingOrder
    )
    if person is None:
        return

    person.character.unpoison()
    await message_utils.notify_storytellers_about_action(message.author,
                                                         f"unpoisoned {person.display_name}")


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
)
async def endgame_command(message: discord.Message, argument: str):
    """End the current game and announce winner."""
    argument = argument.lower()
    if argument not in ("good", "evil", "tie"):
        await message_utils.safe_send(message.author,
                                      "The winner must be 'good' or 'evil' or 'tie' exactly.")
        return

    winner_msg = "Good won!" if argument == "good" else "Evil won!" if argument == "evil" else ""
    await message_utils.notify_storytellers_about_action(
        message.author,
        f"{message.author.display_name} has ended the game! {winner_msg} Please wait for the bot to finish."
    )

    await global_vars.game.end(argument)
    if global_vars.game is not model.game.NULL_GAME:
        utils.game_utils.backup("current_game.pckl")


@registry.command(
    name="exile",
    description="exiles traveler",
    help_sections=[HelpSection.COMMON, HelpSection.GAMESTATE],
    user_types=[UserType.STORYTELLER],
    arguments=[CommandArgument("traveler")],
    required_phases=[GamePhase.DAY, GamePhase.NIGHT],  # Any phase
)
async def exile_command(message: discord.Message, argument: str):
    """Exile a traveler from the game."""
    person = await player_utils.select_player(
        message.author, argument, global_vars.game.seatingOrder
    )
    if person is None:
        return

    if not isinstance(person.character, model.characters.Traveler):
        await message_utils.safe_send(message.author, f"{person.display_name} is not a traveler.")
        return

    await person.character.exile(person, message.author)
    if global_vars.game is not model.game.NULL_GAME:
        utils.game_utils.backup("current_game.pckl")


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
    new_mode = model.game.whisper_mode.to_whisper_mode(argument)

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
    #  message storytellers that atheist game is set
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
    deadline = time_utils.parse_deadline(argument)

    if deadline is None:
        await message_utils.safe_send(message.author,
                                      "Unrecognized format. Please provide a deadline in the format 'HH:MM', '+[HHh][MMm]', or a Unix timestamp.")
        return

    if len(global_vars.game.days[-1].deadlineMessages) > 0:
        previous_deadline = global_vars.game.days[-1].deadlineMessages[-1]
        try:
            await (
                await global_vars.channel.fetch_message(previous_deadline)
            ).unpin()
        except discord.errors.NotFound:
            print("Missing message: ", str(previous_deadline))
        except discord.errors.DiscordServerError:
            print("Discord server error: ", str(previous_deadline))
    announcement = await message_utils.safe_send(
        global_vars.channel,
        "{}, nominations are open. The deadline is <t:{}:R> at <t:{}:t> unless someone nominates or everyone skips.".format(
            global_vars.player_role.mention,
            str(int(deadline.timestamp())),
            str(int(deadline.timestamp()))
        ),
    )
    await announcement.pin()
    global_vars.game.days[-1].deadlineMessages.append(announcement.id)
    await global_vars.game.days[-1].open_noms()
