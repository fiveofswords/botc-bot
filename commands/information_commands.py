"""Information and utility commands for game status and settings."""
import inspect
import itertools
from collections import OrderedDict

import discord

import global_vars
import model
from commands.command_enums import HelpSection, UserType, GamePhase
from commands.registry import registry, CommandArgument
from model import Player
from utils import message_utils, player_utils


@registry.command(
    name="clear",
    description="returns whitespace",
    help_sections=[HelpSection.PLAYER],
    user_types=[UserType.STORYTELLER, UserType.OBSERVER, UserType.PLAYER, UserType.PUBLIC],
    required_phases=[],  # No game needed
)
async def clear_command(message: discord.Message, argument: str):
    """Clear the chat window with blank lines."""
    # Clears history
    await message_utils.safe_send(message.author, "{}Clearing\n{}".format("\u200b\n" * 25, "\u200b\n" * 25))


@registry.command(
    name="notactive",
    description="lists players who are yet to speak",
    help_sections=[HelpSection.MISC],
    user_types=[UserType.STORYTELLER],
    required_phases=[GamePhase.DAY],  # Day only
)
async def notactive_command(message: discord.Message, argument: str):
    """List players who have not spoken today."""
    notActive = [
        player_obj
        for player_obj in global_vars.game.seatingOrder
        if player_obj.is_active == False and player_obj.alignment != model.player.STORYTELLER_ALIGNMENT
    ]

    if not notActive:
        await message_utils.safe_send(message.author, "Everyone has spoken!")
        return

    message_text = "These players have not spoken:"
    for player_obj in notActive:
        message_text += "\n{}".format(player_obj.display_name)

    await message_utils.safe_send(message.author, message_text)


@registry.command(
    name="tocheckin",
    description="lists players who are yet to check in",
    help_sections=[HelpSection.PLAYER],
    user_types=[UserType.STORYTELLER],
    required_phases=[GamePhase.NIGHT],  # Night only
)
async def tocheckin_command(message: discord.Message, argument: str):
    """List players who have not checked in for the night."""
    to_check_in = [
        player_obj
        for player_obj in global_vars.game.seatingOrder
        if player_obj.has_checked_in == False
    ]
    if not to_check_in:
        await message_utils.safe_send(message.author, "Everyone has checked in!")
        return

    message_text = "These players have not checked in:"
    for player_obj in to_check_in:
        message_text += "\n{}".format(player_obj.display_name)

    await message_utils.safe_send(message.author, message_text)


@registry.command(
    name="cannominate",
    description="lists players who are yet to nominate or skip",
    help_sections=[HelpSection.PLAYER],
    user_types=[UserType.STORYTELLER, UserType.OBSERVER, UserType.PLAYER, UserType.PUBLIC],
    required_phases=[GamePhase.DAY],  # Day only
)
async def cannominate_command(message: discord.Message, argument: str):
    """List players who have not nominated or skipped."""
    can_nominate = [
        player_obj
        for player_obj in global_vars.game.seatingOrder
        if player_obj.can_nominate == True
           and player_obj.has_skipped == False
           and player_obj.alignment != model.player.STORYTELLER_ALIGNMENT
           and player_obj.is_ghost == False
    ]
    if not can_nominate:
        await message_utils.safe_send(message.author, "Everyone has nominated or skipped!")
        return

    message_text = "These players have not nominated or skipped:"
    for player_obj in can_nominate:
        message_text += "\n{}".format(player_obj.display_name)

    await message_utils.safe_send(message.author, message_text)


@registry.command(
    name="canbenominated",
    description="lists players who are yet to be nominated",
    help_sections=[HelpSection.PLAYER],
    user_types=[UserType.STORYTELLER, UserType.OBSERVER, UserType.PLAYER, UserType.PUBLIC],
    required_phases=[GamePhase.DAY],  # Day only
)
async def canbenominated_command(message: discord.Message, argument: str):
    """List players who can still be nominated."""
    can_be_nominated = [
        player_obj
        for player_obj in global_vars.game.seatingOrder
        if player_obj.can_be_nominated == True
    ]
    if not can_be_nominated:
        await message_utils.safe_send(message.author, "Everyone has been nominated!")
        return

    message_text = "These players have not been nominated:"
    for player_obj in can_be_nominated:
        message_text += "\n{}".format(player_obj.display_name)

    await message_utils.safe_send(message.author, message_text)


@registry.command(
    name="enabletally",
    description="enables display of whisper counts",
    help_sections=[HelpSection.CONFIGURE],
    user_types=[UserType.STORYTELLER],
    required_phases=[GamePhase.DAY, GamePhase.NIGHT],  # Any phase
)
async def enabletally_command(message: discord.Message, argument: str):
    """Enable display of whisper message counts."""
    global_vars.game.show_tally = True
    await message_utils.notify_storytellers_about_action(message.author, "enabled the message tally")


