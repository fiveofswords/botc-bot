from typing import Optional

import discord
import logging

from discord import Guild, CategoryChannel, Member, TextChannel, Client

import config
import global_vars
from model.settings import GameSettings

logger = logging.getLogger('discord')


class ChannelManager:
    """Encapsulates logic for managing Discord Channels."""

    _client: Client
    _server: Guild
    _in_play_category: Optional[CategoryChannel]
    _out_of_play_category: Optional[CategoryChannel]
    _hands_channel: TextChannel
    _observer_channel: TextChannel
    _info_channel: TextChannel
    _whisper_channel: TextChannel
    _town_square_channel: TextChannel
    _st_role: discord.Role
    _channel_suffix: str

    def __init__(self, client: Client):
        self._client = client
        self._server = global_vars.server
        self._in_play_category = global_vars.game_category
        self._out_of_play_category = global_vars.out_of_play_category
        self._hands_channel = global_vars.hands_channel
        self._observer_channel = global_vars.observer_channel
        self._info_channel = global_vars.info_channel
        self._whisper_channel = global_vars.whisper_channel
        self._town_square_channel = global_vars.channel
        self._channel_suffix = config.CHANNEL_SUFFIX
        self._st_role = global_vars.gamemaster_role

    async def create_channel(self, game_settings: GameSettings, player: Member) -> TextChannel:
        """
        Creates a new text for the given player, and puts it in the out of play category.
        """

        new_channel = await self._out_of_play_category.create_text_channel(
            name=f"{player.display_name}-x-{self._channel_suffix}",
            overwrites={
                self._server.default_role: discord.PermissionOverwrite(read_messages=False, send_messages=False),
                self._st_role: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                self._client.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                player: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            })
        logger.info(f"Channel {new_channel.name} has been created.")
        game_settings.set_st_channel(player.id, new_channel.id).save()
        return new_channel

    async def set_ghost(self, channel_id: int):
        """
        Toggles from '👤' to '👻' in the channel name for the given channel ID.

        Parameters:
        - channel_id: The ID of the channel to update.
        """
        # Retrieve the channel object using the channel ID
        channel = self._client.get_channel(channel_id)
        if channel is None:
            logger.info(f"Channel with ID {channel_id} not found.")
            return

        new_name = None
        if channel is not None:
            # Check and replace '👤' with '👻' or vice versa
            if "👤" in channel.name:
                new_name = channel.name.replace("👤", "👻")
            elif "👻" in channel.name:
                logger.info("Player is currently 👻 and not 👤.")
            else:
                logger.warning("No emoji found to toggle.")
                return

            # Update the channel name
            if new_name:
                await channel.edit(name=new_name)

    async def remove_ghost(self, channel_id: int):
        """
        Toggles from '👻' to '👤' in the channel name for the given channel ID.

        Parameters:
        - channel_id: The ID of the channel to update.
        """
        # Retrieve the channel object using the channel ID
        channel = self._client.get_channel(channel_id)
        if channel is None:
            logger.info(f"Channel with ID {channel_id} not found.")
            return

        new_name = None
        if channel is not None:
            # Check and replace '👤' with '👻' or vice versa
            if "👻" in channel.name:
                new_name = channel.name.replace("👻", "👤")
            elif "👤" in channel.name:
                logger.info("Player is currently 👤 and not 👻.")
            else:
                logger.warning("No emoji found to toggle.")
                return

            # Update the channel name
            if new_name:
                await channel.edit(name=new_name)

    async def setup_channels_in_order(self, ordered_player_channels: list[TextChannel]):
        ordered_channels: list[TextChannel] = [self._hands_channel, self._observer_channel,
                                               self._info_channel, self._whisper_channel] + ordered_player_channels + [
                                                  self._town_square_channel]

        to_move_out: list[TextChannel] = [channel for channel in self._in_play_category.channels if
                                          channel not in ordered_channels]

        # Move unused channels out of play
        for channel in to_move_out:
            await channel.move(category=self._out_of_play_category, end=True)
            logger.info(f"Channel {channel.name} has been moved to Out of Play category.")

        # Move remaining channels in play in order
        for index, channel in enumerate(ordered_channels):
            await channel.edit(category=self._in_play_category, position=index)
            logger.info(f"{channel.name} has been moved to position {index} of {self._in_play_category.name}.")
