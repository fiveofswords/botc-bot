"""Utilities for game management, extracted to avoid circular imports."""

import os

import discord

import global_vars


async def update_presence(client):
    """Updates Discord Presence based on the current game state.
    
    Args:
        client: The Discord client
    """
    from model.game.whisper_mode import WhisperMode

    if global_vars.game is None or not hasattr(global_vars, 'game') or global_vars.game.seatingOrder == []:
        await client.change_presence(
            status=discord.Status.dnd, activity=discord.Game(name="No ongoing game!")
        )
    elif not global_vars.game.isDay:
        await client.change_presence(
            status=discord.Status.idle, activity=discord.Game(name="It's nighttime!")
        )
    else:
        clopen = ["Closed", "Open"]

        whisper_state = "to " + global_vars.game.whisper_mode if global_vars.game.days[
                                                                     -1].isPms and global_vars.game.whisper_mode != WhisperMode.ALL else \
            clopen[
                global_vars.game.days[-1].isPms]
        status = "PMs {}, Nominations {}!".format(whisper_state, clopen[global_vars.game.days[-1].isNoms])
        await client.change_presence(
            status=discord.Status.online,
            activity=discord.Game(
                name=status
            ),
        )


def remove_backup(fileName):
    """Removes a backup file and its associated object files.
    
    Args:
        fileName: The name of the backup file
    """
    if os.path.exists(fileName):
        os.remove(fileName)

    for obj in [
        x
        for x in dir(global_vars.game)
        if not x.startswith("__") and not callable(getattr(global_vars.game, x))
    ]:
        obj_file = obj + "_" + fileName
        if os.path.exists(obj_file):
            os.remove(obj_file)
