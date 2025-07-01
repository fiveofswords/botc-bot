"""
Utility functions for player management.
"""

import asyncio
from typing import List, Optional, Sequence, TypeVar

import discord

import bot_client
import global_vars
import model.player
from model import game
from utils import message_utils

T = TypeVar('T')


def is_player(member: discord.Member) -> bool:
    """
    Check if a Discord member is a player in the current game.
    
    Args:
        member: The member to check
        
    Returns:
        True if the member is a player, False otherwise
    """
    return global_vars.player_role in member.roles


def find_player_by_nick(nick: str) -> Optional[model.player.Player]:
    """
    Find a player by their display name (case-insensitive).
    
    Args:
        nick: The nickname/display name to search for
        
    Returns:
        The player object if found, None otherwise
    """
    nick = nick.lower()
    
    # Try exact match
    for player in global_vars.game.seatingOrder:
        if player.display_name.lower() == nick:
            return player
            
    # Try partial match
    for player in global_vars.game.seatingOrder:
        if nick in player.display_name.lower():
            return player
            
    return None


def who_by_id(user_id: int) -> Optional[model.player.Player]:
    """
    Find a player by their Discord user ID.
    
    Args:
        user_id: The Discord user ID
        
    Returns:
        The player object if found, None otherwise
    """
    for player in global_vars.game.seatingOrder:
        if player.user.id == user_id:
            return player
    return None


def who_by_name(name: str) -> Optional[model.player.Player]:
    """
    Find a player by their name.
    
    Args:
        name: The name to search for
        
    Returns:
        The player object if found, None otherwise
    """
    return find_player_by_nick(name)


def who_by_character(character_name: str) -> Optional[model.player.Player]:
    """
    Find a player by their character name.
    
    Args:
        character_name: The character name to search for
        
    Returns:
        The player object if found, None otherwise
    """
    character_name = character_name.lower()
    for player in global_vars.game.seatingOrder:
        if player.character.role_name.lower() == character_name:
            return player
    return None


def who(arg) -> Optional[model.player.Player]:
    """
    Find a player by various identifiers.
    
    Args:
        arg: The identifier (ID, name, or Member)
        
    Returns:
        The player object if found, None otherwise
    """
    if isinstance(arg, int):
        return who_by_id(arg)
    elif isinstance(arg, str):
        if arg.isdigit():
            return who_by_id(int(arg))
        player = who_by_name(arg)
        if player:
            return player
        return who_by_character(arg)
    elif isinstance(arg, discord.Member):
        return who_by_id(arg.id)
    return None


def get_neighbors(player: model.player.Player) -> List[model.player.Player]:
    """
    Get the neighboring players for a given player.
    
    Args:
        player: The player to get neighbors for
        
    Returns:
        List containing the player's neighbors (left and right)
    """
    if player not in global_vars.game.seatingOrder:
        return []
    
    index = global_vars.game.seatingOrder.index(player)
    result = []
    
    # Find alive left neighbor
    for i in range(1, len(global_vars.game.seatingOrder)):
        left_index = (index - i) % len(global_vars.game.seatingOrder)
        left_neighbor = global_vars.game.seatingOrder[left_index]
        if not left_neighbor.is_ghost:
            result.append(left_neighbor)
            break
    
    # Find alive right neighbor
    for i in range(1, len(global_vars.game.seatingOrder)):
        right_index = (index + i) % len(global_vars.game.seatingOrder)
        right_neighbor = global_vars.game.seatingOrder[right_index]
        if not right_neighbor.is_ghost:
            result.append(right_neighbor)
            break
    
    return result


async def check_and_print_if_one_or_zero_to_check_in() -> None:
    """Check and notify storytellers if only one or zero players need to check in."""
    from model.player import STORYTELLER_ALIGNMENT
    
    not_checked_in = [
        player
        for player in global_vars.game.seatingOrder
        if not player.has_checked_in and player.alignment != STORYTELLER_ALIGNMENT
    ]
    
    if len(not_checked_in) == 1:
        for member in global_vars.gamemaster_role.members:
            await message_utils.safe_send(
                member, 
                f"Just waiting on {not_checked_in[0].display_name} to check in."
            )
    elif len(not_checked_in) == 0:
        for member in global_vars.gamemaster_role.members:
            await message_utils.safe_send(member, "Everyone has checked in!")


def get_player(user) -> Optional[model.player.Player]:
    """
    Returns the Player object corresponding to user.
    
    Args:
        user: The Discord user
        
    Returns:
        The Player object if found, None otherwise
    """
    if global_vars.game is game.NULL_GAME:
        return None

    for person in global_vars.game.seatingOrder:
        if person.user == user:
            return person

    return None