@registry.command(
    name="disabletally",
    description="disables display of whisper counts",
    help_sections=[HelpSection.CONFIGURE],
    user_types=[UserType.STORYTELLER],
    required_phases=[GamePhase.DAY, GamePhase.NIGHT],  # Any phase
)
async def disabletally_command(message: discord.Message, argument: str):
    """Disable display of whisper message counts."""
    global_vars.game.show_tally = False
    await message_utils.notify_storytellers_about_action(message.author, "disabled the message tally")


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
    await global_vars.game.reseat(global_vars.game.seatingOrder)


@registry.command(
    name="messagetally",
    description="Report of message count tallies between pairs of players since a particular message.",
    help_sections=[HelpSection.INFO],
    user_types=[UserType.STORYTELLER],
    arguments=[CommandArgument("message_id")],
    required_phases=[GamePhase.DAY, GamePhase.NIGHT],  # Any phase
)
async def messagetally_command(message: discord.Message, argument: str):
    """Report message count tallies between pairs of players since a particular message."""
    # Sends a message tally
    if not global_vars.game.days:
        await message_utils.safe_send(message.author, "There have been no days.")
        return

    try:
        idn = int(argument)
    except ValueError:
        await message_utils.safe_send(message.author, "Invalid message ID: {}".format(argument))
        return

    try:
        origin_msg = await global_vars.channel.fetch_message(idn)
    except discord.errors.NotFound:
        await message_utils.safe_send(message.author, "Message not found by ID: {}".format(argument))
        return

    message_tally = {
        X: 0 for X in itertools.combinations(global_vars.game.seatingOrder, 2)
    }
    for person in global_vars.game.seatingOrder:
        for msg in person.message_history:
            if msg["from_player"] == person:
                if msg["time"] >= origin_msg.created_at:
                    if (person, msg["to_player"]) in message_tally:
                        message_tally[(person, msg["to_player"])] += 1
                    elif (msg["to_player"], person) in message_tally:
                        message_tally[(msg["to_player"], person)] += 1
                    else:
                        message_tally[(person, msg["to_player"])] = 1
    sorted_tally = sorted(message_tally.items(), key=lambda x: -x[1])
    message_text = "Message Tally:"
    for pair in sorted_tally:
        if pair[1] > 0:
            message_text += "\n> {person1} - {person2}: {n}".format(
                person1=pair[0][0].display_name, person2=pair[0][1].display_name, n=pair[1]
            )
        else:
            message_text += "\n> All other pairs: 0"
            break
    await message_utils.safe_send(message.author, message_text)


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
)
async def whispers_command(message: discord.Message, argument: str):
    """Show whisper counts (requires player for ST, shows own for Player)."""
    person: Player | None = None
    # If the user is a storyteller, they can specify a player to view
    if global_vars.gamemaster_role in global_vars.server.get_member(message.author.id).roles:
        argument = argument.split(" ")
        if len(argument) != 1:
            await message_utils.safe_send(message.author, "Usage: @whispers <player>")
            return
        if len(argument) == 1:
            person = await player_utils.select_player(
                message.author, argument[0], global_vars.game.seatingOrder + global_vars.game.storytellers
            )
    else:
        # If the user is a player, we get their own player object
        person = player_utils.get_player(message.author)
    if not person:
        await message_utils.safe_send(message.author,
                                      "You are not in the game. You have no message history.")
        return

    # initialize counts with zero for all players
    day = 1
    counts = OrderedDict([(player, 0) for player in global_vars.game.seatingOrder])

    for msg in person.message_history:
        if msg["day"] != day:
            # share summary and reset counts
            message_text = "Day {}\n".format(day)
            for player, count in counts.items():
                message_text += "{}: {}\n".format(player if player == "Storytellers" else player.display_name, count)
            await message_utils.safe_send(message.author, message_text)
            counts = OrderedDict([(player, 0) for player in global_vars.game.seatingOrder])
            day = msg["day"]
        if msg["from_player"] == person:
            if msg["to_player"] in counts:
                counts[msg["to_player"]] += 1
            else:
                if "Storytellers" in counts:
                    counts["Storytellers"] += 1
                else:
                    counts["Storytellers"] = 1
        else:
            counts[msg["from_player"]] += 1

    message_text = "Day {}\n".format(day)
    for player, count in counts.items():
        message_text += "{}: {}\n".format(player if player == "Storytellers" else player.display_name, count)
    await message_utils.safe_send(message.author, message_text)


