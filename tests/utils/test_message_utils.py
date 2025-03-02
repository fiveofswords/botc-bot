"""
Tests for message utility functions used in the BOTC bot
"""

from unittest.mock import AsyncMock, MagicMock, patch, Mock

import discord
import pytest

# Import safe_send from both sources to test the functionality is consistent
from bot_impl import safe_send as bot_safe_send
from utils.message_utils import safe_send, safe_send_dm, _split_text
from utils.message_utils import safe_send as utils_safe_send


@pytest.fixture
def mock_target():
    """Create a mock target for sending messages."""
    target = MagicMock()
    target.send = AsyncMock(return_value=MagicMock())
    return target


@pytest.mark.asyncio
async def test_safe_send_normal(mock_target):
    """Test safe_send with normal message lengths."""
    # Test with a normal message
    message = "This is a test message that is well under the character limit."

    # Test both implementations with the same inputs
    bot_result = await bot_safe_send(mock_target, message)

    # Reset mock calls
    mock_target.send.reset_mock()

    # Now test the utils version
    utils_result = await utils_safe_send(mock_target, message)

    # Verify send was called once with the message
    mock_target.send.assert_called_once_with(message)

    # Both implementations should return the same type of result
    assert type(bot_result) == type(utils_result)


@pytest.mark.asyncio
async def test_safe_send_empty(mock_target):
    """Test safe_send with an empty message."""
    # Test with an empty message
    message = ""

    # Test the implementation
    result = await bot_safe_send(mock_target, message)

    # Verify send was called once with the empty message
    mock_target.send.assert_called_once_with(message)

    # Verify the result is what was returned by send
    assert result == mock_target.send.return_value


@pytest.mark.asyncio
async def test_safe_send_split():
    """Test safe_send with a message that needs to be split."""
    # Create a mock target
    mock_target = MagicMock()

    # Create mock return values for the first and second sends
    first_result = MagicMock()
    second_result = MagicMock()

    # Configure mock to raise exception on first call, then return values on subsequent calls
    mock_exception = discord.HTTPException(MagicMock(), {"code": 50035})
    mock_exception.code = 50035  # Ensure code attribute is set properly

    mock_target.send = AsyncMock(side_effect=[mock_exception, first_result, second_result])

    # Create a message
    message = "A message that will be split"

    # Mock the recursive calls to safe_send
    with patch('bot_impl.safe_send', side_effect=[first_result, second_result]) as mock_safe_send:
        # Call safe_send
        result = await bot_safe_send(mock_target, message)

        # Verify send was called with the original message
        mock_target.send.assert_called_once_with(message)

        # Verify result is the first successful send
        assert result == first_result


@pytest.mark.asyncio
async def test_safe_send_other_exception():
    """Test safe_send with a different HTTP exception."""
    # Create a mock target
    mock_target = MagicMock()

    # Create exception with a different code
    mock_exception = discord.HTTPException(MagicMock(), {"code": 40001})
    mock_exception.code = 40001  # Ensure code attribute is set properly

    # Configure mock to raise the exception
    mock_target.send = AsyncMock(side_effect=mock_exception)

    # Test with a normal message
    message = "Test message"

    # Should raise the exception
    with pytest.raises(discord.HTTPException) as exc_info:
        await bot_safe_send(mock_target, message)

    # Verify the exception has the expected code
    assert exc_info.value.code == 40001

    # Verify send was called once with the message
    mock_target.send.assert_called_once_with(message)


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

    @patch('utils.message_utils.logger')
    @pytest.mark.asyncio
    async def test_send_normal_message(self, mock_logger):
        """Test sending a normal message."""
        self.channel.send.return_value = AsyncMock(spec=discord.Message)

        result = await safe_send(self.channel, "Test message")

        self.channel.send.assert_called_once_with("Test message")
        assert result is not None
        mock_logger.error.assert_not_called()

    @patch('utils.message_utils.logger')
    @pytest.mark.asyncio
    async def test_send_empty_message(self, mock_logger):
        """Test sending an empty message adds zero-width space."""
        self.channel.send.return_value = AsyncMock(spec=discord.Message)

        result = await safe_send(self.channel)

        self.channel.send.assert_called_once_with("\u200b")
        assert result is not None
        mock_logger.error.assert_not_called()

    @patch('utils.message_utils.logger')
    @patch('utils.message_utils._split_text')
    @pytest.mark.asyncio
    async def test_send_long_message(self, mock_split_text, mock_logger):
        """Test sending a message over 2000 characters."""
        long_message = "x" * 3000
        chunks = ["chunk1", "chunk2"]
        mock_split_text.return_value = chunks

        first_message = AsyncMock(spec=discord.Message)
        self.channel.send.side_effect = [first_message, AsyncMock()]

        result = await safe_send(self.channel, long_message)

        mock_split_text.assert_called_once_with(long_message)
        assert self.channel.send.call_count == 2
        assert result == first_message
        mock_logger.error.assert_not_called()

    @patch('utils.message_utils.logger')
    @pytest.mark.asyncio
    async def test_handle_http_exception(self, mock_logger):
        """Test handling HTTP exceptions."""
        self.channel.send.side_effect = discord.HTTPException(response=Mock(), message="Error")

        result = await safe_send(self.channel, "Test message")

        assert result is None
        mock_logger.error.assert_called_once()

    @patch('utils.message_utils.logger')
    @pytest.mark.asyncio
    async def test_handle_generic_exception(self, mock_logger):
        """Test handling generic exceptions."""
        self.channel.send.side_effect = Exception("General error")

        result = await safe_send(self.channel, "Test message")

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

    @patch('utils.message_utils.logger')
    @pytest.mark.asyncio
    async def test_handle_http_exception(self, mock_logger):
        """Test handling HTTP exceptions."""
        self.user.dm_channel = self.dm_channel
        self.user.display_name = "TestUser"
        self.dm_channel.send.side_effect = discord.HTTPException(response=Mock(), message="Error")

        result = await safe_send_dm(self.user, "Test DM")

        assert result is None
        mock_logger.error.assert_called_once()

    @patch('utils.message_utils.logger')
    @pytest.mark.asyncio
    async def test_handle_generic_exception(self, mock_logger):
        """Test handling generic exceptions."""
        self.user.dm_channel = None
        self.user.display_name = "TestUser"
        self.user.create_dm.side_effect = Exception("General error")

        result = await safe_send_dm(self.user, "Test DM")

        assert result is None
        mock_logger.error.assert_called_once_with("Unexpected error sending DM to TestUser: General error")
