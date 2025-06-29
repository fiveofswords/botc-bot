"""
Tests for message utility functions used in the BOTC bot
"""

from unittest.mock import AsyncMock, patch, Mock

import discord
import pytest

from utils import message_utils
from utils.message_utils import safe_send_dm, _split_text


class TestSplitText:
    """Test the split_text function."""

    def test_text_under_max_length(self):
        """Test text under max length returns single item list."""
        text = "Short text"
        result = _split_text(text, max_length=20)
        assert len(result) == 1
        assert result[0] == text

    def test_text_exactly_max_length(self):
        """Test text exactly max length returns single item list."""
        text = "1234567890"
        result = _split_text(text, max_length=10)
        assert len(result) == 1
        assert result[0] == text

    def test_text_over_max_length(self):
        """Test text over max length is split correctly."""
        text = "1234567890ABCDEFGHIJ"
        result = _split_text(text, max_length=10)
        assert len(result) == 2
        assert result[0] == "1234567890"
        assert result[1] == "ABCDEFGHIJ"

    def test_multiple_chunks(self):
        """Test text is split into multiple chunks."""
        text = "123456789012345678901234567890"
        result = _split_text(text, max_length=10)
        assert len(result) == 3
        assert result[0] == "1234567890"
        assert result[1] == "1234567890"
        assert result[2] == "1234567890"


class TestSafeSend:
    """Test the safe_send function."""

    @pytest.fixture(autouse=True)
    def setup_test(self):
        self.channel = AsyncMock(spec=discord.TextChannel)

    @patch('bot_client.logger')
    @pytest.mark.asyncio
    async def test_send_normal_message(self, mock_logger):
        """Test sending a normal message."""
        self.channel.send.return_value = AsyncMock(spec=discord.Message)

        result = await message_utils.safe_send(self.channel, "Test message")

        self.channel.send.assert_called_once_with("Test message")
        assert result is not None
        mock_logger.error.assert_not_called()

    @patch('bot_client.logger')
    @pytest.mark.asyncio
    async def test_send_empty_message(self, mock_logger):
        """Test sending an empty message adds zero-width space."""
        self.channel.send.return_value = AsyncMock(spec=discord.Message)

        result = await message_utils.safe_send(self.channel)

        self.channel.send.assert_called_once_with("\u200b")
        assert result is not None
        mock_logger.error.assert_not_called()

    @patch('bot_client.logger')
    @patch('utils.message_utils._split_text')
    @pytest.mark.asyncio
    async def test_send_long_message(self, mock_split_text, mock_logger):
        """Test sending a message over 2000 characters."""
        long_message = "x" * 3000
        chunks = ["chunk1", "chunk2"]
        mock_split_text.return_value = chunks

        first_message = AsyncMock(spec=discord.Message)
        self.channel.send.side_effect = [first_message, AsyncMock()]

        result = await message_utils.safe_send(self.channel, long_message)

        mock_split_text.assert_called_once_with(long_message)
        assert self.channel.send.call_count == 2
        assert result == first_message
        mock_logger.error.assert_not_called()

    @patch('bot_client.logger')
    @pytest.mark.asyncio
    async def test_handle_http_exception(self, mock_logger):
        """Test handling HTTP exceptions."""
        self.channel.send.side_effect = discord.HTTPException(response=Mock(), message="Error")

        result = await message_utils.safe_send(self.channel, "Test message")

        assert result is None
        mock_logger.error.assert_called_once()

    @patch('bot_client.logger')
    @pytest.mark.asyncio
    async def test_handle_generic_exception(self, mock_logger):
        """Test handling generic exceptions."""
        self.channel.send.side_effect = Exception("General error")

        result = await message_utils.safe_send(self.channel, "Test message")

        assert result is None
        mock_logger.error.assert_called_once()


class TestSafeSendDM:
    """Test the safe_send_dm function."""

    @pytest.fixture(autouse=True)
    def setup_test(self):
        self.user = AsyncMock(spec=discord.User)
        self.dm_channel = AsyncMock(spec=discord.DMChannel)

    @patch('utils.message_utils.safe_send')
    @pytest.mark.asyncio
    async def test_dm_channel_exists(self, mock_safe_send):
        """Test sending DM when channel already exists."""
        self.user.dm_channel = self.dm_channel
        mock_safe_send.return_value = AsyncMock(spec=discord.Message)

        result = await safe_send_dm(self.user, "Test DM")

        self.user.create_dm.assert_not_called()
        mock_safe_send.assert_called_once_with(self.dm_channel, "Test DM")
        assert result is not None

    @patch('utils.message_utils.safe_send')
    @pytest.mark.asyncio
    async def test_create_dm_channel(self, mock_safe_send):
        """Test creating DM channel when it doesn't exist."""
        self.user.dm_channel = None
        self.user.create_dm.return_value = self.dm_channel
        mock_safe_send.return_value = AsyncMock(spec=discord.Message)

        result = await safe_send_dm(self.user, "Test DM")

        self.user.create_dm.assert_called_once()
        mock_safe_send.assert_called_once_with(self.dm_channel, "Test DM")
        assert result is not None

    @patch('bot_client.logger')
    @pytest.mark.asyncio
    async def test_handle_http_exception(self, mock_logger):
        """Test handling HTTP exceptions."""
        self.user.dm_channel = self.dm_channel
        self.user.display_name = "TestUser"
        self.dm_channel.send.side_effect = discord.HTTPException(response=Mock(), message="Error")

        result = await safe_send_dm(self.user, "Test DM")

        assert result is None
        mock_logger.error.assert_called_once()

    @patch('bot_client.logger')
    @pytest.mark.asyncio
    async def test_handle_generic_exception(self, mock_logger):
        """Test handling generic exceptions."""
        self.user.dm_channel = None
        self.user.display_name = "TestUser"
        self.user.create_dm.side_effect = Exception("General error")

        result = await safe_send_dm(self.user, "Test DM")

        assert result is None
        mock_logger.error.assert_called_once_with("Unexpected error sending DM to TestUser: General error")
