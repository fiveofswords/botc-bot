from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from discord import Guild, TextChannel, CategoryChannel, Role

if TYPE_CHECKING:
    from bot_impl import Game

# The following are global variables that are used throughout the bot from a global context

# Guild
server: Optional[Guild] = None

# Channels
game_category: Optional[CategoryChannel] = None
hands_channel: Optional[TextChannel] = None
observer_channel: Optional[TextChannel] = None
info_channel: Optional[TextChannel] = None
whisper_channel: Optional[TextChannel] = None
channel: Optional[TextChannel] = None
out_of_play_category: Optional[CategoryChannel] = None

# Roles
player_role: Optional[Role] = None
traveler_role: Optional[Role] = None
ghost_role: Optional[Role] = None
dead_vote_role: Optional[Role] = None
gamemaster_role: Optional[Role] = None
inactive_role: Optional[Role] = None
observer_role: Optional[Role] = None

# Game
game: Optional[Game] = None
