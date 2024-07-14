from __future__ import annotations

from typing import Optional, Union, TYPE_CHECKING

from discord import Guild, ForumChannel, TextChannel, CategoryChannel, Role

if TYPE_CHECKING:
    from bot_impl import Game

# The following are global variables that are used throughout the bot from a global context

server: Optional[Guild] = None
channel: Optional[Union[ForumChannel, TextChannel, CategoryChannel]] = None
whisper_channel: Optional[Union[ForumChannel, TextChannel, CategoryChannel]] = None
player_role: Optional[Role] = None
traveler_role: Optional[Role] = None
ghost_role: Optional[Role] = None
dead_vote_role: Optional[Role] = None
gamemaster_role: Optional[Role] = None
inactive_role: Optional[Role] = None
observer_role: Optional[Role] = None
game: Optional[Game] = None
