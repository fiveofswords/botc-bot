from __future__ import annotations

from typing import Optional

import discord

from model import game

# The following are global variables that are used throughout the bot from a global context

# Guild
server: Optional[discord.Guild] = None

# Channels
game_category: Optional[discord.CategoryChannel] = None
hands_channel: Optional[discord.TextChannel] = None
observer_channel: Optional[discord.TextChannel] = None
info_channel: Optional[discord.TextChannel] = None
whisper_channel: Optional[discord.TextChannel] = None
channel: Optional[discord.TextChannel] = None
out_of_play_category: Optional[discord.CategoryChannel] = None
channel_suffix: Optional[str] = None

# Roles
player_role: Optional[discord.Role] = None
traveler_role: Optional[discord.Role] = None
ghost_role: Optional[discord.Role] = None
dead_vote_role: Optional[discord.Role] = None
gamemaster_role: Optional[discord.Role] = None
inactive_role: Optional[discord.Role] = None
observer_role: Optional[discord.Role] = None

# Game
game: Optional[game.Game] = None
