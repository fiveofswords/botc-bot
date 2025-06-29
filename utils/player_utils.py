"""
Utility functions for player management.
"""

from typing import List, Optional

import discord

import global_vars
import model.player
from utils import message_utils


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
    not_checked_in = [
        player
        for player in global_vars.game.seatingOrder
        if not player.has_checked_in and player.alignment != "neutral"
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
