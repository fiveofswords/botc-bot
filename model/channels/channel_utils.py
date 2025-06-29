from __future__ import annotations

import discord

import bot_client
import global_vars
from model.channels import ChannelManager
from utils import message_utils


async def reorder_channels(st_channels: list[discord.TextChannel]):
    result = await ChannelManager(bot_client.client).setup_channels_in_order(st_channels)
    if not result:
        for st in global_vars.gamemaster_role.members:
            await message_utils.safe_send(st, "Failed to set up channels. Please review the channel order.")
        return
