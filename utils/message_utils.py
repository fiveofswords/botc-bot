"""
Utility functions for handling Discord messages.
"""

from typing import Optional, List, Union

import discord

import bot_client


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
        bot_client.logger.error(f"Failed to send message: {e}")
        return None
    except Exception as e:
        bot_client.logger.error(f"Unexpected error sending message: {e}")
        return None


async def safe_send_dm(
    user: Union[discord.Member, discord.User], 
    content: Optional[str] = None, 
    **kwargs
) -> Optional[discord.Message]:
    """
    Safely send a DM to a user, handling errors.
    
    Args:
        user: The user to send to
        content: The content of the message
        **kwargs: Additional message parameters
        
    Returns:
        The sent message or None if failed
    """
    try:
        # Create DM channel if needed
        dm_channel = user.dm_channel
        if dm_channel is None:
            dm_channel = await user.create_dm()
        
        # Send the message
        return await safe_send(dm_channel, content, **kwargs)
    except discord.HTTPException as e:
        bot_client.logger.error(f"Failed to send DM to {user.display_name}: {e}")
        return None
    except Exception as e:
        bot_client.logger.error(f"Unexpected error sending DM to {user.display_name}: {e}")
        return None


async def notify_storytellers(message: str, **kwargs) -> None:
    """
    Send a message to all storytellers in the current game.
    
    This utility function handles the common pattern of notifying all storytellers
    about game state changes. It will try both global_vars.gamemaster_role.members
    and global_vars.game.storytellers to find storytellers.
    
    Args:
        message: The message to send to storytellers
        **kwargs: Additional message parameters for safe_send
    """
    import global_vars

    # Try to send to storytellers from the game object first (preferred)
    if (hasattr(global_vars, 'game') and
            global_vars.game and
            hasattr(global_vars.game, 'storytellers') and
            global_vars.game.storytellers):
        for storyteller in global_vars.game.storytellers:
            # Game storytellers have a .user attribute
            user = getattr(storyteller, 'user', storyteller)
            await safe_send(user, message, **kwargs)

    # Fallback to gamemaster role members
    elif (hasattr(global_vars, 'gamemaster_role') and
          global_vars.gamemaster_role and
          hasattr(global_vars.gamemaster_role, 'members')):
        for member in global_vars.gamemaster_role.members:
            await safe_send(member, message, **kwargs)

    # If neither is available, log a warning
    else:
        bot_client.logger.warning(f"Could not notify storytellers: {message}")


async def notify_storytellers_about_action(author: Union[discord.Member, discord.User], action_description: str,
                                           **kwargs) -> None:
    """
    Send a notification to all storytellers about an action taken by someone.
    
    This is a convenience wrapper around notify_storytellers for the common pattern
    of notifying storytellers that someone performed an action.
    
    Args:
        author: The Discord user/member who performed the action
        action_description: Description of what happened (e.g., "whisper mode set to neighbors")
        **kwargs: Additional message parameters for safe_send
    
    Example (sends "<author> set whisper mode to neighbors" to storytellers):
        await notify_storytellers_about_action(
            message.author,
            "set whisper mode to neighbors"
        )
    """
    notification_message = f"{author.display_name} {action_description}"
    await notify_storytellers(notification_message, **kwargs)
