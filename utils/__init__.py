"""
Utility functions for the BOTC bot.

This module provides utility functions for character abilities, game state management,
message handling, and player operations.
"""

# Make modules available for direct import
from . import interaction_utils
from . import text_utils
# Import commonly used functions
from .character_utils import has_ability, the_ability, str_to_class
from .game_utils import remove_backup, update_presence, backup, load
from .message_utils import safe_send, safe_send_dm, notify_storytellers
from .player_utils import (
    who, find_player_by_nick, is_player, get_player, generate_possibilities,
    choices, select_player, active_in_st_chat, make_active, cannot_nominate,
    warn_missing_player_channels, check_and_print_if_one_or_zero_to_check_in
)

__all__ = [
    # Character utilities
    'has_ability',
    'the_ability',
    'str_to_class',

    # Game utilities  
    'remove_backup',
    'update_presence',
    'backup',
    'load',

    # Message utilities
    'safe_send',
    'safe_send_dm',
    'notify_storytellers',

    # Player utilities
    'who',
    'find_player_by_nick',
    'is_player',
    'get_player',
    'generate_possibilities',
    'choices',
    'select_player',
    'active_in_st_chat',
    'make_active',
    'cannot_nominate',
    'warn_missing_player_channels',
    'check_and_print_if_one_or_zero_to_check_in'
]
