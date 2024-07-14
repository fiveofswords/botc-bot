import discord

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

    for member in guild.members:
        channels_with_permissions = []
        for channel in guild.channels:
            # Check if the channel has specific permissions set for this member
            if member.id in [overwrite.id for overwrite, _ in channel.overwrites.items() if
                             isinstance(overwrite, discord.Member)]:
                channels_with_permissions.append(f'{channel.name}(ID: {channel.id})')

        # Print the member and their channels with explicit permissions
        if channels_with_permissions:  # Only print if the member has permissions in any channel
            print(f'Member: {member}({member.id}) has permissions in: {", ".join(channels_with_permissions)}')


# Replace "YOUR_BOT_TOKEN_HERE" with your actual bot token
client.run("YOUR_BOT_TOKEN_HERE")
