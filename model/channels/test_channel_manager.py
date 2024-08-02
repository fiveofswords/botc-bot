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
        self.mock_category = MagicMock(spec=discord.CategoryChannel)
        self.mock_server = MagicMock(spec=discord.Guild)
        self.mock_everyone_role = MagicMock(spec=discord.CategoryChannel, name="@everyone")
        self.in_play_category = MagicMock(spec=discord.CategoryChannel, name="In Play")
        self.out_of_play_category = MagicMock(spec=discord.CategoryChannel, name="Out of Play")
        self.channel_manager._in_play_category = self.in_play_category
        self.channel_manager._out_of_play_category = self.out_of_play_category

        self.hands_channel = MagicMock(spec=discord.TextChannel, name="hands")
        self.observer_channel = MagicMock(spec=discord.TextChannel, name="observers")
        self.info_channel = MagicMock(spec=discord.TextChannel, name="info")
        self.whisper_channel = MagicMock(spec=discord.TextChannel, name="whisper")
        self.town_square_channel = MagicMock(spec=discord.TextChannel, name="town_square")
        self.channel_manager._hands_channel = self.hands_channel
        self.channel_manager._observer_channel = self.observer_channel
        self.channel_manager._info_channel = self.info_channel
        self.channel_manager._whisper_channel = self.whisper_channel
        self.channel_manager._town_square_channel = self.town_square_channel

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

    async def test_create_channel(self):
        self.channel_manager._out_of_play_category = self.mock_category
        self.channel_manager._server = self.mock_server
        self.mock_server.default_role = self.mock_everyone_role
        mock_channel = MagicMock(spec=discord.TextChannel)
        self.mock_category.create_text_channel.return_value = mock_channel
        self.channel_manager._st_role = MagicMock(spec=discord.Role)
        self.mock_member.display_name = "another test-member (pronouns)"
        self.channel_manager._channel_suffix = "test_suffix"

        # Setup expected permissions
        expected_overwrites = {
            self.mock_everyone_role: discord.PermissionOverwrite(read_messages=False, send_messages=False),
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
        self.assertEqual('👤another_test_member-x-test_suffix', kwargs['name'])
        for key, value in expected_overwrites.items():
            self.assertTrue(key in kwargs['overwrites'])
            self.assertEqual(kwargs['overwrites'][key].read_messages, value.read_messages)
            self.assertEqual(kwargs['overwrites'][key].send_messages, value.send_messages)
        self.assertIsInstance(result, discord.TextChannel)
        self.assertEqual(result, mock_channel)

    async def test_setup_channels_in_order_success(self):
        # Mock channels
        in_play_st_channels = [MagicMock(spec=discord.TextChannel, name=f'in_play_{i}') for i in range(5)]
        extra_channels = [MagicMock(spec=discord.TextChannel, name=f'out_of_play_{i}') for i in range(2)]

        self.in_play_category.channels = in_play_st_channels + extra_channels

        # Execute
        result = await self.channel_manager.setup_channels_in_order(in_play_st_channels)

        # Verify
        expected_in_play_channels = [self.hands_channel, self.observer_channel, self.info_channel,
                                     self.whisper_channel] + in_play_st_channels + [self.town_square_channel]
        for channel in extra_channels:
            channel.move.assert_called_once_with(category=self.out_of_play_category, end=True)
        for index, channel in enumerate(expected_in_play_channels):
            channel.edit.assert_called_once_with(category=self.in_play_category, position=index)

    async def test_setup_channels_in_order_skips_in_place_channels(self):
        # Setup:
        # Put the hands channel in the correct position already
        self.hands_channel.category = self.in_play_category
        self.hands_channel.position = 0
        # Create mock channels already in their correct positions
        in_play_st_channels = [
            MagicMock(spec=discord.TextChannel, name=f'in_play_{i}', category=self.in_play_category, position=i + 4)
            for i in range(5)
        ]

        # Execute: Attempt to reorder channels, expecting no changes for already correctly placed channels
        await self.channel_manager.setup_channels_in_order(in_play_st_channels)

        # Verify: Assert that edit is not called on channels already in the correct position
        self.hands_channel.edit.assert_not_called()
        for channel in in_play_st_channels:
            channel.edit.assert_not_called()

        # Verify: Assert that edit is called on channels not in the list to ensure they are moved correctly
        self.observer_channel.edit.assert_called_once_with(category=self.in_play_category, position=1)
        self.info_channel.edit.assert_called_once_with(category=self.in_play_category, position=2)
        self.whisper_channel.edit.assert_called_once_with(category=self.in_play_category, position=3)
        self.town_square_channel.edit.assert_called_once_with(category=self.in_play_category,
                                                              position=len(in_play_st_channels) + 4)


if __name__ == '__main__':
    unittest.main()
