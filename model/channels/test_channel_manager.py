import unittest
from unittest.mock import MagicMock, AsyncMock

import discord

from model.channels.channel_manager import ChannelManager


class TestChannelManager(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.mock_client = MagicMock(spec=discord.Client)
        self.mock_channel = MagicMock(spec=discord.TextChannel)
        self.mock_category = MagicMock(spec=discord.CategoryChannel)
        self.channel_manager = ChannelManager(self.mock_client)

    # ==============================
    # Tests for toggle_ghost
    # ==============================
    async def test_toggle_ghost_from_person_to_ghost(self):
        mock_channel = MagicMock()
        mock_channel.name = "Test Channel 👤"
        mock_channel.edit = AsyncMock()
        self.mock_client.get_channel.return_value = mock_channel

        await self.channel_manager.toggle_ghost(123)
        mock_channel.edit.assert_called_once_with(name="Test Channel 👻")

    async def test_toggle_ghost_from_ghost_to_person(self):
        mock_channel = MagicMock()
        mock_channel.name = "Test Channel 👻"
        mock_channel.edit = AsyncMock()
        self.mock_client.get_channel.return_value = mock_channel

        await self.channel_manager.toggle_ghost(123)
        mock_channel.edit.assert_called_once_with(name="Test Channel 👤")

    async def test_toggle_ghost_no_emoji_found(self):
        mock_channel = MagicMock()
        mock_channel.name = "Test Channel"
        mock_channel.edit = AsyncMock()
        self.mock_client.get_channel.return_value = mock_channel

        await self.channel_manager.toggle_ghost(123)
        mock_channel.edit.assert_not_called()

    async def test_toggle_ghost_channel_not_found(self):
        self.mock_client.get_channel.return_value = None

        with self.assertLogs(level='INFO') as log:
            await self.channel_manager.toggle_ghost(123)
            self.assertIn("Channel with ID 123 not found.", log.output[0])

    # ==================================
    # Tests for move_channel_to_category
    # ==================================

    async def test_move_channel_to_category_success(self):
        self.mock_client.get_channel.side_effect = lambda x: self.mock_channel if x == 123 else self.mock_category
        result = await self.channel_manager.move_channel_to_category(123, 456)
        self.assertTrue(result)
        self.mock_channel.edit.assert_called_once_with(category=self.mock_category)

    async def test_move_channel_to_category_channel_not_found(self):
        self.mock_client.get_channel.side_effect = lambda x: None if x == 123 else self.mock_category
        result = await self.channel_manager.move_channel_to_category(123, 456)
        self.assertFalse(result)

    async def test_move_channel_to_category_category_not_found(self):
        self.mock_client.get_channel.side_effect = lambda x: self.mock_channel if x == 123 else None
        result = await self.channel_manager.move_channel_to_category(123, 456)
        self.assertFalse(result)

    async def test_move_channel_to_category_channel_not_text_channel(self):
        non_text_channel = MagicMock(spec=discord.VoiceChannel)  # Mock object not of type discord.TextChannel
        self.mock_client.get_channel.side_effect = lambda x: non_text_channel if x == 123 else self.mock_category
        result = await self.channel_manager.move_channel_to_category(123, 456)
        self.assertFalse(result)

    async def test_move_channel_to_category_category_not_category_channel(self):
        non_category_channel = MagicMock(spec=discord.VoiceChannel)  # Mock object not of type discord.CategoryChannel
        self.mock_client.get_channel.side_effect = lambda x: self.mock_channel if x == 123 else non_category_channel
        result = await self.channel_manager.move_channel_to_category(123, 456)
        self.assertFalse(result)

    async def test_move_channel_to_category_http_exception(self):
        self.mock_client.get_channel.side_effect = lambda x: self.mock_channel if x == 123 else self.mock_category
        self.mock_channel.edit.side_effect = discord.HTTPException(MagicMock(), MagicMock())
        with self.assertLogs(level='INFO') as log:
            result = await self.channel_manager.move_channel_to_category(123, 456)
            self.assertFalse(result)
            self.assertIn("An error occurred while moving channel", log.output[0])


if __name__ == '__main__':
    unittest.main()
