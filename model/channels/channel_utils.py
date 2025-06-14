from __future__ import annotations

from discord import TextChannel

import global_vars
from bot_client import client
from utils import message_utils
from . import ChannelManager


async def reorder_channels(st_channels: list[TextChannel]):
    for st in global_vars.gamemaster_role.members:
        await message_utils.safe_send(st, "Setting up channels for game...")
    result = await ChannelManager(client).setup_channels_in_order(st_channels)
    if not result:
        for st in global_vars.gamemaster_role.members:
            await message_utils.safe_send(st, "Failed to set up channels. Please review the channel order.")
        return
    for st in global_vars.gamemaster_role.members:
        await message_utils.safe_send(st, "Channels setup successfully!")
