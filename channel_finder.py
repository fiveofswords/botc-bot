from __future__ import annotations

import discord

from model.settings import GameSettings

intents = discord.Intents.all()
intents.members = True
intents.presences = True
client = discord.Client(intents=intents)


@client.event
async def on_ready():
    print(f'Logged in as {client.user}')
    guild_id = 421432788894482434  # Replace with your guild's ID
    guild = client.get_guild(guild_id)
    if not guild:
        print("Guild not found.")
        return

    game_settings = GameSettings.load()

    for member in guild.members:
        channels_with_permissions = []
        for channel in guild.channels:
            # Check if the channel has specific permissions set for this member
            if channel.name.endswith("teensy"):
                if member.id in [overwrite.id for overwrite, _ in channel.overwrites.items() if
                                 isinstance(overwrite, discord.Member)]:
                    # channels_with_permissions.append(f'{channel.name}(ID: {channel.id})')
                    channels_with_permissions.append(channel)
                    # Print the member and their channels with explicit permissions
        if channels_with_permissions:  # Only print if the member has permissions in any channel
            print(f'Member: {member}({member.id}) has permissions in: {", ".join([f"{channel.name}(ID: {channel.id})" for channel in channels_with_permissions])}')
            game_settings.set_st_channel(member.id, channels_with_permissions[0].id)

    game_settings.save()
    # await client.close()


# Replace "YOUR_BOT_TOKEN_HERE" with your actual bot token
client.run("YOUR_BOT_TOKEN_HERE")
