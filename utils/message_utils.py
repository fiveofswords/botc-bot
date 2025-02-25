"""
Utility functions for handling Discord messages.
"""

from typing import Optional, List, Union

import discord

from bot_client import logger


def _split_text(text: str, max_length: int = 2000) -> List[str]:
    """
    Split text into chunks of maximum length.
    
    Args:
        text: The text to split
        max_length: Maximum length of each chunk
        
    Returns:
        List of text chunks
    """
    return [text[i:i+max_length] for i in range(0, len(text), max_length)]


async def safe_send(
    channel: Union[discord.abc.Messageable, discord.Member, discord.User], 
    content: Optional[str] = None, 
    **kwargs
) -> Optional[discord.Message]:
    """
    Safely send a message to a channel, handling errors and long messages.
    
    Args:
        channel: The channel or user to send to
        content: The content of the message
        **kwargs: Additional message parameters
        
    Returns:
        The sent message or None if failed
    """
    try:
        # Handle empty content
        if not content and not any(k in kwargs for k in ['embed', 'embeds', 'file', 'files']):
            content = "\u200b"  # Zero-width space
        
        # Split long messages
        if content and len(content) > 2000:
            chunks = _split_text(content)
            first_message = None
            for i, chunk in enumerate(chunks):
                if i == 0:
                    # Apply kwargs only to the first message
                    message = await channel.send(chunk, **kwargs)
                    first_message = message
                else:
                    await channel.send(chunk)
            return first_message
        
        # Regular send
        return await channel.send(content, **kwargs)
    except discord.HTTPException as e:
        logger.error(f"Failed to send message: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error sending message: {e}")
        return None