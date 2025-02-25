"""
Unit tests for message utility functions.
"""

from unittest import TestCase, IsolatedAsyncioTestCase, mock
import discord

from utils.message_utils import _split_text, safe_send


class TestSplitText(TestCase):
    """Test the split_text function."""

    def test_text_under_max_length(self):
        """Test text under max length returns single item list."""
        text = "Short text"
        result = _split_text(text, max_length=20)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], text)

    def test_text_exactly_max_length(self):
        """Test text exactly max length returns single item list."""
        text = "1234567890"
        result = _split_text(text, max_length=10)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], text)

    def test_text_over_max_length(self):
        """Test text over max length is split correctly."""
        text = "1234567890ABCDEFGHIJ"
        result = _split_text(text, max_length=10)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], "1234567890")
        self.assertEqual(result[1], "ABCDEFGHIJ")

    def test_multiple_chunks(self):
        """Test text is split into multiple chunks."""
        text = "123456789012345678901234567890"
        result = _split_text(text, max_length=10)
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0], "1234567890")
        self.assertEqual(result[1], "1234567890")
        self.assertEqual(result[2], "1234567890")


class TestSafeSend(IsolatedAsyncioTestCase):
    """Test the safe_send function."""

    async def asyncSetUp(self):
        self.channel = mock.AsyncMock(spec=discord.TextChannel)

    @mock.patch('utils.message_utils.logger')
    async def test_send_normal_message(self, mock_logger):
        """Test sending a normal message."""
        self.channel.send.return_value = mock.AsyncMock(spec=discord.Message)
        
        result = await safe_send(self.channel, "Test message")
        
        self.channel.send.assert_called_once_with("Test message")
        self.assertIsNotNone(result)
        mock_logger.error.assert_not_called()

    @mock.patch('utils.message_utils.logger')
    async def test_send_empty_message(self, mock_logger):
        """Test sending an empty message adds zero-width space."""
        self.channel.send.return_value = mock.AsyncMock(spec=discord.Message)
        
        result = await safe_send(self.channel)
        
        self.channel.send.assert_called_once_with("\u200b")
        self.assertIsNotNone(result)
        mock_logger.error.assert_not_called()

    @mock.patch('utils.message_utils.logger')
    @mock.patch('utils.message_utils._split_text')
    async def test_send_long_message(self, mock_split_text, mock_logger):
        """Test sending a message over 2000 characters."""
        long_message = "x" * 3000
        chunks = ["chunk1", "chunk2"]
        mock_split_text.return_value = chunks
        
        first_message = mock.AsyncMock(spec=discord.Message)
        self.channel.send.side_effect = [first_message, mock.AsyncMock()]
        
        result = await safe_send(self.channel, long_message)
        
        mock_split_text.assert_called_once_with(long_message)
        self.assertEqual(self.channel.send.call_count, 2)
        self.assertEqual(result, first_message)
        mock_logger.error.assert_not_called()

    @mock.patch('utils.message_utils.logger')
    async def test_handle_http_exception(self, mock_logger):
        """Test handling HTTP exceptions."""
        self.channel.send.side_effect = discord.HTTPException(response=mock.Mock(), message="Error")
        
        result = await safe_send(self.channel, "Test message")
        
        self.assertIsNone(result)
        mock_logger.error.assert_called_once()

    @mock.patch('utils.message_utils.logger')
    async def test_handle_generic_exception(self, mock_logger):
        """Test handling generic exceptions."""
        self.channel.send.side_effect = Exception("General error")
        
        result = await safe_send(self.channel, "Test message")
        
        self.assertIsNone(result)
        mock_logger.error.assert_called_once()


if __name__ == '__main__':
    import unittest
    unittest.main()