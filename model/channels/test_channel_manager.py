import unittest
from unittest.mock import MagicMock, AsyncMock

import discord

from model.channels.channel_manager import ChannelManager
from model.settings import GameSettings


class TestChannelManager(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.mock_client = MagicMock(spec=discord.Client)
        self.channel_manager = ChannelManager(self.mock_client)
        self.mock_member = MagicMock(spec=discord.Member)
        self.mock_settings = MagicMock(spec=GameSettings)
        self.mock_channel = MagicMock(spec=discord.TextChannel)
        self.mock_category = MagicMock(spec=discord.CategoryChannel)
        self.mock_server = MagicMock(spec=discord.Guild)
        self.mock_everyone_category = MagicMock(spec=discord.CategoryChannel)

    # ==============================
    # Tests for updating ghost state
    # ==============================

    # Tests for set_ghost
    async def test_set_ghost_with_person(self):
        mock_channel = MagicMock()
        mock_channel.name = "Test Channel 👤"
        mock_channel.edit = AsyncMock()
        self.mock_client.get_channel.return_value = mock_channel

        await self.channel_manager.set_ghost(123)
        mock_channel.edit.assert_called_once_with(name="Test Channel 👻")

    async def test_set_ghost_with_ghost(self):
        mock_channel = MagicMock()
        mock_channel.name = "Test Channel 👻"
        mock_channel.edit = AsyncMock()
        self.mock_client.get_channel.return_value = mock_channel

        await self.channel_manager.set_ghost(123)
        mock_channel.edit.assert_not_called()

    async def test_set_ghost_no_emoji_found(self):
        mock_channel = MagicMock()
        mock_channel.name = "Test Channel"
        mock_channel.edit = AsyncMock()
        self.mock_client.get_channel.return_value = mock_channel

        with self.assertLogs(level='INFO', logger='discord') as log:
            await self.channel_manager.set_ghost(123)
            self.assertIn("No emoji found", log.output[0])
        mock_channel.edit.assert_not_called()

    async def test_set_ghost_channel_not_found(self):
        self.mock_client.get_channel.return_value = None

        with self.assertLogs(level='INFO', logger='discord') as log:
            await self.channel_manager.set_ghost(123)
            self.assertIn("Channel with ID 123 not found.", log.output[0])

    # Tests for remove_ghost
    async def test_remove_ghost_with_person(self):
        mock_channel = MagicMock()
        mock_channel.name = "Test Channel 👤"
        mock_channel.edit = AsyncMock()
        self.mock_client.get_channel.return_value = mock_channel

        await self.channel_manager.remove_ghost(123)
        mock_channel.edit.assert_not_called()

    async def test_remove_ghost_with_ghost(self):
        mock_channel = MagicMock()
        mock_channel.name = "Test Channel 👻"
        mock_channel.edit = AsyncMock()
        self.mock_client.get_channel.return_value = mock_channel

        await self.channel_manager.remove_ghost(123)
        mock_channel.edit.assert_called_once_with(name="Test Channel 👤")

    async def test_remove_ghost_no_emoji_found(self):
        mock_channel = MagicMock()
        mock_channel.name = "Test Channel"
        mock_channel.edit = AsyncMock()
        self.mock_client.get_channel.return_value = mock_channel

        with self.assertLogs(level='INFO', logger='discord') as log:
            await self.channel_manager.remove_ghost(123)
            self.assertIn("No emoji found", log.output[0])
        mock_channel.edit.assert_not_called()

    async def test_remove_ghost_channel_not_found(self):
        self.mock_client.get_channel.return_value = None

        with self.assertLogs(level='INFO', logger='discord') as log:
            await self.channel_manager.remove_ghost(123)
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

    async def test_create_channel(self):
        self.channel_manager._out_of_play_category = self.mock_category
        self.channel_manager._server = self.mock_server
        self.mock_server.default_role = self.mock_everyone_category
        self.mock_category.create_text_channel.return_value = self.mock_channel
        self.channel_manager._st_role = MagicMock(spec=discord.Role)

        # Setup expected permissions
        expected_overwrites = {
            self.mock_everyone_category: discord.PermissionOverwrite(read_messages=False, send_messages=False),
            self.channel_manager._client.user: discord.PermissionOverwrite(read_messages=True,
                                                                           send_messages=True),
            self.channel_manager._st_role: discord.PermissionOverwrite(read_messages=True,
                                                                       send_messages=True),
            self.mock_member: discord.PermissionOverwrite(read_messages=True,
                                                          send_messages=True),
        }

        # Execute the method
        result = await self.channel_manager.create_channel(self.mock_settings, self.mock_member)

        # Assertions
        self.mock_category.create_text_channel.assert_called_once()
        _, kwargs = self.mock_category.create_text_channel.call_args
        self.assertTrue('overwrites' in kwargs)
        for key, value in expected_overwrites.items():
            self.assertTrue(key in kwargs['overwrites'])
            self.assertEqual(kwargs['overwrites'][key].read_messages, value.read_messages)
            self.assertEqual(kwargs['overwrites'][key].send_messages, value.send_messages)
        self.assertIsInstance(result, discord.TextChannel)
        self.assertEqual(result, self.mock_channel)


if __name__ == '__main__':
    unittest.main()
