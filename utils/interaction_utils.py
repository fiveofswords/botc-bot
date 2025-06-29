"""
Utility functions for user interactions.
"""

import asyncio

import discord

import bot_client
from utils import message_utils


async def yes_no(user: discord.User, text: str):
    """
    Ask a yes or no question of a user.
    
    Args:
        user: The Discord user to ask
        text: The question text
        
    Returns:
        True for yes, False for no, None for timeout/cancel
    """
    reply = await message_utils.safe_send(user, "{}? yes or no".format(text))
    try:
        choice = await bot_client.client.wait_for(
            "message",
            check=(lambda x: x.author == user and x.channel == reply.channel),
            timeout=200,
        )
    except asyncio.TimeoutError:
        await message_utils.safe_send(user, "Timed out.")
        return None

    # Cancel
    if choice.content.lower() == "cancel":
        await message_utils.safe_send(user, "Action cancelled!")
        return None

    # Yes
    if choice.content.lower() == "yes" or choice.content.lower() == "y":
        return True

    # No
    elif choice.content.lower() == "no" or choice.content.lower() == "n":
        return False

    else:
        await message_utils.safe_send(
            user, "Your answer must be 'yes,' 'y,' 'no,' or 'n' exactly. Try again."
        )
        return None
