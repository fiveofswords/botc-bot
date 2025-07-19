import re

import discord

import bot_client
import global_vars
import model.settings


class ChannelManager:
    """Encapsulates logic for managing Discord Channels."""

    _client: discord.Client
    _server: discord.Guild
    _in_play_category: discord.CategoryChannel | None
    _out_of_play_category: discord.CategoryChannel | None
    _hands_channel: discord.TextChannel
    _observer_channel: discord.TextChannel
    _info_channel: discord.TextChannel
    _whisper_channel: discord.TextChannel
    _town_square_channel: discord.TextChannel
    _st_role: discord.Role
    _channel_suffix: str

    def __init__(self, client: discord.Client):
        self._client = client
        self._server = global_vars.server
        self._in_play_category = global_vars.game_category
        self._out_of_play_category = global_vars.out_of_play_category
        self._hands_channel = global_vars.hands_channel
        self._observer_channel = global_vars.observer_channel
        self._info_channel = global_vars.info_channel
        self._whisper_channel = global_vars.whisper_channel
        self._town_square_channel = global_vars.channel
        self._channel_suffix = global_vars.channel_suffix
        self._st_role = global_vars.gamemaster_role

    async def create_channel(self, game_settings: model.settings.GameSettings,
                             player: discord.Member) -> discord.TextChannel:
        """
        Creates a new text for the given player, and puts it in the out of play category.
        """
        cleaned_display_name = self._cleanup_display_name(player)
        # Create the new channel with the player's name
        new_channel = await self._out_of_play_category.create_text_channel(
            name=f"👤{cleaned_display_name}-x-{self._channel_suffix}",
            overwrites={
                self._server.default_role: discord.PermissionOverwrite(read_messages=False, send_messages=False),
                self._st_role: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                self._client.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                player: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            })
        bot_client.logger.info(f"Channel {new_channel.name} has been created.")
        game_settings.set_st_channel(player.id, new_channel.id).save()
        return new_channel

    @staticmethod
    def _cleanup_display_name(player):
        # Remove any text in parentheses
        cleaned_display_name = re.sub(r'\(.*?\)', '', player.display_name)
        # Replace spaces and hyphens with underscores
        cleaned_display_name = re.sub(r'[\s-]', '_', cleaned_display_name)
        # Remove leading and trailing whitespace
        cleaned_display_name = cleaned_display_name.strip()
        # Remove trailing underscores
        cleaned_display_name = cleaned_display_name.rstrip('_')
        return cleaned_display_name

    async def set_ghost(self, channel_id: int):
        """
        Toggles from '👤' to '👻' in the channel name for the given channel ID.

        Parameters:
        - channel_id: The ID of the channel to update.
        """
        # Retrieve the channel object using the channel ID
        channel = self._client.get_channel(channel_id)
        if channel is None:
            bot_client.logger.info(f"Channel with ID {channel_id} not found.")
            return

        new_name = None
        if channel is not None:
            # Check and replace '👤' with '👻' or vice versa
            if "👤" in channel.name:
                new_name = channel.name.replace("👤", "👻")
            elif "👻" in channel.name:
                bot_client.logger.info("Player is currently 👻 and not 👤.")
            else:
                bot_client.logger.warning("No emoji found to toggle.")
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
            bot_client.logger.info(f"Channel with ID {channel_id} not found.")
            return

        new_name = None
        if channel is not None:
            # Check and replace '👤' with '👻' or vice versa
            if "👻" in channel.name:
                new_name = channel.name.replace("👻", "👤")
            elif "👤" in channel.name:
                bot_client.logger.info("Player is currently 👤 and not 👻.")
            else:
                bot_client.logger.warning("No emoji found to toggle.")
                return

            # Update the channel name
            if new_name:
                await channel.edit(name=new_name)

    async def setup_channels_in_order(self, ordered_player_channels: list[discord.TextChannel]):
        ordered_channels: list[discord.TextChannel] = [self._hands_channel, self._observer_channel,
                                                       self._info_channel,
                                                       self._whisper_channel] + ordered_player_channels + [
                                                  self._town_square_channel]
        ordered_channels_set = set(ordered_channels)
        to_move_out: list[discord.TextChannel] = [channel for channel in self._in_play_category.channels if
                                                  channel not in ordered_channels_set]
        to_move_in: list[discord.TextChannel] = [channel for channel in ordered_channels if
                                                 channel.category != self._in_play_category]

        for channel in to_move_in:
            if channel.category != self._in_play_category:
                await channel.move(category=self._in_play_category, end=True)
                bot_client.logger.debug(f"Channel {channel.name} has been moved to In Play category.")
            else:
                bot_client.logger.debug(f"Channel {channel.name} is already in the correct category.")

        # Move unused channels out of play
        for channel in to_move_out:
            await channel.move(category=self._out_of_play_category, end=True)
            bot_client.logger.debug(f"Channel {channel.name} has been moved to Out of Play category.")


        num_needing_changed = None
        attempt_num = 1
        while attempt_num < 5:
            # ordered_channels = [
            #     self._client.get_channel(channel.id)
            #     for channel in ordered_channels
            # ]
            #
            # positions can have gaps, so sorting and getting indexes for repositioning
            sorted_positions = sorted([c.position for c in ordered_channels])
            current_index = {p: i for i, p in enumerate(sorted_positions)}
            current_position_for_index = {i: p for i, p in enumerate(sorted_positions)}

            # Find the channel with the largest distance from its desired position
            distance_desired_and_channel = [
                (abs(current_index[c.position] - index), index, c)
                for index, c in enumerate(ordered_channels)
                if current_index[c.position] != index
            ]

            # keeps track of if the number of channels needing to be changed hasn't changed
            # if it hasn't changed, and there's still channels in the wrong position,
            # then stop after 5 attempts
            new_num_needing_changed = len(distance_desired_and_channel)
            if new_num_needing_changed == num_needing_changed:
                attempt_num += 1
            else:
                num_needing_changed = new_num_needing_changed
                attempt_num = 1
            if not distance_desired_and_channel:
                break  # All channels are in the correct position

            # Move the most out-of-place channel
            _, idx, channel = max(distance_desired_and_channel)

            # discord channels are 1 indexed
            await channel.edit(position=current_position_for_index[idx] + 1)
            bot_client.logger.debug(
                f"{channel.name} has been moved to position {idx} of {self._in_play_category.name}.")
        else:
            bot_client.logger.warning("Channel positions could not be set correctly after 5 attempts.")
            return False
        return True
#