@registry.command(
    name="info",
    description="views game information about player",
    help_sections=[HelpSection.INFO],
    user_types=[UserType.STORYTELLER],
    arguments=[CommandArgument("player")],
    required_phases=[GamePhase.DAY, GamePhase.NIGHT],  # Any phase
)
async def info_command(message: discord.Message, argument: str):
    """Show detailed info about a player (character, alignment, votes, etc)."""
    person = await player_utils.select_player(
        message.author, argument, global_vars.game.seatingOrder
    )
    if person is None:
        return

    base_info = inspect.cleandoc(f"""
             Player: {person.display_name}
             Character: {person.character.role_name}
             Alignment: {person.alignment}
             Alive: {not person.is_ghost}
             Dead Votes: {person.dead_votes}
             Poisoned: {person.character.is_poisoned}
             Last Active <t:{int(person.last_active)}:R> at <t:{int(person.last_active)}:t>
             Has Checked In {person.has_checked_in}
             ST Channel: {f"https://discord.com/channels/{global_vars.server.id}/{person.st_channel.id}" if person.st_channel else "None"}
             """)

    # Add Hand Status
    hand_status_info = f"Hand Status: {'Raised' if person.hand_raised else 'Lowered'}"

    # Add Preset Vote Status
    preset_vote_info = "Preset Vote: N/A (No active vote)"
    active_vote = None
    if global_vars.game.isDay and global_vars.game.days[-1].votes and not global_vars.game.days[-1].votes[-1].done:
        active_vote = global_vars.game.days[-1].votes[-1]

    if active_vote:
        preset_value = active_vote.presetVotes.get(person.user.id)
        if preset_value is None:
            preset_vote_info = "Preset Vote: None"
        elif preset_value == 0:
            preset_vote_info = "Preset Vote: No"
        elif preset_value == 1:
            preset_vote_info = "Preset Vote: Yes"
        elif preset_value == 2:  # Assuming 2 is for Banshee scream, adjust if needed
            preset_vote_info = "Preset Vote: Yes (Banshee Scream)"
        # Add more conditions if other preset_values are possible

    full_info = "\n".join([base_info, hand_status_info, preset_vote_info, person.character.extra_info()])
    await message_utils.safe_send(message.author, full_info)


@registry.command(
    name="votehistory",
    description="views all nominations and votes for those nominations",
    help_sections=[HelpSection.INFO],
    user_types=[UserType.STORYTELLER],
    required_phases=[GamePhase.DAY, GamePhase.NIGHT],  # Any phase
)
async def votehistory_command(message: discord.Message, argument: str):
    """Show all nominations and votes for all days."""
    for index, day in enumerate(global_vars.game.days):
        votes_for_day = f"Day {index + 1}\n"
        for vote in day.votes:  # type: model.Vote
            nominator_name = vote.nominator.display_name if vote.nominator else "the storytellers"
            nominee_name = vote.nominee.display_name if vote.nominee else "the storytellers"
            voters = ", ".join([voter.display_name for voter in vote.voted])
            votes_for_day += f"{nominator_name} -> {nominee_name} ({vote.votes}): {voters}\n"
        await message_utils.safe_send(message.author, f"```\n{votes_for_day}\n```")


@registry.command(
    name="grimoire",
    description="views the grimoire",
    help_sections=[HelpSection.INFO],
    user_types=[UserType.STORYTELLER],
    required_phases=[GamePhase.DAY, GamePhase.NIGHT],  # Any phase
)
async def grimoire_command(message: discord.Message, argument: str):
    """Show the current grimoire (all player roles/status)."""
    message_text = "**Grimoire:**"
    for player in global_vars.game.seatingOrder:
        message_text += f"\n{player.display_name}: {player.character.role_name}"
        if player.character.is_poisoned and player.is_ghost:
            message_text += " (Poisoned, Dead)"
        elif player.character.is_poisoned and not player.is_ghost:
            message_text += " (Poisoned)"
        elif not player.character.is_poisoned and player.is_ghost:
            message_text += " (Dead)"

    await message_utils.safe_send(message.author, message_text)


@registry.command(
    name="lastactive",
    description="Show last active times for all players",
    help_sections=[HelpSection.INFO],
    user_types=[UserType.STORYTELLER, UserType.OBSERVER],
    required_phases=[GamePhase.DAY, GamePhase.NIGHT],  # Any phase
)
async def lastactive_command(message: discord.Message, argument: str):
    """Show last active times for all players."""
    last_active = sorted(global_vars.game.seatingOrder, key=lambda p: p.last_active)
    message_text = "Last active time for these players:"
    for player in last_active:
        last_active_str = str(int(player.last_active))
        message_text += f"\n{player.display_name}:<t:{last_active_str}:R> at <t:{last_active_str}:t>"

    await message_utils.safe_send(message.author, message_text)