async def generate_possibilities(text: str, people: Sequence[T]) -> List[T]:
    """
    Generates possible users with name or nickname matching text.
    
    Args:
        text: The text to match against
        people: The sequence of people to search through
        
    Returns:
        List of matching people
    """
    possibilities = []
    for person in people:
        if (
                person.display_name is not None and text.lower() in person.display_name.lower()
        ) or text.lower() in person.name.lower():
            possibilities.append(person)
    return possibilities


async def select_player(user: discord.User, text: str, possibilities: Sequence[T]) -> Optional[T]:
    """
    Finds a player from players matching a string.
    
    Args:
        user: The Discord user making the selection
        text: The text to match
        possibilities: The sequence of possible matches
        
    Returns:
        The selected player if found, None otherwise
    """
    new_possibilities = await generate_possibilities(text, possibilities)

    # If no users found
    if len(new_possibilities) == 0:
        await message_utils.safe_send(user, "User {} not found. Try again!".format(text))
        return None

    # If exactly one user found
    elif len(new_possibilities) == 1:
        return new_possibilities[0]

    # If too many users found
    elif len(new_possibilities) > 1:
        return await choices(user, new_possibilities, text)


async def choices(user: discord.User, possibilities: List[model.player.Player], text: str) -> Optional[
    model.player.Player]:
    """
    Clarifies which user is intended when there are multiple matches.
    
    Args:
        user: The Discord user making the choice
        possibilities: List of possible players
        text: The original search text
        
    Returns:
        The chosen player if selected, None otherwise
    """
    # Generate clarification message
    if text == "":
        message_text = "Who do you mean? or use 'cancel'"
    else:
        message_text = "Who do you mean by {}? or use 'cancel'".format(text)
    for index, person in enumerate(possibilities):
        message_text += "\n({}). {}".format(
            index + 1, person.display_name if person.display_name else person.name
        )

    # Request clarification from user
    reply = await message_utils.safe_send(user, message_text)
    try:
        choice = await bot_client.client.wait_for(
            "message",
            check=(lambda x: x.author == user and x.channel == reply.channel),
            timeout=200,
        )
    except asyncio.TimeoutError:
        await message_utils.safe_send(user, "Timed out.")
        return None

    # Cancel
    if choice.content.lower() == "cancel":
        await message_utils.safe_send(user, "Action cancelled!")
        return None

    # If a is an int
    try:
        return possibilities[int(choice.content) - 1]

    # If a is a name
    except Exception:
        return await select_player(user, choice.content, possibilities)


async def active_in_st_chat(user):
    """
    Makes user active in storyteller chat.
    
    Args:
        user: The Discord user
    """
    person: model.player.Player = get_player(user)

    if not person:
        return

    # updates last active timestamp when posting in ST chat.
    person.update_last_active()

    if person.has_checked_in or global_vars.game.isDay:
        return

    person.has_checked_in = True
    await check_and_print_if_one_or_zero_to_check_in()


async def make_active(user):
    """
    Makes user active during the day.
    
    Args:
        user: The Discord user
    """
    if not get_player(user):
        return

    person = get_player(user)
    person.update_last_active()

    if person.is_active or not global_vars.game.isDay:
        return

    person.is_active = True
    from model.player import STORYTELLER_ALIGNMENT

    notActive = [
        player
        for player in global_vars.game.seatingOrder
        if player.is_active == False and player.alignment != STORYTELLER_ALIGNMENT
    ]
    if len(notActive) == 1:
        for memb in global_vars.gamemaster_role.members:
            await message_utils.safe_send(
                memb, "Just waiting on {} to speak.".format(notActive[0].display_name)
            )
    if len(notActive) == 0:
        for memb in global_vars.gamemaster_role.members:
            await message_utils.safe_send(memb, "Everyone has spoken!")


async def cannot_nominate(user):
    """
    Uses user's nomination.
    
    Args:
        user: The Discord user
    """
    player = get_player(user)
    if player is None:
        return
    player.can_nominate = False
    can_nominate = [
        player
        for player in global_vars.game.seatingOrder
        if player.can_nominate == True
           and player.has_skipped == False
           and player.is_ghost == False
    ]
    if len(can_nominate) == 1:
        for memb in global_vars.gamemaster_role.members:
            await message_utils.safe_send(
                memb,
                "Just waiting on {} to nominate or skip.".format(can_nominate[0].display_name),
            )
    if len(can_nominate) == 0:
        for memb in global_vars.gamemaster_role.members:
            await message_utils.safe_send(memb, "Everyone has nominated or skipped!")


async def warn_missing_player_channels(channel_to_send, players_missing_channels):
    """
    Warn about missing player channels.
    
    Args:
        channel_to_send: The channel to send the warning to
        players_missing_channels: List of players missing channels
    """
    plural = len(players_missing_channels) > 1
    chan = "channels" if plural else "a channel"
    playz = "those players" if plural else "that player"
    await message_utils.safe_send(channel_to_send,
                                  f"Missing {chan} for: {', '.join([x.display_name for x in players_missing_channels])}.  Please run `@welcome` for {playz} to create {chan} for them.")
