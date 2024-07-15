import discord
import logging

logger = logging.getLogger('discord')


class ChannelManager:
    """Encapsulates logic for managing Discord Channels."""

    _client: discord.client.Client

    def __init__(self, client: discord.client.Client):
        self._client = client

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

    async def move_channel_to_category(self, channel_id: int, category_id: int) -> bool:
        """
        Moves a channel to a specified category.

        Parameters:
        - channel_id: The ID of the channel to move.
        - category_id: The ID of the category to move the channel into.
        """
        # Retrieve the channel and category objects using their IDs
        channel: discord.TextChannel = self._client.get_channel(channel_id)
        new_category: discord.CategoryChannel = self._client.get_channel(category_id)

        # Check if both the channel and category exist
        if channel is None or new_category is None:
            logger.info(f"Either channel with ID {channel_id} or category with ID {category_id} was not found.")
            return False

        if not isinstance(channel, discord.TextChannel):
            logger.info(f"Channel with ID {channel_id} is not a text channel.")
            return False

        if not isinstance(new_category, discord.CategoryChannel):
            logger.info(f"Category with ID {category_id} is not a category channel.")
            return False

        # Move the channel to the category
        try:
            await channel.edit(category=new_category)
            logger.info(f"Channel {channel.name} has been moved to category {new_category.name}.")
            return True
        except discord.HTTPException as e:
            logger.warning(f"An error occurred while moving channel {channel.name} to category {new_category.name}: {e}.")
            return False
