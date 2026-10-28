"""Game management commands for controlling game state and player actions."""
import textwrap

import discord

import bot_client
import global_vars
import model.game.whisper_mode
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
    global_vars.game.is_atheist = argument.lower() == "true" or argument.lower() == "t"
    #  message storytellers that atheist game is set
    await message_utils.notify_storytellers_about_action(
        message.author,
        f"{'enabled' if global_vars.game.is_atheist else 'disabled'} atheist mode"
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

#       "The Sheriff: Each day before nominations, any player may propose any other living player to be The Sheriff. They require half or more votes of all players to be elected. Once someone is elected sheriff, no one else can be proposed that day. The same player cannot be sheriff two days in a row.\n\nIf the Sheriff nominates a player for execution, the vote count starts at 1."

@registry.command(
    name="sheriff",
    description="sets the sheriff for the day. Use `-f`/`--force` before player to override an already-set sheriff. The sheriff can nominate a player for execution, and their vote counts as 1. will show the current sheriff if no argument is supplied",
    help_sections=[HelpSection.COMMON, HelpSection.DAY],
    user_types=[UserType.STORYTELLER],
    arguments=[CommandArgument(("-f", "--force"), optional=True), CommandArgument("player", optional=True)],
    required_phases=[GamePhase.DAY],  # Day only
    implemented=True
)
async def set_sheriff(message: discord.Message, argument: str):
    argument = (argument or "").strip()

    # No argument: display current sheriff status
    if not argument:
        if global_vars.game.sheriff is not None:
            await message_utils.safe_send(message.author, f"The Sheriff for today is {global_vars.game.sheriff.display_name}.")
        else:
            await message_utils.safe_send(message.author, "A Sheriff has not been elected yet today.")
        return

    force_override = False
    player_argument = argument

    if argument.startswith("-"):
        split_argument = argument.split(maxsplit=1)
        flag = split_argument[0].lower()

        if flag in ("-f", "--force"):
            force_override = True
            if len(split_argument) < 2 or not split_argument[1].strip():
                await message_utils.safe_send(
                    message.author,
                    "Usage: `@sheriff [--force|-f] [player]`\n"
                    "Use `@sheriff` to view current status, or `@sheriff -f <player>` to override."
                )
                return
            player_argument = split_argument[1].strip()

    if global_vars.game.sheriff is not None and not force_override:
        await message_utils.safe_send(
            message.author,
            f"The sheriff for today is already set to {global_vars.game.sheriff.display_name}."
        )
        return

    player = player_utils.who(player_argument)
    if player is None:
        await message_utils.safe_send(message.author, f"Could not find a living player named '{player_argument}'.")
        return

    if player.is_ghost:
        await message_utils.safe_send(message.author, f"{player.display_name} is dead and cannot be The Sheriff.")
        return

    if global_vars.game.previous_sheriff is not None and player is global_vars.game.previous_sheriff:
        await message_utils.safe_send(
            message.author,
            f"{player.display_name} was The Sheriff yesterday and cannot be The Sheriff two days in a row."
        )
        return

    if force_override and global_vars.game.sheriff_announcement_message_id is not None:
        try:
            old_announcement = await global_vars.channel.fetch_message(global_vars.game.sheriff_announcement_message_id)
            await old_announcement.unpin()
        except discord.errors.NotFound:
            pass
        except discord.errors.DiscordServerError:
            pass

    global_vars.game.sheriff = player
    announcement = await message_utils.safe_send(
        global_vars.channel,
        f"{player.display_name} has been elected as The Sheriff for today. "
        f"If they nominate a player for execution, the vote count starts at 1."
    )
    if announcement:
        await announcement.pin()
        global_vars.game.sheriff_announcement_message_id = announcement.id
    await message_utils.notify_storytellers_about_action(
        message.author,
        f"has set {player.display_name} as The Sheriff for today"
    )
