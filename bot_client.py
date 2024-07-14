from __future__ import annotations

import os

import discord
import logging


_member_cache: discord.MemberCacheFlags
client: discord.Client
logger: logging.Logger
token: str

logger = logging.getLogger("discord")
logger.setLevel(logging.WARNING)
handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="w")
handler.setFormatter(
    logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s")
)
logger.addHandler(handler)


try:
    _member_cache = discord.MemberCacheFlags(
        # Whether to cache members with a status. Members that go offline are no longer cached.
        online=True,
        # Whether to cache members that are in voice. Members that leave voice are no longer cached.
        voice=True,
        # Whether to cache members that joined the guild or are chunked as part of the initial log in flow.
        # Members that leave the guild are no longer cached.
        joined=True,
    )
except TypeError:
    # online is not a valid flag name
    _member_cache = discord.MemberCacheFlags(
        voice=True,
        joined=True
    )

_intents = discord.Intents.all()
_intents.members = True
_intents.presences = True

client = discord.Client(
    intents=_intents, member_cache_flags=_member_cache
)  # discord client

# Read API Token
with open(os.path.dirname(os.path.realpath(__file__)) + "/token.txt") as tokenfile:
    token = tokenfile.readline().strip()




