from __future__ import annotations

import discord

from model import game

# The following are global variables that are used throughout the bot from a global context

# Guild
server: discord.Guild | None = None

# Channels
game_category: discord.CategoryChannel | None = None
hands_channel: discord.TextChannel | None = None
observer_channel: discord.TextChannel | None = None
info_channel: discord.TextChannel | None = None
whisper_channel: discord.TextChannel | None = None
channel: discord.TextChannel | None = None
out_of_play_category: discord.CategoryChannel | None = None
channel_suffix: str | None = None

# Roles
player_role: discord.Role | None = None
traveler_role: discord.Role | None = None
ghost_role: discord.Role | None = None
dead_vote_role: discord.Role | None = None
gamemaster_role: discord.Role | None = None
inactive_role: discord.Role | None = None
observer_role: discord.Role | None = None

# Game
game: game.Game | None = None
