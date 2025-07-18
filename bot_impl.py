from __future__ import annotations

import asyncio
import inspect
import itertools
import math
import os
from collections import OrderedDict

import discord

import bot_client
import commands.loader
import global_vars
import model.channels
import model.channels.channel_utils
import model.characters
import model.game.script
import model.game.vote
import model.game.whisper_mode
import model.player
import model.settings
import time_utils
from commands.registry import registry
from model.game import game
from utils import player_utils, message_utils, update_presence, text_utils, character_utils, game_utils

# Try to import config, create a mock config module if not available
try:
    import config
except ImportError:
    # Create a mock config module with default values for testing
    import types

    config = types.ModuleType('config')
    config.SERVER_ID = 1
    config.GAME_CATEGORY_ID = 2
    config.HANDS_CHANNEL_ID = 3
    config.OBSERVER_CHANNEL_ID = 4
    config.INFO_CHANNEL_ID = 5
    config.WHISPER_CHANNEL_ID = 6
    config.TOWN_SQUARE_CHANNEL_ID = 7
    config.OUT_OF_PLAY_CATEGORY_ID = 8
    config.PLAYER_ROLE = "player"
    config.TRAVELER_ROLE = "traveler"
    config.GHOST_ROLE = "ghost"
    config.DEAD_VOTE_ROLE = "deadVote"
    config.STORYTELLER_ROLE = "storyteller"
    config.INACTIVE_ROLE = "inactive"
    config.OBSERVER_ROLE = "observer"
    config.CHANNEL_SUFFIX = 'test'
    config.PREFIXES = (',', '@')



# Load all commands into the registry
commands.loader.load_all_commands()

### API Stuff
try:
    member_cache = discord.MemberCacheFlags(
        online=True,  # Whether to cache members with a status. Members that go offline are no longer cached.
        voice=True,  # Whether to cache members that are in voice. Members that leave voice are no longer cached.
        joined=True,  # Whether to cache members that joined the guild or are chunked as part of the initial log in flow. Members that leave the guild are no longer cached.
    )
except TypeError:
    # online is not a valid flag name
    member_cache = discord.MemberCacheFlags(
        voice=True,
        joined=True
    )

### Event Handling
@bot_client.client.event
async def on_ready():
    # On startup
    from model.game.game import NULL_GAME

    global_vars.game = NULL_GAME
    global_vars.observer_role = None

    global_vars.server = bot_client.client.get_guild(config.SERVER_ID)
    global_vars.game_category = bot_client.client.get_channel(config.GAME_CATEGORY_ID)
    global_vars.hands_channel = bot_client.client.get_channel(config.HANDS_CHANNEL_ID)
    global_vars.observer_channel = bot_client.client.get_channel(config.OBSERVER_CHANNEL_ID)
    global_vars.info_channel = bot_client.client.get_channel(config.INFO_CHANNEL_ID)
    global_vars.whisper_channel = bot_client.client.get_channel(config.WHISPER_CHANNEL_ID)
    global_vars.channel = bot_client.client.get_channel(config.TOWN_SQUARE_CHANNEL_ID)
    global_vars.out_of_play_category = bot_client.client.get_channel(config.OUT_OF_PLAY_CATEGORY_ID)
    global_vars.channel_suffix = config.CHANNEL_SUFFIX
    bot_client.logger.info(
        f"server: {global_vars.server.name}, "
        f"game_category: {global_vars.game_category.name if global_vars.game_category else None}, "
        f"hands_channel: {global_vars.hands_channel.name if global_vars.hands_channel else None}, "
        f"observer_channel: {global_vars.observer_channel.name if global_vars.observer_channel else None}, "
        f"info_channel: {global_vars.info_channel.name if global_vars.info_channel else None}, "
        f"whisper_channel: {global_vars.whisper_channel.name if global_vars.whisper_channel else None}, "
        f"townsquare_channel: {global_vars.channel.name}, "
        f"out_of_play_category: {global_vars.out_of_play_category.name if global_vars.out_of_play_category else None}, "
    )

    for role in global_vars.server.roles:
        if role.name == config.PLAYER_ROLE:
            global_vars.player_role = role
        elif role.name == config.TRAVELER_ROLE:
            global_vars.traveler_role = role
        elif role.name == config.GHOST_ROLE:
            global_vars.ghost_role = role
        elif role.name == config.DEAD_VOTE_ROLE:
            global_vars.dead_vote_role = role
        elif role.name == config.STORYTELLER_ROLE:
            global_vars.gamemaster_role = role
        elif role.name == config.INACTIVE_ROLE:
            global_vars.inactive_role = role
        elif role.name == config.OBSERVER_ROLE:
            global_vars.observer_role = role

    if os.path.isfile("current_game.pckl"):
        global_vars.game = await game_utils.load("current_game.pckl")
        print("Backup restored!")

    else:
        print("No backup found.")

    await update_presence(bot_client.client)

    # Log all registered commands
    registry.log_registered_commands(bot_client.logger)

    print("Logged in as")
    print(bot_client.client.user.name)
    print(bot_client.client.user.id)
    print("------")


@bot_client.client.event
async def on_message(message):
    # Handles messages

    game_utils.backup("current_game.pckl")

    # Don't respond to self
    if message.author == bot_client.client.user:
        return

    # Update activity from town square message
    if message.channel == global_vars.channel:
        if global_vars.game is not game.NULL_GAME:
            await player_utils.make_active(message.author)
            game_utils.backup("current_game.pckl")

        # Votes
        if message.content.startswith(config.PREFIXES):

            if " " in message.content:
                command = message.content[1: message.content.index(" ")].lower()
                argument = message.content[message.content.index(" ") + 1:].lower()
            else:
                command = message.content[1:].lower()
                argument = ""

            if command == "vote":

                if global_vars.game is game.NULL_GAME:
                    await message_utils.safe_send(global_vars.channel, "There's no game right now.")
                    return

                if global_vars.game.isDay == False:
                    await message_utils.safe_send(global_vars.channel, "It's not day right now.")
                    return

                if global_vars.game.days[-1].votes == [] or global_vars.game.days[-1].votes[-1].done == True:
                    await message_utils.safe_send(global_vars.channel, "There's no vote right now.")
                    return

                if (
                    argument != "yes"
                    and argument != "y"
                    and argument != "no"
                    and argument != "n"
                ):
                    await message_utils.safe_send(
                        global_vars.channel,
                        "{} is not a valid vote. Use 'yes', 'y', 'no', or 'n'.".format(
                            argument
                        )
                    )
                    return

                vote = global_vars.game.days[-1].votes[-1]

                voting_player = player_utils.get_player(message.author)
                if not voting_player:
                    await message_utils.safe_send(global_vars.channel, "You are not a player in the game.")
                    return
                if (
                    vote.order[vote.position].user
                    != voting_player.user
                ):
                    await message_utils.safe_send(global_vars.channel, "It's not your vote right now.")
                    return

                vt = int(argument == "yes" or argument == "y")
                voudon_in_play = model.game.vote.in_play_voudon()
                if vt > 0 and voudon_in_play and voting_player != voudon_in_play and not voting_player.is_ghost:
                    await message_utils.safe_send(global_vars.channel,
                                                  "Voudon is in play. Only the Voudon and dead may vote.")
                    return

                await vote.vote(vt, voter=voting_player)
                if global_vars.game is not game.NULL_GAME:
                    game_utils.backup("current_game.pckl")
                return

    # Update activity from a player's Storyteller channel
    if global_vars.game is not game.NULL_GAME:
        if message.channel.id == model.settings.GameSettings.load().get_st_channel(message.author.id):
            await player_utils.active_in_st_chat(message.author)
            game_utils.backup("current_game.pckl")
            return

    # Responding to dms
    if message.guild is None:

        # Check if command
        if message.content.startswith(config.PREFIXES):

            # Generate command and arguments
            if " " in message.content:
                command = message.content[1: message.content.index(" ")].lower()
                argument = message.content[message.content.index(" ") + 1:].lower()
            else:
                command = message.content[1:].lower()
                argument = ""

            alias = model.settings.GlobalSettings.load().get_alias(message.author.id, command)
            if alias:
                command = alias

            # Try to handle command using the registry
            if await registry.handle_command(command, message, argument):
                return

            # Legacy command handling - gradually move these to registry
            # Opens pms
            if command == "openpms":
                if global_vars.game is game.NULL_GAME:
                    await message_utils.safe_send(message.author, "There's no game right now.")
                    return

                if not global_vars.gamemaster_role in global_vars.server.get_member(message.author.id).roles:
                    await message_utils.safe_send(message.author, "You don't have permission to open PMs.")
                    return

                if global_vars.game.isDay == False:
                    await message_utils.safe_send(message.author, "It's not day right now.")
                    return

                await global_vars.game.days[-1].open_pms()
                if global_vars.game is not game.NULL_GAME:
                    game_utils.backup("current_game.pckl")

            # Opens nominations
            elif command == "opennoms":
                if global_vars.game is game.NULL_GAME:
                    await message_utils.safe_send(message.author, "There's no game right now.")
                    return

                if not global_vars.gamemaster_role in global_vars.server.get_member(message.author.id).roles:
                    await message_utils.safe_send(message.author, "You don't have permission to open nominations.")
                    return

                if global_vars.game.isDay == False:
                    await message_utils.safe_send(message.author, "It's not day right now.")
                    return

                await global_vars.game.days[-1].open_noms()
                if global_vars.game is not game.NULL_GAME:
                    game_utils.backup("current_game.pckl")

            # Opens pms and nominations
            elif command == "open":
                if global_vars.game is game.NULL_GAME:
                    await message_utils.safe_send(message.author, "There's no game right now.")
                    return

                if not global_vars.gamemaster_role in global_vars.server.get_member(message.author.id).roles:
                    await message_utils.safe_send(message.author,
                                                  "You don't have permission to open PMs and nominations.")
                    return

                if global_vars.game.isDay == False:
                    await message_utils.safe_send(message.author, "It's not day right now.")
                    return

                await global_vars.game.days[-1].open_pms()
                await global_vars.game.days[-1].open_noms()
                if global_vars.game is not game.NULL_GAME:
                    game_utils.backup("current_game.pckl")

            # Closes pms
            elif command == "closepms":
                if global_vars.game is game.NULL_GAME:
                    await message_utils.safe_send(message.author, "There's no game right now.")
                    return

                if not global_vars.gamemaster_role in global_vars.server.get_member(message.author.id).roles:
                    await message_utils.safe_send(message.author, "You don't have permission to close PMs.")
                    return

                if global_vars.game.isDay == False:
                    await message_utils.safe_send(message.author, "It's not day right now.")
                    return

                await global_vars.game.days[-1].close_pms()
                if global_vars.game is not game.NULL_GAME:
                    game_utils.backup("current_game.pckl")

            # Closes nominations
            elif command == "closenoms":
                if global_vars.game is game.NULL_GAME:
                    await message_utils.safe_send(message.author, "There's no game right now.")
                    return

                if not global_vars.gamemaster_role in global_vars.server.get_member(message.author.id).roles:
                    await message_utils.safe_send(message.author, "You don't have permission to close nominations.")
                    return

                if global_vars.game.isDay == False:
                    await message_utils.safe_send(message.author, "It's not day right now.")
                    return

                await global_vars.game.days[-1].close_noms()
                if global_vars.game is not game.NULL_GAME:
                    game_utils.backup("current_game.pckl")

            # Closes pms and nominations
            elif command == "close":
                if global_vars.game is game.NULL_GAME:
                    await message_utils.safe_send(message.author, "There's no game right now.")
                    return

                if not global_vars.gamemaster_role in global_vars.server.get_member(message.author.id).roles:
                    await message_utils.safe_send(message.author,
                                                  "You don't have permission to close PMs and nominations.")
                    return

                if global_vars.game.isDay == False:
                    await message_utils.safe_send(message.author, "It's not day right now.")
                    return

                await global_vars.game.days[-1].close_pms()
                await global_vars.game.days[-1].close_noms()
                if global_vars.game is not game.NULL_GAME:
                    game_utils.backup("current_game.pckl")
                return

            # Welcomes players
            elif command == "welcome":
                player = await player_utils.select_player(message.author, argument, global_vars.server.members)
                if player is None:
                    return

                if global_vars.gamemaster_role not in global_vars.server.get_member(message.author.id).roles:
                    await message_utils.safe_send(message.author, "You don't have permission to do that.")
                    return

                bot_nick = global_vars.server.get_member(bot_client.client.user.id).display_name
                channel_name = global_vars.channel.name
                server_name = global_vars.server.name
                storytellers = [st.display_name for st in global_vars.gamemaster_role.members]

                if len(storytellers) == 1:
                    sts = storytellers[0]
                elif len(storytellers) == 2:
                    sts = storytellers[0] + " and " + storytellers[1]
                else:
                    sts = (
                        ", ".join([x for x in storytellers[:-1]])
                        + ", and "
                        + storytellers[-1]
                    )

                game_settings = model.settings.GameSettings.load()
                st_channel = bot_client.client.get_channel(game_settings.get_st_channel(player.id))
                if not st_channel:
                    st_channel = await model.channels.ChannelManager(bot_client.client).create_channel(game_settings,
                                                                                                       player)
                    await message_utils.safe_send(message.author,
                                    f'Successfully created the channel https://discord.com/channels/{global_vars.server.id}/{st_channel.id}!')

                await message_utils.safe_send(
                    player,
                    "Hello, {player_nick}! {storyteller_nick} welcomes you to Blood on the Clocktower on Discord! I'm {bot_nick}, the bot used on #{channel_name} in {server_name} to run games. Your Storyteller channel for this game is #{st_channel}\n\nThis is where you'll perform your private messaging during the game. To send a pm to a player, type `@pm [name]`.\n\nFor more info, type `@help`, or ask the storyteller(s): {storytellers}.".format(
                        bot_nick=bot_nick,
                        channel_name=channel_name,
                        server_name=server_name,
                        st_channel=st_channel,
                        storytellers=sts,
                        player_nick=player.display_name,
                        storyteller_nick=global_vars.server.get_member(
                            message.author.id
                        ).display_name,
                    ),
                )
                await message_utils.safe_send(message.author, f'Welcomed {player.display_name} successfully!')
                return

            # Starts game
            elif command == "startgame":
                game_settings: model.settings.GameSettings = model.settings.GameSettings.load()

                if global_vars.game is not game.NULL_GAME:
                    await message_utils.safe_send(message.author, "There's already an ongoing game!")
                    return

                if not global_vars.gamemaster_role in global_vars.server.get_member(message.author.id).roles:
                    await message_utils.safe_send(message.author, "You don't have permission to start a game.")
                    return

                msg = await message_utils.safe_send(message.author,
                                                    "What is the seating order? (separate users with line breaks)")
                try:
                    order_message = await bot_client.client.wait_for(
                        "message",
                        check=(lambda x: x.author == message.author and x.channel == msg.channel),
                        timeout=200,
                    )
                except asyncio.TimeoutError:
                    await message_utils.safe_send(message.author, "Time out.")
                    return

                if order_message.content == "cancel":
                    await message_utils.safe_send(message.author, "Game cancelled!")
                    return

                order: list[str] = order_message.content.split("\n")

                users: list[discord.Member] = []
                for person in order:
                    name = await player_utils.select_player(message.author, person, global_vars.server.members)
                    if name is None:
                        return
                    users.append(name)

                st_channels: list[discord.TextChannel] = [
                    bot_client.client.get_channel(game_settings.get_st_channel(x.id)) for
                    x in users]

                players_missing_channels = [users[index] for index, channel in enumerate(st_channels) if channel is None]
                if players_missing_channels:
                    await warn_missing_player_channels(message.author, players_missing_channels)
                    return

                await message_utils.safe_send(message.author,
                                              "What are the corresponding roles? (also separated with line breaks)")
                try:
                    roles_message = await bot_client.client.wait_for(
                        "message",
                        check=(lambda x: x.author == message.author and x.channel == msg.channel),
                        timeout=200,
                    )
                except asyncio.TimeoutError:
                    await message_utils.safe_send(message.author, "Timed out.")
                    return

                if roles_message.content == "cancel":
                    await message_utils.safe_send(message.author, "Game cancelled!")
                    return

                roles: list[str] = roles_message.content.split("\n")

                if len(roles) != len(order):
                    await message_utils.safe_send(message.author, "Players and roles do not match.")
                    return

                characters: list[type[model.characters.Character]] = []
                for text in roles:
                    role = text_utils.str_cleanup(text, [",", " ", "-", "'"])
                    try:
                        role = character_utils.str_to_class(role)
                    except AttributeError:
                        await message_utils.safe_send(message.author, "Role not found: {}.".format(text))
                        return
                    characters.append(role)

                # Role Stuff
                rls = {global_vars.player_role, global_vars.traveler_role, global_vars.dead_vote_role, global_vars.ghost_role}
                for memb in global_vars.server.members:
                    print(memb)
                    if global_vars.gamemaster_role in global_vars.server.get_member(memb.id).roles:
                        pass
                    else:
                        for rl in set(global_vars.server.get_member(memb.id).roles).intersection(
                            rls
                        ):
                            await memb.remove_roles(rl)

                for index, user in enumerate(users):
                    if global_vars.gamemaster_role in user.roles:
                        await user.remove_roles(global_vars.gamemaster_role)
                    if global_vars.observer_role in user.roles:
                        await user.remove_roles(global_vars.observer_role)
                    await user.add_roles(global_vars.player_role)
                    if issubclass(characters[index], model.characters.Traveler):
                        await user.add_roles(global_vars.traveler_role)

                alignments: list[str] = []
                for role in characters:
                    if issubclass(role, model.characters.Traveler):
                        msg = await message_utils.safe_send(
                            message.author,
                            "What alignment is the {}?".format(role(None).role_name)
                        )
                        try:
                            alignment = await bot_client.client.wait_for(
                                "message",
                                check=(lambda x: x.author == message.author and x.channel == msg.channel),
                                timeout=200,
                            )
                        except asyncio.TimeoutError:
                            await message_utils.safe_send(message.author, "Timed out.")
                            return

                        if alignment.content == "cancel":
                            await message_utils.safe_send(message.author, "Game cancelled!")
                            return

                        if (
                            alignment.content.lower() != "good"
                            and alignment.content.lower() != "evil"
                        ):
                            await message_utils.safe_send(message.author,
                                                          "The alignment must be 'good' or 'evil' exactly.")
                            return

                        alignments.append(alignment.content.lower())

                    elif issubclass(role, model.characters.Townsfolk) or issubclass(role, model.characters.Outsider):
                        alignments.append("good")

                    elif issubclass(role, model.characters.Minion) or issubclass(role, model.characters.Demon):
                        alignments.append("evil")

                indicies = [x for x in range(len(users))]

                seating_order: list[model.player.Player] = []
                for x in indicies:
                    seating_order.append(
                        model.player.Player(characters[x], alignments[x], users[x], st_channels[x], position=x)
                    )

                msg = await message_utils.safe_send(
                    message.author,
                    "What roles are on the script? (send the text of the json file from the script creator)"
                )
                try:
                    script_message = await bot_client.client.wait_for(
                        "message",
                        check=(lambda x: x.author == message.author and x.channel == msg.channel),
                        timeout=200,
                    )
                except asyncio.TimeoutError:
                    await message_utils.safe_send(message.author, "Timed out.")
                    return

                if script_message.content == "cancel":
                    await message_utils.safe_send(message.author, "Game cancelled!")
                    return

                script_list = ''.join(script_message.content.split())[8:-3].split('"},{"id":"')

                script = model.game.script.Script(script_list)

                # Setup ST channels
                tasks = [model.channels.ChannelManager(bot_client.client).remove_ghost(st_channel.id) for st_channel in
                         st_channels]
                await asyncio.gather(*tasks)
                await model.channels.channel_utils.reorder_channels(st_channels)

                await message_utils.safe_send(
                    global_vars.channel,
                    "{}, welcome to Blood on the Clocktower! Go to sleep.".format(
                        global_vars.player_role.mention
                    ),
                )

                message_text = "**Seating Order:**"
                for person in seating_order:
                    display_name_with_hand = person.display_name
                    if person.hand_raised:
                        display_name_with_hand += " ✋"
                    message_text += "\n{}".format(display_name_with_hand)
                    if isinstance(person.character, model.characters.SeatingOrderModifier):
                        message_text += person.character.seating_order_message(
                            seating_order
                        )
                seating_order_message = await message_utils.safe_send(global_vars.channel, message_text)
                await seating_order_message.pin()

                num_full_players = len([x for x in characters if not issubclass(x, model.characters.Traveler)])
                distribution: tuple[int, int, int, int] = (-1, -1, -1, -1)
                if num_full_players == 5:
                    distribution = (3, 0, 1, 1)
                elif num_full_players == 6:
                    distribution = (3, 1, 1, 1)
                elif 7 <= num_full_players <= 15:
                    outsiders = int((num_full_players - 1) % 3)
                    minions = int(math.floor((num_full_players - 1) / 3) - 1)
                    distribution = (num_full_players - (outsiders + minions + 1), outsiders, minions, 1)

                msg = await message_utils.safe_send(
                    global_vars.channel,
                    f"There are {num_full_players} non-Traveler players. The default distribution is {distribution[0]} Townsfolk, {distribution[1]} Outsider{'s' if distribution[1] != 1 else ''}, {distribution[2]} Minion{'s' if distribution[2] != 1 else ''}, and {distribution[3]} Demon."
                )
                await msg.pin()

                # Create info channel seating order message if info channel exists
                info_channel_message = None
                if global_vars.info_channel:
                    try:
                        info_channel_message = await message_utils.safe_send(global_vars.info_channel, message_text)
                        if info_channel_message:
                            await info_channel_message.pin()
                    except Exception as e:
                        print(f"Error creating info channel seating order message: {e}")

                global_vars.game = game.Game(seating_order, seating_order_message, info_channel_message, script)

                game_utils.backup("current_game.pckl")
                await update_presence(bot_client.client)

                return

            # Ends game
            elif command == "endgame":

                if global_vars.game is game.NULL_GAME:
                    await message_utils.safe_send(message.author, "There's no game right now.")
                    return

                if not global_vars.gamemaster_role in global_vars.server.get_member(message.author.id).roles:
                    await message_utils.safe_send(message.author, "You don't have permission to end the game.")
                    return

                argument = argument.lower()

                if argument != "good" and argument != "evil" and argument != "tie":
                    await message_utils.safe_send(message.author,
                                                  "The winner must be 'good' or 'evil' or 'tie' exactly.")
                    return

                for memb in global_vars.game.storytellers:
                    await message_utils.safe_send(
                        memb.user,
                        f"{message.author.display_name} has ended the game! {'Good won!' if argument == 'good' else 'Evil won!' if argument == 'evil' else ''}  Please wait for the bot to finish.",
                    )

                await global_vars.game.end(argument.lower())
                if global_vars.game is not game.NULL_GAME:
                    game_utils.backup("current_game.pckl")
                return

            # Starts day
            elif command == "startday":

                if global_vars.game is game.NULL_GAME:
                    await message_utils.safe_send(message.author, "There's no game right now.")
                    return

                if not global_vars.gamemaster_role in global_vars.server.get_member(message.author.id).roles:
                    await message_utils.safe_send(message.author, "You don't have permission to start the day.")
                    return

                if global_vars.game.isDay == True:
                    await message_utils.safe_send(message.author, "It's already day!")
                    return

                if argument == "":
                    await global_vars.game.start_day(origin=message.author)
                    if global_vars.game is not game.NULL_GAME:
                        game_utils.backup("current_game.pckl")
                    return

                people = [
                    await player_utils.select_player(message.author, person, global_vars.game.seatingOrder)
                    for person in argument.split(" ")
                ]
                if None in people:
                    return

                await global_vars.game.start_day(kills=people, origin=message.author)
                if global_vars.game is not game.NULL_GAME:
                    game_utils.backup("current_game.pckl")
                return

            # Ends day
            elif command == "endday":

                if global_vars.game is game.NULL_GAME:
                    await message_utils.safe_send(message.author, "There's no game right now.")
                    return

                if not global_vars.gamemaster_role in global_vars.server.get_member(message.author.id).roles:
                    await message_utils.safe_send(message.author, "You don't have permission to end the day.")
                    return

                if global_vars.game.isDay == False:
                    await message_utils.safe_send(message.author, "It's already night!")
                    return

                await global_vars.game.days[-1].end()
                if global_vars.game is not game.NULL_GAME:
                    game_utils.backup("current_game.pckl")
                return

            # Kills a player
            elif command == "kill":

                if global_vars.game is game.NULL_GAME:
                    await message_utils.safe_send(message.author, "There's no game right now.")
                    return

                if not global_vars.gamemaster_role in global_vars.server.get_member(message.author.id).roles:
                    await message_utils.safe_send(message.author, "You don't have permission to kill players.")
                    return

                person = await player_utils.select_player(
                    message.author, argument, global_vars.game.seatingOrder
                )
                if person is None:
                    return

                if person.is_ghost:
                    await message_utils.safe_send(message.author, "{} is already dead.".format(person.display_name))
                    return

                await person.kill(force=True)
                if global_vars.game is not game.NULL_GAME:
                    game_utils.backup("current_game.pckl")
                return

            # Executes a player
            elif command == "execute":

                if global_vars.game is game.NULL_GAME:
                    await message_utils.safe_send(message.author, "There's no game right now.")
                    return

                if not global_vars.gamemaster_role in global_vars.server.get_member(message.author.id).roles:
                    await message_utils.safe_send(message.author, "You don't have permission to execute players.")
                    return

                person = await player_utils.select_player(
                    message.author, argument, global_vars.game.seatingOrder
                )
                if person is None:
                    return

                await person.execute(message.author)
                if global_vars.game is not game.NULL_GAME:
                    game_utils.backup("current_game.pckl")
                return

            # Exiles a traveler
            elif command == "exile":

                if global_vars.game is game.NULL_GAME:
                    await message_utils.safe_send(message.author, "There's no game right now.")
                    return

                if not global_vars.gamemaster_role in global_vars.server.get_member(message.author.id).roles:
                    await message_utils.safe_send(message.author, "You don't have permission to exile travelers.")
                    return

                person = await player_utils.select_player(
                    message.author, argument, global_vars.game.seatingOrder
                )
                if person is None:
                    return

                if not isinstance(person.character, model.characters.Traveler):
                    await message_utils.safe_send(message.author, "{} is not a traveler.".format(person.display_name))

                await person.character.exile(person, message.author)
                if global_vars.game is not game.NULL_GAME:
                    game_utils.backup("current_game.pckl")
                return

            # Revives a player
            elif command == "revive":

                if global_vars.game is game.NULL_GAME:
                    await message_utils.safe_send(message.author, "There's no game right now.")
                    return

                if not global_vars.gamemaster_role in global_vars.server.get_member(message.author.id).roles:
                    await message_utils.safe_send(message.author, "You don't have permission to revive players.")
                    return

                person = await player_utils.select_player(
                    message.author, argument, global_vars.game.seatingOrder
                )
                if person is None:
                    return

                if not person.is_ghost:
                    await message_utils.safe_send(message.author, "{} is not dead.".format(person.display_name))
                    return

                await person.revive()
                if global_vars.game is not game.NULL_GAME:
                    game_utils.backup("current_game.pckl")
                return

            # Changes role
            elif command == "changerole":

                if global_vars.game is game.NULL_GAME:
                    await message_utils.safe_send(message.author, "There's no game right now.")
                    return

                if not global_vars.gamemaster_role in global_vars.server.get_member(message.author.id).roles:
                    await message_utils.safe_send(message.author, "You don't have permission to change roles.")
                    return

                person = await player_utils.select_player(
                    message.author, argument, global_vars.game.seatingOrder
                )
                if person is None:
                    return

                msg = await message_utils.safe_send(message.author, "What is the new role?")
                try:
                    role = await bot_client.client.wait_for(
                        "message",
                        check=(lambda x: x.author == message.author and x.channel == msg.channel),
                        timeout=200,
                    )
                except asyncio.TimeoutError:
                    await message_utils.safe_send(message.author, "Timed out.")
                    return

                role = role.content.lower()

                if role == "cancel":
                    await message_utils.safe_send(message.author, "Role change cancelled!")
                    return

                role = text_utils.str_cleanup(role, [",", " ", "-", "'"])
                try:
                    role = character_utils.str_to_class(role)
                except AttributeError:
                    await message_utils.safe_send(message.author, "Role not found: {}.".format(role))
                    return

                await person.change_character(role)
                await message_utils.safe_send(message.author, "Role change successful!")
                if global_vars.game is not game.NULL_GAME:
                    game_utils.backup("current_game.pckl")
                return

            # Changes alignment
            elif command == "changealignment":

                if global_vars.game is game.NULL_GAME:
                    await message_utils.safe_send(message.author, "There's no game right now.")
                    return

                if not global_vars.gamemaster_role in global_vars.server.get_member(message.author.id).roles:
                    await message_utils.safe_send(message.author, "You don't have permission to change alignments.")
                    return

                person = await player_utils.select_player(
                    message.author, argument, global_vars.game.seatingOrder
                )
                if person is None:
                    return

                msg = await message_utils.safe_send(message.author, "What is the new alignment?")
                try:
                    alignment = await bot_client.client.wait_for(
                        "message",
                        check=(lambda x: x.author == message.author and x.channel == msg.channel),
                        timeout=200,
                    )
                except asyncio.TimeoutError:
                    await message_utils.safe_send(message.author, "Timed out.")
                    return

                alignment = alignment.content.lower()

                if alignment == "cancel":
                    await message_utils.safe_send(message.author, "Alignment change cancelled!")
                    return

                if alignment != "good" and alignment != "evil":
                    await message_utils.safe_send(message.author, "The alignment must be 'good' or 'evil' exactly.")
                    return

                await person.change_alignment(alignment)
                await message_utils.safe_send(message.author, "Alignment change successful!")
                if global_vars.game is not game.NULL_GAME:
                    game_utils.backup("current_game.pckl")
                return

            # Adds an ability to an AbilityModifier character
            elif command == "changeability":
                if global_vars.game is game.NULL_GAME:
                    await message_utils.safe_send(message.author, "There's no game right now.")
                    return

                if not global_vars.gamemaster_role in global_vars.server.get_member(message.author.id).roles:
                    await message_utils.safe_send(message.author, "You don't have permission to give abilities.")
                    return

                person = await player_utils.select_player(
                    message.author, argument, global_vars.game.seatingOrder
                )
                if person is None:
                    return

                if not isinstance(person.character, model.characters.AbilityModifier):
                    await message_utils.safe_send(message.author,
                                                  "The {} cannot gain abilities.".format(person.character.role_name))
                    return

                msg = await message_utils.safe_send(message.author, "What is the new ability role?")
                try:
                    role = await bot_client.client.wait_for(
                        "message",
                        check=(lambda x: x.author == message.author and x.channel == msg.channel),
                        timeout=200,
                    )
                except asyncio.TimeoutError:
                    await message_utils.safe_send(message.author, "Timed out.")
                    return

                role = role.content.lower()

                if role == "cancel":
                    await message_utils.safe_send(message.author, "New ability cancelled!")
                    return

                role = text_utils.str_cleanup(role, [",", " ", "-", "'"])
                try:
                    role = character_utils.str_to_class(role)
                except AttributeError:
                    await message_utils.safe_send(message.author, "Role not found: {}.".format(role))
                    return

                person.character.add_ability(role)
                await message_utils.safe_send(message.author, "New ability added.")
                return

            # removes an ability from an AbilityModifier ability (useful if a nested ability is gained)
            elif command == "removeability":
                if global_vars.game is game.NULL_GAME:
                    await message_utils.safe_send(message.author, "There's no game right now.")
                    return

                if not global_vars.gamemaster_role in global_vars.server.get_member(message.author.id).roles:
                    await message_utils.safe_send(message.author, "You don't have permission to remove abilities.")
                    return

                person = await player_utils.select_player(
                    message.author, argument, global_vars.game.seatingOrder
                )
                if person is None:
                    return

                if not isinstance(person.character, model.characters.AbilityModifier):
                    await message_utils.safe_send(message.author, "The {} cannot gain abilities to clear.".format(
                        person.character.role_name))
                    return

                removed_ability = person.character.clear_ability()
                if (removed_ability):
                    await message_utils.safe_send(message.author,
                                                  "Ability removed: {}".format(removed_ability.role_name))
                else:
                    await message_utils.safe_send(message.author, "No ability to remove")
                return

            # Marks as inactive
            elif command == "makeinactive":

                if global_vars.game is game.NULL_GAME:
                    await message_utils.safe_send(message.author, "There's no game right now.")
                    return

                if not global_vars.gamemaster_role in global_vars.server.get_member(message.author.id).roles:
                    await message_utils.safe_send(message.author, "You don't have permission to make players inactive.")
                    return

                person = await player_utils.select_player(
                    message.author, argument, global_vars.game.seatingOrder
                )
                if person is None:
                    return

                await person.make_inactive()
                if global_vars.game is not game.NULL_GAME:
                    game_utils.backup("current_game.pckl")
                return

            # Marks as inactive
            elif command == "undoinactive":

                if global_vars.game is game.NULL_GAME:
                    await message_utils.safe_send(message.author, "There's no game right now.")
                    return

                if not global_vars.gamemaster_role in global_vars.server.get_member(message.author.id).roles:
                    await message_utils.safe_send(message.author, "You don't have permission to make players active.")
                    return

                person = await player_utils.select_player(
                    message.author, argument, global_vars.game.seatingOrder
                )
                if person is None:
                    return

                await person.undo_inactive()
                if global_vars.game is not game.NULL_GAME:
                    game_utils.backup("current_game.pckl")
                return

            # Marks as checked in
            elif command == "checkin":

                if global_vars.game is game.NULL_GAME:
                    await message_utils.safe_send(message.author, "There's no game right now.")
                    return

                if global_vars.gamemaster_role not in global_vars.server.get_member(message.author.id).roles:
                    await message_utils.safe_send(message.author,
                                                  "You don't have permission to mark a player cheacked in.")
                    return

                people = [
                    await player_utils.select_player(message.author, person, global_vars.game.seatingOrder)
                    for person in argument.split(" ")
                ]
                if None in people:
                    return
                for person in people:
                    person.has_checked_in = True

                await message_utils.safe_send(message.author, "Successfully marked as checked in: {}".format(
                    ", ".join([person.display_name for person in people])))
                if global_vars.game is not game.NULL_GAME:
                    game_utils.backup("current_game.pckl")

                await player_utils.check_and_print_if_one_or_zero_to_check_in()
                return

            # Marks as not checked in
            elif command == "undocheckin":

                if global_vars.game is game.NULL_GAME:
                    await message_utils.safe_send(message.author, "There's no game right now.")
                    return

                if global_vars.gamemaster_role not in global_vars.server.get_member(message.author.id).roles:
                    await message_utils.safe_send(message.author, "You don't have permission to make players active.")
                    return

                people = [
                    await player_utils.select_player(message.author, person, global_vars.game.seatingOrder)
                    for person in argument.split(" ")
                ]
                if None in people:
                    return

                for person in people:
                    person.has_checked_in = False

                await message_utils.safe_send(message.author, "Successfully marked as not checked in: {}".format(
                    ", ".join([person.display_name for person in people])))

                if global_vars.game is not game.NULL_GAME:
                    game_utils.backup("current_game.pckl")

                await player_utils.check_and_print_if_one_or_zero_to_check_in()
                return

            # Adds traveler
            elif command == "addtraveler" or command == "addtraveller":

                if global_vars.game is game.NULL_GAME:
                    await message_utils.safe_send(message.author, "There's no game right now.")
                    return

                if global_vars.gamemaster_role not in global_vars.server.get_member(message.author.id).roles:
                    await message_utils.safe_send(message.author, "You don't have permission to add travelers.")
                    return

                person = await player_utils.select_player(message.author, argument, global_vars.server.members)
                if person is None:
                    return

                if player_utils.get_player(person) is not None:
                    await message_utils.safe_send(message.author, "{} is already in the game.".format(
                        person.display_name if person.display_name else person.name))
                    return

                st_channel = global_vars.server.get_channel(
                    model.settings.GameSettings.load().get_st_channel(person.id))
                if not st_channel:
                    await warn_missing_player_channels(message.author, [person])
                    return

                msg = await message_utils.safe_send(message.author, "What role?")
                try:
                    text = await bot_client.client.wait_for(
                        "message",
                        check=(lambda x: x.author == message.author and x.channel == msg.channel),
                        timeout=200,
                    )
                except asyncio.TimeoutError:
                    await message_utils.safe_send(message.author, "Timed out.")
                    return

                if text.content == "cancel":
                    await message_utils.safe_send(message.author, "Traveler cancelled!")
                    return

                text = text.content

                role = text_utils.str_cleanup(text, [",", " ", "-", "'"])

                try:
                    role = character_utils.str_to_class(role)
                except AttributeError:
                    await message_utils.safe_send(message.author, "Role not found: {}.".format(text))
                    return

                if not issubclass(role, model.characters.Traveler):
                    await message_utils.safe_send(message.author, "{} is not a traveler role.".format(text))
                    return

                # Determine position in order
                msg = await message_utils.safe_send(message.author,
                                                    "Where in the order are they? (send the player before them or a one-indexed integer)")
                try:
                    pos = await bot_client.client.wait_for(
                        "message",
                        check=(lambda x: x.author == message.author and x.channel == msg.channel),
                        timeout=200,
                    )

                except asyncio.TimeoutError:
                    await message_utils.safe_send(message.author, "Timed out.")
                    return

                if pos.content == "cancel":
                    await message_utils.safe_send(message.author, "Traveler cancelled!")
                    return

                pos = pos.content

                try:
                    pos = int(pos) - 1
                except ValueError:
                    player = await player_utils.select_player(message.author, pos, global_vars.game.seatingOrder)
                    if player is None:
                        return
                    pos = player.position + 1

                # Determine alignment
                msg = await message_utils.safe_send(message.author, "What alignment are they?")
                try:
                    alignment = await bot_client.client.wait_for(
                        "message",
                        check=(lambda x: x.author == message.author and x.channel == msg.channel),
                        timeout=200,
                    )

                except asyncio.TimeoutError:
                    await message_utils.safe_send(message.author, "Timed out.")
                    return

                if alignment.content == "cancel":
                    await message_utils.safe_send(message.author, "Traveler cancelled!")
                    return

                if (
                    alignment.content.lower() != "good"
                    and alignment.content.lower() != "evil"
                ):
                    await message_utils.safe_send(message.author, "The alignment must be 'good' or 'evil' exactly.")
                    return

                await global_vars.game.add_traveler(
                    model.player.Player(role, alignment.content.lower(), person, st_channel, position=pos)
                )
                if global_vars.game is not game.NULL_GAME:
                    game_utils.backup("current_game.pckl")
                return

            # Removes traveler
            elif command == "removetraveler" or command == "removetraveller":

                if global_vars.game is game.NULL_GAME:
                    await message_utils.safe_send(message.author, "There's no game right now.")
                    return

                if not global_vars.gamemaster_role in global_vars.server.get_member(message.author.id).roles:
                    await message_utils.safe_send(message.author, "You don't have permission to remove travelers.")
                    return

                person = await player_utils.select_player(
                    message.author, argument, global_vars.game.seatingOrder
                )
                if person is None:
                    return

                await global_vars.game.remove_traveler(person)
                if global_vars.game is not game.NULL_GAME:
                    game_utils.backup("current_game.pckl")
                return

            # Resets the seating chart
            elif command == "resetseats":
                if global_vars.game is game.NULL_GAME:
                    await message_utils.safe_send(message.author, "There's no game right now.")

                if not global_vars.gamemaster_role in global_vars.server.get_member(message.author.id).roles:
                    await message_utils.safe_send(message.author,
                                                  "You don't have permission to change the seating chart.")
                    return

                await global_vars.game.reseat(global_vars.game.seatingOrder)
                return

            # Changes seating chart
            elif command == "reseat":

                if global_vars.game is game.NULL_GAME:
                    await message_utils.safe_send(message.author, "There's no game right now.")

                if not global_vars.gamemaster_role in global_vars.server.get_member(message.author.id).roles:
                    await message_utils.safe_send(message.author,
                                                  "You don't have permission to change the seating chart.")
                    return

                msg = await message_utils.safe_send(message.author,
                                                    "What is the seating order? (separate users with line breaks)")
                try:
                    order_message = await bot_client.client.wait_for(
                        "message",
                        check=(lambda x: x.author == message.author and x.channel == msg.channel),
                        timeout=200,
                    )

                except asyncio.TimeoutError:
                    await message_utils.safe_send(message.author, "Timed out.")
                    return

                if order_message.content == "cancel":
                    await message_utils.safe_send(message.author, "Reseating cancelled!")
                    return

                if order_message.content == "none":
                    await global_vars.game.reseat(global_vars.game.seatingOrder)

                order = [
                    await player_utils.select_player(message.author, person, global_vars.game.seatingOrder)
                    for person in order_message.content.split("\n")
                ]
                if None in order:
                    return

                await global_vars.game.reseat(order)
                if global_vars.game is not game.NULL_GAME:
                    game_utils.backup("current_game.pckl")
                return

            # Poisons
            elif command == "poison":
                if global_vars.game is game.NULL_GAME:
                    await message_utils.safe_send(message.author, "There's no game right now.")
                    return

                if not global_vars.gamemaster_role in global_vars.server.get_member(message.author.id).roles:
                    await message_utils.safe_send(message.author, "You don't have permission to poison players.")
                    return

                person = await player_utils.select_player(
                    message.author, argument, global_vars.game.seatingOrder
                )
                if person is None:
                    return

                person.character.poison()

                await message_utils.safe_send(message.author, "Successfully poisoned {}!".format(person.display_name))
                return

            # Unpoisons
            elif command == "unpoison":
                if global_vars.game is game.NULL_GAME:
                    await message_utils.safe_send(message.author, "There's no game right now.")
                    return

                if not global_vars.gamemaster_role in global_vars.server.get_member(message.author.id).roles:
                    await message_utils.safe_send(message.author, "You don't have permission to revive players.")
                    return

                person = await player_utils.select_player(
                    message.author, argument, global_vars.game.seatingOrder
                )
                if person is None:
                    return

                person.character.unpoison()
                await message_utils.safe_send(message.author, "Successfully unpoisoned {}!".format(person.display_name))
                return

            # Cancels a nomination
            elif command == "cancelnomination":
                if global_vars.game is game.NULL_GAME:
                    await message_utils.safe_send(message.author, "There's no game right now.")
                    return

                if not global_vars.gamemaster_role in global_vars.server.get_member(message.author.id).roles:
                    await message_utils.safe_send(message.author, "You don't have permission to cancel nominations.")
                    return

                if global_vars.game.isDay == False:
                    await message_utils.safe_send(message.author, "It's not day right now.")
                    return

                if global_vars.game.days[-1].votes == [] or global_vars.game.days[-1].votes[-1].done == True:
                    await message_utils.safe_send(message.author, "There's no vote right now.")
                    return

                # Reset hand status for all players
                for player_in_game in global_vars.game.seatingOrder:
                    player_in_game.hand_raised = False
                    player_in_game.hand_locked_for_vote = False

                await global_vars.game.update_seating_order_message()

                current_nomination = global_vars.game.days[-1].votes[-1]
                nominator = current_nomination.nominator

                if nominator:
                    # check for storyteller
                    nominator.can_nominate = True

                await current_nomination.delete()
                await global_vars.game.days[-1].open_pms()
                await global_vars.game.days[-1].open_noms()
                await message_utils.safe_send(global_vars.channel, "Nomination canceled!")
                if global_vars.game is not game.NULL_GAME:
                    game_utils.backup("current_game.pckl")
                return

            # Sets a deadline
            elif command == "setdeadline":
                if global_vars.game is game.NULL_GAME:
                    await message_utils.safe_send(message.author, "There's no game right now.")
                    return

                if global_vars.gamemaster_role not in global_vars.server.get_member(message.author.id).roles:
                    await message_utils.safe_send(message.author, "You don't have permission to set deadlines.")
                    return

                if not global_vars.game.isDay:
                    await message_utils.safe_send(message.author, "It's not day right now.")
                    return

                deadline = time_utils.parse_deadline(argument)

                if deadline is None:
                    await message_utils.safe_send(message.author,
                                                  "Unrecognized format. Please provide a deadline in the format 'HH:MM', '+[HHh][MMm]', or a Unix timestamp.")
                    return

                if len(global_vars.game.days[-1].deadlineMessages) > 0:
                    previous_deadline = global_vars.game.days[-1].deadlineMessages[-1]
                    try:
                        await (
                            await global_vars.channel.fetch_message(previous_deadline)
                        ).unpin()
                    except discord.errors.NotFound:
                        print("Missing message: ", str(previous_deadline))
                    except discord.errors.DiscordServerError:
                        print("Discord server error: ", str(previous_deadline))
                announcement = await message_utils.safe_send(
                    global_vars.channel,
                    "{}, nominations are open. The deadline is <t:{}:R> at <t:{}:t> unless someone nominates or everyone skips.".format(
                        global_vars.player_role.mention,
                        str(int(deadline.timestamp())),
                        str(int(deadline.timestamp()))
                    ),
                )
                await announcement.pin()
                global_vars.game.days[-1].deadlineMessages.append(announcement.id)
                await global_vars.game.days[-1].open_noms()

            # Gives a dead vote
            elif command == "givedeadvote":
                if global_vars.game is game.NULL_GAME:
                    await message_utils.safe_send(message.author, "There's no game right now.")
                    return

                if not global_vars.gamemaster_role in global_vars.server.get_member(message.author.id).roles:
                    await message_utils.safe_send(message.author, "You don't have permission to give dead votes.")
                    return

                person = await player_utils.select_player(
                    message.author, argument, global_vars.game.seatingOrder
                )
                if person is None:
                    return

                await person.add_dead_vote()
                if global_vars.game is not game.NULL_GAME:
                    game_utils.backup("current_game.pckl")
                return

            # Removes a dead vote
            elif command == "removedeadvote":
                if global_vars.game is game.NULL_GAME:
                    await message_utils.safe_send(message.author, "There's no game right now.")
                    return

                if not global_vars.gamemaster_role in global_vars.server.get_member(message.author.id).roles:
                    await message_utils.safe_send(message.author, "You don't have permission to remove dead votes.")
                    return

                person = await player_utils.select_player(
                    message.author, argument, global_vars.game.seatingOrder
                )
                if person is None:
                    return

                await person.remove_dead_vote()
                if global_vars.game is not game.NULL_GAME:
                    game_utils.backup("current_game.pckl")
                return

            # Sends a message tally
            elif command == "messagetally":
                if global_vars.game is game.NULL_GAME:
                    await message_utils.safe_send(message.author, "There's no game right now.")
                    return

                if global_vars.gamemaster_role not in global_vars.server.get_member(message.author.id).roles:
                    await message_utils.safe_send(message.author,
                                                  "You don't have permission to report the message tally.")
                    return

                if global_vars.game.days == []:
                    await message_utils.safe_send(message.author, "There have been no days.")
                    return

                try:
                    idn = int(argument)
                except ValueError:
                    await message_utils.safe_send(message.author, "Invalid message ID: {}".format(argument))
                    return

                try:
                    origin_msg = await global_vars.channel.fetch_message(idn)
                except discord.errors.NotFound:
                    await message_utils.safe_send(message.author, "Message not found by ID: {}".format(argument))
                    return

                message_tally = {
                    X: 0 for X in itertools.combinations(global_vars.game.seatingOrder, 2)
                }
                for person in global_vars.game.seatingOrder:
                    for msg in person.message_history:
                        if msg["from_player"] == person:
                            if msg["time"] >= origin_msg.created_at:
                                if (person, msg["to_player"]) in message_tally:
                                    message_tally[(person, msg["to_player"])] += 1
                                elif (msg["to_player"], person) in message_tally:
                                    message_tally[(msg["to_player"], person)] += 1
                                else:
                                    message_tally[(person, msg["to_player"])] = 1
                sorted_tally = sorted(message_tally.items(), key=lambda x: -x[1])
                message_text = "Message Tally:"
                for pair in sorted_tally:
                    if pair[1] > 0:
                        message_text += "\n> {person1} - {person2}: {n}".format(
                            person1=pair[0][0].display_name, person2=pair[0][1].display_name, n=pair[1]
                        )
                    else:
                        message_text += "\n> All other pairs: 0"
                        break
                await message_utils.safe_send(message.author, message_text)
            elif command == "whispers":
                person = None
                if global_vars.gamemaster_role in global_vars.server.get_member(message.author.id).roles:
                    argument = argument.split(" ")
                    if len(argument) != 1:
                        await message_utils.safe_send(message.author, "Usage: @whispers <player>")
                        return
                    if len(argument) == 1:
                        person = await player_utils.select_player(
                            message.author, argument[0], global_vars.game.seatingOrder + global_vars.game.storytellers
                        )
                else:
                    person = player_utils.get_player(message.author)
                if not person:
                    await message_utils.safe_send(message.author,
                                                  "You are not in the game. You have no message history.")
                    return

                # initialize counts with zero for all players
                day = 1
                counts = OrderedDict([(player, 0) for player in global_vars.game.seatingOrder])

                for msg in person.message_history:
                    if msg["day"] != day:
                        # share summary and reset counts
                        message_text = "Day {}\n".format(day)
                        for player, count in counts.items():
                            message_text += "{}: {}\n".format(player if player == "Storytellers" else player.display_name, count)
                        await message_utils.safe_send(message.author, message_text)
                        counts = OrderedDict([(player, 0) for player in global_vars.game.seatingOrder])
                        day = msg["day"]
                    if msg["from_player"] == person:
                        if (msg["to_player"] in counts):
                            counts[msg["to_player"]] += 1
                        else:
                            if "Storytellers" in counts:
                                counts["Storytellers"] += 1
                            else:
                                counts["Storytellers"] = 1
                    else:
                        counts[msg["from_player"]] += 1

                message_text = "Day {}\n".format(day)
                for player, count in counts.items():
                    message_text += "{}: {}\n".format(player if player == "Storytellers" else player.display_name, count)
                await message_utils.safe_send(message.author, message_text)
                return
            # Views relevant information about a player
            elif command == "info":
                if global_vars.game is game.NULL_GAME:
                    await message_utils.safe_send(message.author, "There's no game right now.")
                    return

                if not global_vars.gamemaster_role in global_vars.server.get_member(message.author.id).roles:
                    await message_utils.safe_send(message.author,
                                                  "You don't have permission to view player information.")
                    return

                person = await player_utils.select_player(
                    message.author, argument, global_vars.game.seatingOrder
                )
                if person is None:
                    return

                base_info = inspect.cleandoc(f"""
                    Player: {person.display_name}
                    Character: {person.character.role_name}
                    Alignment: {person.alignment}
                    Alive: {not person.is_ghost}
                    Dead Votes: {person.dead_votes}
                    Poisoned: {person.character.is_poisoned}
                    Last Active <t:{int(person.last_active)}:R> at <t:{int(person.last_active)}:t>
                    Has Checked In {person.has_checked_in}
                    ST Channel: {f"https://discord.com/channels/{global_vars.server.id}/{person.st_channel.id}" if person.st_channel else "None"}
                    """)

                # Add Hand Status
                hand_status_info = f"Hand Status: {'Raised' if person.hand_raised else 'Lowered'}"

                # Add Preset Vote Status
                preset_vote_info = "Preset Vote: N/A (No active vote)"
                active_vote = None
                if global_vars.game.isDay and global_vars.game.days[-1].votes and not global_vars.game.days[-1].votes[-1].done:
                    active_vote = global_vars.game.days[-1].votes[-1]

                if active_vote:
                    preset_value = active_vote.presetVotes.get(person.user.id)
                    if preset_value is None:
                        preset_vote_info = "Preset Vote: None"
                    elif preset_value == 0:
                        preset_vote_info = "Preset Vote: No"
                    elif preset_value == 1:
                        preset_vote_info = "Preset Vote: Yes"
                    elif preset_value == 2: # Assuming 2 is for Banshee scream, adjust if needed
                        preset_vote_info = "Preset Vote: Yes (Banshee Scream)"
                    # Add more conditions if other preset_values are possible

                full_info = "\n".join([base_info, hand_status_info, preset_vote_info, person.character.extra_info()])
                await message_utils.safe_send(message.author, full_info)
                return
            # Views relevant information about a player
            elif command == "votehistory":
                if global_vars.game is game.NULL_GAME:
                    await message_utils.safe_send(message.author, "There's no game right now.")
                    return

                if global_vars.gamemaster_role not in global_vars.server.get_member(message.author.id).roles:
                    await message_utils.safe_send(message.author,
                                                  "You don't have permission to view player information.")
                    return

                for index, day in enumerate(global_vars.game.days):
                    votes_for_day = f"Day {index + 1}\n"
                    for vote in day.votes:  # type: model.Vote
                        nominator_name = vote.nominator.display_name if vote.nominator else "the storytellers"
                        nominee_name = vote.nominee.display_name if vote.nominee else "the storytellers"
                        voters = ", ".join([voter.display_name for voter in vote.voted])
                        votes_for_day += f"{nominator_name} -> {nominee_name} ({vote.votes}): {voters}\n"
                    await message_utils.safe_send(message.author, f"```\n{votes_for_day}\n```")
                return
            # Views the grimoire
            elif command == "grimoire":
                if global_vars.game is game.NULL_GAME:
                    await message_utils.safe_send(message.author, "There's no game right now.")
                    return

                if not global_vars.gamemaster_role in global_vars.server.get_member(message.author.id).roles:
                    await message_utils.safe_send(message.author,
                                                  "You don't have permission to view player information.")
                    return

                message_text = "**Grimoire:**"
                for player in global_vars.game.seatingOrder:
                    message_text += "\n{}: {}".format(
                        player.display_name, player.character.role_name
                    )
                    if player.character.is_poisoned and player.is_ghost:
                        message_text += " (Poisoned, Dead)"
                    elif player.character.is_poisoned and not player.is_ghost:
                        message_text += " (Poisoned)"
                    elif not player.character.is_poisoned and player.is_ghost:
                        message_text += " (Dead)"

                await message_utils.safe_send(message.author, message_text)
                return
            # Checks active players
            elif command == "notactive":

                if not global_vars.gamemaster_role in global_vars.server.get_member(message.author.id).roles:
                    await message_utils.safe_send(message.author, "You don't have permission to view that information.")
                    return

                if global_vars.game is game.NULL_GAME:
                    await message_utils.safe_send(message.author, "There's no game right now.")
                    return

                if global_vars.game.isDay == False:
                    await message_utils.safe_send(message.author, "It's not day right now.")
                    return

                notActive = [
                    player
                    for player in global_vars.game.seatingOrder
                    if player.is_active == False and player.alignment != model.player.STORYTELLER_ALIGNMENT
                ]

                if notActive == []:
                    await message_utils.safe_send(message.author, "Everyone has spoken!")
                    return

                message_text = "These players have not spoken:"
                for player in notActive:
                    message_text += "\n{}".format(player.display_name)

                await message_utils.safe_send(message.author, message_text)
                return

            # Checks who can nominate
            elif command == "tocheckin":

                if global_vars.game is game.NULL_GAME:
                    await message_utils.safe_send(message.author, "There's no game right now.")
                    return

                if not global_vars.gamemaster_role in global_vars.server.get_member(message.author.id).roles:
                    await message_utils.safe_send(message.author, "You don't have permission to view that information.")
                    return

                if global_vars.game.isDay:
                    await message_utils.safe_send(message.author, "It's day right now.")
                    return

                to_check_in = [
                    player
                    for player in global_vars.game.seatingOrder
                    if player.has_checked_in == False
                ]
                if not to_check_in:
                    await message_utils.safe_send(message.author, "Everyone has checked in!")
                    return

                message_text = "These players have not checked in:"
                for player in to_check_in:
                    message_text += "\n{}".format(player.display_name)

                await message_utils.safe_send(message.author, message_text)
                return

            # Checks who can nominate
            elif command == "cannominate":

                if global_vars.game is game.NULL_GAME:
                    await message_utils.safe_send(message.author, "There's no game right now.")
                    return

                if global_vars.game.isDay == False:
                    await message_utils.safe_send(message.author, "It's not day right now.")
                    return

                can_nominate = [
                    player
                    for player in global_vars.game.seatingOrder
                    if player.can_nominate == True
                       and player.has_skipped == False
                       and player.alignment != model.player.STORYTELLER_ALIGNMENT
                       and player.is_ghost == False
                ]
                if can_nominate == []:
                    await message_utils.safe_send(message.author, "Everyone has nominated or skipped!")
                    return

                message_text = "These players have not nominated or skipped:"
                for player in can_nominate:
                    message_text += "\n{}".format(player.display_name)

                await message_utils.safe_send(message.author, message_text)
                return

            # Checks who can be nominated
            elif command == "canbenominated":

                if global_vars.game is game.NULL_GAME:
                    await message_utils.safe_send(message.author, "There's no game right now.")
                    return

                if global_vars.game.isDay == False:
                    await message_utils.safe_send(message.author, "It's not day right now.")
                    return

                can_be_nominated = [
                    player
                    for player in global_vars.game.seatingOrder
                    if player.can_be_nominated == True
                ]
                if can_be_nominated == []:
                    await message_utils.safe_send(message.author, "Everyone has been nominated!")
                    return

                message_text = "These players have not been nominated:"
                for player in can_be_nominated:
                    message_text += "\n{}".format(player.display_name)

                await message_utils.safe_send(message.author, message_text)
                return

            # Checks when a given player was last active
            elif command == "lastactive":
                if global_vars.game is game.NULL_GAME:
                    await message_utils.safe_send(message.author, "There's no game right now.")
                    return

                author_roles = global_vars.server.get_member(message.author.id).roles
                if global_vars.gamemaster_role not in author_roles and global_vars.observer_role not in author_roles:
                    await message_utils.safe_send(message.author,
                                                  "You don't have permission to view player information.")
                    return

                last_active = sorted(global_vars.game.seatingOrder, key=lambda p: p.last_active)
                message_text = "Last active time for these players:"
                for player in last_active:
                    last_active_str = str(int(player.last_active))
                    message_text += "\n{}:<t:{}:R> at <t:{}:t>".format(
                        player.display_name, last_active_str, last_active_str)

                await message_utils.safe_send(message.author, message_text)
                return

            # Nominates
            elif command == "nominate":

                if global_vars.game is game.NULL_GAME:
                    await message_utils.safe_send(message.author, "There's no game right now.")
                    return

                if global_vars.game.isDay == False:
                    await message_utils.safe_send(message.author, "It's not day right now.")
                    return

                if global_vars.game.days[-1].isNoms == False:
                    await message_utils.safe_send(message.author, "Nominations aren't open right now.")
                    return

                nominator_player = player_utils.get_player(message.author)
                story_teller_is_nominated = await model.game.vote.is_storyteller(argument)
                person = await player_utils.select_player(
                    message.author, argument, global_vars.game.seatingOrder
                ) if not story_teller_is_nominated else None

                traveler_called = person is not None and isinstance(person.character, model.characters.Traveler)

                banshee_ability_of_player = character_utils.the_ability(nominator_player.character,
                                                                        model.characters.Banshee) if nominator_player else None
                banshee_override = banshee_ability_of_player is not None and banshee_ability_of_player.is_screaming

                if not nominator_player:
                    if not global_vars.gamemaster_role in global_vars.server.get_member(message.author.id).roles:
                        await message_utils.safe_send(message.author, "You aren't in the game, and so cannot nominate.")
                        return
                    else:
                        if len([
                            player for player in global_vars.game.seatingOrder
                            if player.character.role_name == "Riot"
                            if not player.character.is_poisoned
                            if not player.is_ghost
                        ]) > 0:
                            # todo: ask if the nominee dies
                            st_user = message.author
                            msg = await message_utils.safe_send(st_user, "Do they die? yes or no")
                            try:
                                choice = await bot_client.client.wait_for(
                                    "message",
                                    check=(lambda x: x.author == st_user and x.channel == msg.channel),
                                    timeout=200,
                                )
                            except asyncio.TimeoutError:
                                await message_utils.safe_send(st_user, "Message timed out!")
                                return
                            # Cancel
                            if choice.content.lower() == "cancel":
                                await message_utils.safe_send(st_user, "Action cancelled!")
                                return
                            player_dies = False
                            # Yes
                            if choice.content.lower() == "yes" or choice.content.lower() == "y":
                                player_dies = True
                            # No
                            elif choice.content.lower() == "no" or choice.content.lower() == "n":
                                player_dies = False
                            else:
                                await message_utils.safe_send(
                                    st_user, "Your answer must be 'yes,' 'y,' 'no,' or 'n' exactly."
                                )
                                return
                            global_vars.game.days[-1].st_riot_kill_override = player_dies
                else:
                    if global_vars.game.days[-1].riot_active:
                        if not nominator_player.riot_nominee:
                            await message_utils.safe_send(message.author, "Riot is active, you may not nominate.")
                            return
                    if nominator_player.is_ghost and not traveler_called and not nominator_player.riot_nominee and not banshee_override:
                        await message_utils.safe_send(
                            message.author, "You are dead, and so cannot nominate."
                        )
                        return
                    if banshee_override and banshee_ability_of_player.remaining_nominations < 1:
                        await message_utils.safe_send(message.author, "You have already nominated twice.")
                        return
                    if not nominator_player.can_nominate and not traveler_called and not banshee_override:
                        await message_utils.safe_send(message.author, "You have already nominated.")
                        return

                if global_vars.game.script.is_atheist:
                    if story_teller_is_nominated:
                        if None in [x.nominee for x in global_vars.game.days[-1].votes]:
                            await message_utils.safe_send(message.author,
                                                          "The storytellers have already been nominated today.")
                            await message.unpin()
                            return
                        await global_vars.game.days[-1].nomination(None, nominator_player)
                        if global_vars.game is not game.NULL_GAME:
                            game_utils.backup("current_game.pckl")
                        await message.unpin()
                        return

                if person is None:
                    return

                if global_vars.gamemaster_role in global_vars.server.get_member(message.author.id).roles:
                    await global_vars.game.days[-1].nomination(person, None)
                    if global_vars.game is not game.NULL_GAME:
                        game_utils.backup("current_game.pckl")
                    return

                #  make sure that the nominee has not been nominated yet
                if not person.can_be_nominated:
                    await message_utils.safe_send(message.author,
                                                  "{} has already been nominated".format(person.display_name))
                    return

                model.game.vote.remove_banshee_nomination(banshee_ability_of_player)

                await global_vars.game.days[-1].nomination(person, nominator_player)
                if global_vars.game is not game.NULL_GAME:
                    game_utils.backup("current_game.pckl")
                return

            # Votes
            elif command == "vote":

                if global_vars.game is game.NULL_GAME:
                    await message_utils.safe_send(message.author, "There's no game right now.")
                    return

                if global_vars.game.isDay == False:
                    await message_utils.safe_send(message.author, "It's not day right now.")
                    return

                if global_vars.game.days[-1].votes == [] or global_vars.game.days[-1].votes[-1].done == True:
                    await message_utils.safe_send(message.author, "There's no vote right now.")
                    return

                if (
                    argument != "yes"
                    and argument != "y"
                    and argument != "no"
                    and argument != "n"
                ):
                    await message_utils.safe_send(message.author,
                                                  "{} is not a valid vote. Use 'yes', 'y', 'no', or 'n'.".format(
                                                      argument))
                    return

                voudon_in_play = model.game.vote.in_play_voudon()

                vote = global_vars.game.days[-1].votes[-1]

                if global_vars.gamemaster_role in global_vars.server.get_member(message.author.id).roles:
                    msg = await message_utils.safe_send(message.author, "Whose vote is this?")
                    try:
                        reply = await bot_client.client.wait_for(
                            "message",
                            check=(lambda x: x.author == message.author and x.channel == msg.channel),
                            timeout=200,
                        )

                    except asyncio.TimeoutError:
                        await message_utils.safe_send(message.author, "Timed out.")
                        return

                    if reply.content.lower() == "cancel":
                        await message_utils.safe_send(message.author, "Vote cancelled!")
                        return

                    reply = reply.content.lower()

                    person = await player_utils.select_player(
                        message.author, reply, global_vars.game.seatingOrder
                    )
                    if person is None:
                        return

                    if vote.order[vote.position].user != person.user:
                        await message_utils.safe_send(message.author,
                                                      "It's not their vote right now. Do you mean @presetvote?")
                        return

                    vt = int(argument == "yes" or argument == "y")

                    if voudon_in_play and voudon_in_play != person and not person.is_ghost and vt > 0:
                        await message_utils.safe_send(message.author,
                                                      "Voudon is in play. Only the Voudon and dead may vote.")
                        return

                    await vote.vote(vt, voter=person, operator=message.author)
                    if global_vars.game is not game.NULL_GAME:
                        game_utils.backup("current_game.pckl")
                    return

                voting_player = player_utils.get_player(message.author)
                if vote.order[vote.position].user != voting_player.user:
                    await message_utils.safe_send(message.author,
                                                  "It's not your vote right now. Do you mean @presetvote?")
                    return

                vt = int(argument == "yes" or argument == "y")

                if voudon_in_play and voting_player != voudon_in_play and not voting_player.is_ghost and vt > 0:
                    await message_utils.safe_send(message.author,
                                                  "Voudon is in play. Only the Voudon and dead may vote.")
                    return

                await vote.vote(vt, voter=voting_player)
                if global_vars.game is not game.NULL_GAME:
                    game_utils.backup("current_game.pckl")
                return

            # Presets a vote
            elif command == "presetvote" or command == "prevote":

                if global_vars.game is game.NULL_GAME:
                    await message_utils.safe_send(message.author, "There's no game right now.")
                    return

                if global_vars.game.isDay == False:
                    await message_utils.safe_send(message.author, "It's not day right now.")
                    return

                if global_vars.game.days[-1].votes == [] or global_vars.game.days[-1].votes[-1].done == True:
                    await message_utils.safe_send(message.author, "There's no vote right now.")
                    return

                # if player has active banshee ability then they can prevote 0, 1, or 2 as well
                if (
                    argument != "yes"
                    and argument != "y"
                    and argument != "no"
                    and argument != "n"
                    and argument not in ["0", "1", "2"]
                ):
                    await message_utils.safe_send(message.author,
                                                  "{} is not a valid vote. Use 'yes', 'y', 'no', or 'n'.".format(
                                                      argument))
                    return

                vote = global_vars.game.days[-1].votes[-1]
                voudon_in_play = model.game.vote.in_play_voudon()

                if global_vars.gamemaster_role in global_vars.server.get_member(message.author.id).roles:
                    msg = await message_utils.safe_send(message.author, "Whose vote is this?")
                    try:
                        reply = await bot_client.client.wait_for(
                            "message",
                            check=(lambda x: x.author == message.author and x.channel == msg.channel),
                            timeout=200,
                        )

                    except asyncio.TimeoutError:
                        await message_utils.safe_send(message.author, "Timed out.")
                        return

                    if reply.content.lower() == "cancel":
                        await message_utils.safe_send(message.author, "Preset vote cancelled!")
                        return

                    reply = reply.content.lower()

                    person = await player_utils.select_player(
                        message.author, reply, global_vars.game.seatingOrder
                    )
                    if person is None:
                        return

                    player_banshee_ability = character_utils.the_ability(person.character, model.characters.Banshee)
                    banshee_override = player_banshee_ability and player_banshee_ability.is_screaming

                    if argument in ["0", "1", "2"]:
                        if not banshee_override:
                            await message_utils.safe_send(message.author,
                                                          "{} is not a valid vote for this player.".format(argument))
                            return
                        vt = int(argument)
                    else:
                        yes_entered = argument == "yes" or argument == "y"
                        vt = int(yes_entered) * (2 if banshee_override else 1)
                    if voudon_in_play and person != voudon_in_play and not person.is_ghost and vt > 0:
                        await message_utils.safe_send(message.author,
                                                      "Voudon is in play. Only the Voudon and dead may vote. Consider killing this player before prevoting yes.")
                        return

                    await vote.preset_vote(person, vt, operator=message.author)
                    if (banshee_override):
                        await message_utils.safe_send(message.author, "Successfully preset to {}!".format(vt))
                    else:
                        await message_utils.safe_send(message.author, "Successfully preset to {}!".format(argument))
                    if global_vars.game is not game.NULL_GAME:
                        game_utils.backup("current_game.pckl")

                    # Prompt for hand status (Storyteller context)
                    try:
                        hand_status_prompt_st = await message_utils.safe_send(message.author,
                                                                              f"Hand up or down for {person.display_name}? (up/down/cancel)")
                        hand_status_choice_st = await bot_client.client.wait_for(
                            "message",
                            check=(lambda x: x.author == message.author and x.channel == hand_status_prompt_st.channel),
                            timeout=200,
                        )
                        choice_content_st = hand_status_choice_st.content.lower()
                        if choice_content_st == "up":
                            person.hand_raised = True
                            await message_utils.safe_send(message.author, f"{person.display_name}'s hand is now up.")
                        elif choice_content_st == "down":
                            person.hand_raised = False
                            await message_utils.safe_send(message.author, f"{person.display_name}'s hand is now down.")
                        elif choice_content_st == "cancel":
                            await message_utils.safe_send(message.author, "Hand status change cancelled.")
                        else:
                            await message_utils.safe_send(message.author, "Invalid choice. Hand status not changed.")

                        if choice_content_st in ["up", "down"]:
                            await global_vars.game.update_seating_order_message()
                            if global_vars.game is not game.NULL_GAME:
                                game_utils.backup("current_game.pckl")

                    except asyncio.TimeoutError:
                        await message_utils.safe_send(message.author, "Timed out. Hand status not changed.")
                    except Exception as e:
                        bot_client.logger.error(f"Error during hand status prompt for ST in presetvote: {e}")
                    return

                the_player = player_utils.get_player(message.author)
                player_banshee_ability = character_utils.the_ability(the_player.character, model.characters.Banshee)
                banshee_override = player_banshee_ability and player_banshee_ability.is_screaming

                if argument in ["0", "1", "2"]:
                    if not banshee_override:
                        await message_utils.safe_send(message.author,
                                                      "is not a valid vote. Use 'yes', 'y', 'no', or 'n'.".format(
                                                          argument))
                        return
                    vt = int(argument)
                else:
                    vt = int(argument == "yes" or argument == "y")

                if voudon_in_play and the_player != voudon_in_play and not the_player.is_ghost and vt > 0:
                    await message_utils.safe_send(message.author,
                                                  "Voudon is in play. Only the Voudon and dead may vote. Wait to see if you die before voting yes.")
                    return

                await vote.preset_vote(the_player, vt)
                await message_utils.safe_send(message.author,
                                              "Successfully preset! For more nuanced presets, contact the storytellers.")
                if global_vars.game is not game.NULL_GAME:
                    game_utils.backup("current_game.pckl")

                # Prompt for hand status
                try:
                    hand_status_prompt = await message_utils.safe_send(message.author,
                                                                       "Hand up or down? (up/down/cancel)")
                    hand_status_choice = await bot_client.client.wait_for(
                        "message",
                        check=(lambda x: x.author == message.author and x.channel == hand_status_prompt.channel),
                        timeout=200,  # 200 seconds to respond
                    )
                    choice_content = hand_status_choice.content.lower()
                    if choice_content == "up":
                        the_player.hand_raised = True
                        await message_utils.safe_send(message.author, "Your hand is now up.")
                    elif choice_content == "down":
                        the_player.hand_raised = False
                        await message_utils.safe_send(message.author, "Your hand is now down.")
                    elif choice_content == "cancel":
                        await message_utils.safe_send(message.author, "Hand status change cancelled.")
                    else:
                        await message_utils.safe_send(message.author, "Invalid choice. Hand status not changed.")

                    if choice_content in ["up", "down"]:
                        await global_vars.game.update_seating_order_message()
                        if global_vars.game is not game.NULL_GAME:
                            game_utils.backup("current_game.pckl")

                except asyncio.TimeoutError:
                    await message_utils.safe_send(message.author, "Timed out. Hand status not changed.")
                except Exception as e:
                    bot_client.logger.error(f"Error during hand status prompt after presetvote: {e}")
                return

            # Cancels a preset vote
            elif command == "cancelpreset" or command == "cancelprevote":

                if global_vars.game is game.NULL_GAME:
                    await message_utils.safe_send(message.author, "There's no game right now.")
                    return

                if global_vars.game.isDay == False:
                    await message_utils.safe_send(message.author, "It's not day right now.")
                    return

                if global_vars.game.days[-1].votes == [] or global_vars.game.days[-1].votes[-1].done == True:
                    await message_utils.safe_send(message.author, "There's no vote right now.")
                    return

                vote = global_vars.game.days[-1].votes[-1]

                if global_vars.gamemaster_role in global_vars.server.get_member(message.author.id).roles:
                    msg = await message_utils.safe_send(message.author, "Whose vote do you want to cancel?")
                    try:
                        reply = await bot_client.client.wait_for(
                            "message",
                            check=(lambda x: x.author == message.author and x.channel == msg.channel),
                            timeout=200,
                        )

                    except asyncio.TimeoutError:
                        await message_utils.safe_send(message.author, "Timed out.")
                        return

                    if reply.content.lower() == "cancel":
                        await message_utils.safe_send(message.author, "Cancelling preset cancelled!")
                        return

                    reply = reply.content.lower()

                    person = await player_utils.select_player(
                        message.author, reply, global_vars.game.seatingOrder
                    )
                    if person is None:
                        return

                    await vote.cancel_preset(person)
                    await message_utils.safe_send(message.author, "Successfully canceled!")
                    if global_vars.game is not game.NULL_GAME:
                        game_utils.backup("current_game.pckl")

                    # Prompt for hand status (Storyteller context)
                    try:
                        hand_status_prompt_st = await message_utils.safe_send(message.author,
                                                                              f"Hand up or down for {person.display_name}? (up/down/cancel)")
                        hand_status_choice_st = await bot_client.client.wait_for(
                            "message",
                            check=(lambda x: x.author == message.author and x.channel == hand_status_prompt_st.channel),
                            timeout=200,
                        )
                        choice_content_st = hand_status_choice_st.content.lower()
                        if choice_content_st == "up":
                            person.hand_raised = True
                            await message_utils.safe_send(message.author, f"{person.display_name}'s hand is now up.")
                        elif choice_content_st == "down":
                            person.hand_raised = False
                            await message_utils.safe_send(message.author, f"{person.display_name}'s hand is now down.")
                        elif choice_content_st == "cancel":
                            await message_utils.safe_send(message.author, "Hand status change cancelled.")
                        else:
                            await message_utils.safe_send(message.author, "Invalid choice. Hand status not changed.")

                        if choice_content_st in ["up", "down"]:
                            await global_vars.game.update_seating_order_message()
                            if global_vars.game is not game.NULL_GAME:
                                game_utils.backup("current_game.pckl")

                    except asyncio.TimeoutError:
                        await message_utils.safe_send(message.author, "Timed out. Hand status not changed.")
                    except Exception as e:
                        bot_client.logger.error(f"Error during hand status prompt for ST in cancelpreset: {e}")
                    return

                the_player = player_utils.get_player(message.author)
                await vote.cancel_preset(the_player)
                await message_utils.safe_send(message.author,
                                              "Successfully canceled! For more nuanced presets, contact the storytellers.")
                if global_vars.game is not game.NULL_GAME:
                    game_utils.backup("current_game.pckl")

                # Prompt for hand status
                try:
                    hand_status_prompt = await message_utils.safe_send(message.author,
                                                                       "Hand up or down? (up/down/cancel)")
                    hand_status_choice = await bot_client.client.wait_for(
                        "message",
                        check=(lambda x: x.author == message.author and x.channel == hand_status_prompt.channel),
                        timeout=200,  # 200 seconds to respond
                    )
                    choice_content = hand_status_choice.content.lower()
                    if choice_content == "up":
                        the_player.hand_raised = True
                        await message_utils.safe_send(message.author, "Your hand is now up.")
                    elif choice_content == "down":
                        the_player.hand_raised = False
                        await message_utils.safe_send(message.author, "Your hand is now down.")
                    elif choice_content == "cancel":
                        await message_utils.safe_send(message.author, "Hand status change cancelled.")
                    else:
                        await message_utils.safe_send(message.author, "Invalid choice. Hand status not changed.")

                    if choice_content in ["up", "down"]:
                        await global_vars.game.update_seating_order_message()
                        if global_vars.game is not game.NULL_GAME:
                            game_utils.backup("current_game.pckl")

                except asyncio.TimeoutError:
                    await message_utils.safe_send(message.author, "Timed out. Hand status not changed.")
                except Exception as e:
                    bot_client.logger.error(f"Error during hand status prompt after cancelpreset: {e}")
                return

            elif command == "adjustvotes" or command == "adjustvote":
                if global_vars.game is game.NULL_GAME or global_vars.gamemaster_role not in global_vars.server.get_member(
                        message.author.id).roles:
                    await message_utils.safe_send(message.author,
                                                  "Command {} not recognized. For a list of commands, type @help.".format(
                                                      command))
                    return
                argument = argument.split(" ")
                if len(argument) != 3:
                    await message_utils.safe_send(message.author,
                                                  "adjustvotes takes three arguments: `@adjustvotes amnesiac target multiplier`. For example `@adjustvotes alfred charlie 2`")
                    return
                try:
                    multiplier = int(argument[2])
                except ValueError:
                    await message_utils.safe_send(message.author, "The third argument must be a whole number")
                    return
                amnesiac = await player_utils.select_player(message.author, argument[0], global_vars.game.seatingOrder)
                target_player = await player_utils.select_player(message.author, argument[1],
                                                                 global_vars.game.seatingOrder)
                if not amnesiac or not target_player:
                    return
                if not isinstance(amnesiac.character, model.characters.Amnesiac):
                    await message_utils.safe_send(message.author, "{} isn't an amnesiac".format(amnesiac.display_name))
                    return
                amnesiac.character.enhance_votes(target_player, multiplier)
                await message_utils.safe_send(message.author,
                                              "Amnesiac {} is currently multiplying the vote of {} by a factor of {}".format(
                                                  amnesiac.display_name, target_player.display_name, multiplier))

            # Set a default vote
            elif command == "defaultvote":

                global_settings: model.settings.GlobalSettings = model.settings.GlobalSettings.load()

                if argument == "":
                    if global_settings.get_default_vote(message.author.id):
                        global_settings.clear_default_vote(message.author.id)
                        global_settings.save()
                        await message_utils.safe_send(message.author, "Removed your default vote.")
                    else:
                        await message_utils.safe_send(message.author, "You have no default vote to remove.")
                    return

                else:
                    argument = argument.split(" ")
                    if len(argument) > 2:
                        await message_utils.safe_send(message.author,
                                                      "defaultvote takes at most two arguments: @defaultvote <vote = no> <time = 3600>")
                        return
                    elif len(argument) == 1:
                        try:
                            time = int(argument[0]) * 60
                            vt = False
                        except ValueError:
                            if argument[0] in ["yes", "y", "no", "n"]:
                                vt = argument[0] in ["yes", "y"]
                                time = 3600
                            else:
                                await message_utils.safe_send(message.author,
                                                              "{} is not a valid number of minutes or vote.".format(
                                                                  argument[0]))
                                return
                    else:
                        if argument[0] in ["yes", "y", "no", "n"]:
                            vt = argument[0] in ["yes", "y"]
                        else:
                            await message_utils.safe_send(message.author, "{} is not a valid vote.".format(argument[0]))
                            return
                        try:
                            time = int(argument[1]) * 60
                        except ValueError:
                            await message_utils.safe_send(message.author,
                                                          "{} is not a valid number of minutes.".format(argument[1]))
                            return

                    global_settings.set_default_vote(message.author.id, vt, time)
                    global_settings.save()
                    await message_utils.safe_send(message.author,
                                                  "Successfully set default {} vote at {} minutes.".format(
                                                      ["no", "yes"][vt], str(int(time / 60))))
                    return

            # Sends pm
            elif command == "pm" or command == "message":

                if global_vars.game is game.NULL_GAME:
                    await message_utils.safe_send(message.author, "There's no game right now.")
                    return

                if not global_vars.game.isDay:
                    await message_utils.safe_send(message.author, "It's not day right now.")
                    return

                if not global_vars.game.days[-1].isPms:  # Check if PMs open
                    await message_utils.safe_send(message.author, "PMs are closed.")
                    return

                if not player_utils.get_player(message.author):
                    await message_utils.safe_send(message.author, "You are not in the game. You may not send messages.")
                    return

                candidates_for_whispers = await model.game.whisper_mode.choose_whisper_candidates(global_vars.game,
                                                                                                  message.author)
                person = await player_utils.select_player(
                    # fixme: get players from everyone and then provide feedback if it is not appropriate
                    message.author, argument, global_vars.game.seatingOrder + global_vars.game.storytellers
                )
                if person is None:
                    return

                if person not in candidates_for_whispers:
                    await message_utils.safe_send(message.author, "You cannot whisper to this player at this time.")
                    return

                message_text = "Messaging {}. What would you like to send?".format(
                    person.display_name
                )
                reply = await message_utils.safe_send(message.author, message_text)

                # Process reply
                try:
                    intendedMessage = await bot_client.client.wait_for(
                        "message",
                        check=(lambda x: x.author == message.author and x.channel == reply.channel),
                        timeout=200,
                    )

                # Timeout
                except asyncio.TimeoutError:
                    await message_utils.safe_send(message.author, "Message timed out!")
                    return

                # Cancel
                if intendedMessage.content.lower() == "cancel":
                    await message_utils.safe_send(message.author, "Message canceled!")
                    return

                await person.message(
                    player_utils.get_player(message.author),
                    intendedMessage.content,
                    message.jump_url,
                )

                await player_utils.make_active(message.author)
                if global_vars.game is not game.NULL_GAME:
                    game_utils.backup("current_game.pckl")
                return

            # Message history
            elif command == "history":
                if global_vars.game is game.NULL_GAME:
                    await message_utils.safe_send(message.author, "There's no game right now.")
                    return

                author_roles = global_vars.server.get_member(message.author.id).roles
                if global_vars.gamemaster_role in author_roles or global_vars.observer_role in author_roles:

                    argument = argument.split(" ")
                    if len(argument) > 2:
                        await message_utils.safe_send(message.author,
                                                      "There must be exactly one or two comma-separated inputs.")
                        return

                    if len(argument) == 1:
                        person = await player_utils.select_player(
                            message.author, argument[0], global_vars.game.seatingOrder + global_vars.game.storytellers
                        )
                        if person is None:
                            return

                        message_text = (
                            "**History for {} (Times in UTC):**\n\n**Day 1:**".format(
                                person.display_name
                            )
                        )
                        day = 1
                        for msg in person.message_history:
                            if len(message_text) > 1500:
                                await message_utils.safe_send(message.author, message_text)
                                message_text = ""
                            while msg["day"] != day:
                                await message_utils.safe_send(message.author, message_text)
                                day += 1
                                message_text = "**Day {}:**".format(str(day))
                            message_text += (
                                "\nFrom: {} | To: {} | Time: {}\n**{}**".format(
                                    msg["from_player"].display_name,
                                    msg["to_player"].display_name,
                                    msg["time"].strftime("%m/%d, %H:%M:%S"),
                                    msg["content"],
                                )
                            )

                        await message_utils.safe_send(message.author, message_text)
                        return

                    person1 = await player_utils.select_player(
                        message.author, argument[0], global_vars.game.seatingOrder + global_vars.game.storytellers
                    )
                    if person1 is None:
                        return

                    person2 = await player_utils.select_player(
                        message.author, argument[1], global_vars.game.seatingOrder + global_vars.game.storytellers
                    )
                    if person2 is None:
                        return

                    message_text = "**History between {} and {} (Times in UTC):**\n\n**Day 1:**".format(
                        person1.display_name, person2.display_name
                    )
                    day = 1
                    for msg in person1.message_history:
                        if not (
                            (msg["from_player"] == person1 and msg["to_player"] == person2)
                            or (msg["to_player"] == person1 and msg["from_player"] == person2)
                        ):
                            continue
                        if len(message_text) > 1500:
                            await message_utils.safe_send(message.author, message_text)
                            message_text = ""
                        while msg["day"] != day:
                            if message_text != "":
                                await message_utils.safe_send(message.author, message_text)
                            day += 1
                            message_text = "**Day {}:**".format(str(day))
                        message_text += "\nFrom: {} | To: {} | Time: {}\n**{}**".format(
                            msg["from_player"].display_name,
                            msg["to_player"].display_name,
                            msg["time"].strftime("%m/%d, %H:%M:%S"),
                            msg["content"],
                        )

                    await message_utils.safe_send(message.author, message_text)
                    return

                if not player_utils.get_player(message.author):
                    await message_utils.safe_send(message.author,
                                                  "You are not in the game. You have no message history.")
                    return

                person = await player_utils.select_player(
                    message.author, argument, global_vars.game.seatingOrder + global_vars.game.storytellers
                )
                if person is None:
                    return

                message_text = (
                    "**History with {} (Times in UTC):**\n\n**Day 1:**".format(
                        person.display_name
                    )
                )
                day = 1
                for msg in player_utils.get_player(message.author).message_history:
                    if not msg["from_player"] == person and not msg["to_player"] == person:
                        continue
                    if len(message_text) > 1500:
                        await message_utils.safe_send(message.author, message_text)
                        message_text = ""
                    while msg["day"] != day:
                        if message_text != "":
                            await message_utils.safe_send(message.author, message_text)
                        day += 1
                        message_text = "\n\n**Day {}:**".format(str(day))
                    message_text += "\nFrom: {} | To: {} | Time: {}\n**{}**".format(
                        msg["from_player"].display_name,
                        msg["to_player"].display_name,
                        msg["time"].strftime("%m/%d, %H:%M:%S"),
                        msg["content"],
                    )

                await message_utils.safe_send(message.author, message_text)
                return

            # Message search
            elif command == "search":
                if global_vars.game is game.NULL_GAME:
                    await message_utils.safe_send(message.author, "There's no game right now.")
                    return

                author_roles = global_vars.server.get_member(message.author.id).roles
                if global_vars.gamemaster_role in author_roles or global_vars.observer_role in author_roles:

                    history = []
                    people = []
                    for person in global_vars.game.seatingOrder:
                        for msg in person.message_history:
                            if not msg["from_player"] in people and not msg["to_player"] in people:
                                history.append(msg)
                        people.append(person)

                    history = sorted(history, key=lambda i: i["time"])

                    message_text = "**Messages mentioning {} (Times in UTC):**\n\n**Day 1:**".format(
                        argument
                    )
                    day = 1
                    for msg in history:
                        if not (argument.lower() in msg["content"].lower()):
                            continue
                        while msg["day"] != day:
                            await message_utils.safe_send(message.author, message_text)
                            day += 1
                            message_text = "**Day {}:**".format(str(day))
                        message_text += "\nFrom: {} | To: {} | Time: {}\n**{}**".format(
                            msg["from_player"].display_name,
                            msg["to_player"].display_name,
                            msg["time"].strftime("%m/%d, %H:%M:%S"),
                            msg["content"],
                        )

                    await message_utils.safe_send(message.author, message_text)
                    return

                if not player_utils.get_player(message.author):
                    await message_utils.safe_send(message.author,
                                                  "You are not in the game. You have no message history.")
                    return

                message_text = (
                    "**Messages mentioning {} (Times in UTC):**\n\n**Day 1:**".format(
                        argument
                    )
                )
                day = 1
                for msg in player_utils.get_player(message.author).message_history:
                    if not (argument.lower() in msg["content"].lower()):
                        continue
                    while msg["day"] != day:
                        await message_utils.safe_send(message.author, message_text)
                        day += 1
                        message_text = "**Day {}:**".format(str(day))
                    message_text += "\nFrom: {} | To: {} | Time: {}\n**{}**".format(
                        msg["from_player"].display_name,
                        msg["to_player"].display_name,
                        msg["time"].strftime("%m/%d, %H:%M:%S"),
                        msg["content"],
                    )
                await message_utils.safe_send(message.author, message_text)
                return

            # Hand up
            elif command == "handup" or command == "handdown":
                player = player_utils.get_player(message.author)
                if not player:
                    await message_utils.safe_send(message.author, "You are not a player in the game.")
                    return

                if global_vars.game is game.NULL_GAME:
                    await message_utils.safe_send(message.author, "There's no game right now.")
                    return

                if not global_vars.game.isDay:
                    await message_utils.safe_send(message.author, "It's not day right now.")
                    return

                if not global_vars.game.days[-1].votes or global_vars.game.days[-1].votes[-1].done:
                    await message_utils.safe_send(message.author,
                                                  "You can only raise or lower your hand during an active vote.")
                    return

                if player.hand_locked_for_vote:
                    await message_utils.safe_send(message.author,
                                    "Your hand is currently locked by your vote and cannot be changed for this nomination.")
                    return

                if command == "handdown":
                    player.hand_raised = False
                    await message_utils.safe_send(message.author, "Your hand is lowered.")
                    game_utils.backup("current_game.pckl")  # Backup for hand_raised change
                    await global_vars.game.update_seating_order_message()

                    active_vote = None
                    if global_vars.game.days[-1].votes and not global_vars.game.days[-1].votes[-1].done:
                        active_vote = global_vars.game.days[-1].votes[-1]

                    if active_vote:
                        try:
                            prevote_prompt_msg = await message_utils.safe_send(message.author,
                                                                               "Preset vote to YES, NO, or CANCEL existing prevote? (yes/no/cancel)")
                            prevote_choice_msg = await bot_client.client.wait_for(
                                "message",
                                check=(lambda x: x.author == message.author and x.channel == prevote_prompt_msg.channel),
                                timeout=200,
                            )
                            prevote_choice = prevote_choice_msg.content.lower()

                            if prevote_choice in ["yes", "y"]:
                                vt = 1  # Default to 'yes'
                                banshee_ability = character_utils.the_ability(player.character,
                                                                              model.characters.Banshee)
                                if banshee_ability and banshee_ability.is_screaming:
                                    vt = 2
                                await active_vote.preset_vote(player, vt)
                                await message_utils.safe_send(message.author, "Your vote has been preset to YES.")
                                if global_vars.game is not game.NULL_GAME:
                                    game_utils.backup("current_game.pckl")
                            elif prevote_choice in ["no", "n"]:
                                await active_vote.preset_vote(player, 0)
                                await message_utils.safe_send(message.author, "Your vote has been preset to NO.")
                                if global_vars.game is not game.NULL_GAME:
                                    game_utils.backup("current_game.pckl")
                            elif prevote_choice == "cancel":
                                await active_vote.cancel_preset(player)
                                await message_utils.safe_send(message.author, "Your preset vote has been cancelled.")
                                if global_vars.game is not game.NULL_GAME:
                                    game_utils.backup("current_game.pckl")
                            else:
                                await message_utils.safe_send(message.author,
                                                              "Invalid prevote choice. Prevote not changed.")
                        except asyncio.TimeoutError:
                            await message_utils.safe_send(message.author, "Timed out. Prevote not changed.")
                        except Exception as e:
                            bot_client.logger.error(f"Error during prevote prompt after handdown: {e}")
                    return

                # command == "handup"
                active_vote = None
                if global_vars.game.days[-1].votes and not global_vars.game.days[-1].votes[-1].done:
                    active_vote = global_vars.game.days[-1].votes[-1]

                # Removed the check for preset_vote_value == 0 here

                player.hand_raised = True
                await message_utils.safe_send(message.author, "Your hand is raised.")  # Initial confirmation
                game_utils.backup("current_game.pckl")  # Backup for hand_raised change
                await global_vars.game.update_seating_order_message()

                if active_vote:
                    try:
                        prevote_prompt_msg = await message_utils.safe_send(message.author,
                                                                           "Preset vote to YES, NO, or CANCEL existing prevote? (yes/no/cancel)")
                        prevote_choice_msg = await bot_client.client.wait_for(
                            "message",
                            check=(lambda x: x.author == message.author and x.channel == prevote_prompt_msg.channel),
                            timeout=200,
                        )
                        prevote_choice = prevote_choice_msg.content.lower()

                        if prevote_choice in ["yes", "y"]:
                            vt = 1  # Default to 'yes'
                            banshee_ability = character_utils.the_ability(player.character, model.characters.Banshee)
                            if banshee_ability and banshee_ability.is_screaming:
                                vt = 2 # Banshee scream with hand up is a 'yes' vote of 2
                            await active_vote.preset_vote(player, vt)
                            await message_utils.safe_send(message.author, "Your vote has been preset to YES.")
                            if global_vars.game is not game.NULL_GAME:
                                game_utils.backup("current_game.pckl")
                        elif prevote_choice in ["no", "n"]:
                            await active_vote.preset_vote(player, 0)
                            await message_utils.safe_send(message.author, "Your vote has been preset to NO.")
                            if global_vars.game is not game.NULL_GAME:
                                game_utils.backup("current_game.pckl")
                        elif prevote_choice == "cancel":
                            await active_vote.cancel_preset(player)
                            await message_utils.safe_send(message.author, "Your preset vote has been cancelled.")
                            if global_vars.game is not game.NULL_GAME:
                                game_utils.backup("current_game.pckl")
                        else:
                            await message_utils.safe_send(message.author,
                                                          "Invalid prevote choice. Prevote not changed.")
                    except asyncio.TimeoutError:
                        await message_utils.safe_send(message.author, "Timed out. Prevote not changed.")
                    except Exception as e:
                        bot_client.logger.error(f"Error during prevote prompt after handup: {e}")
                return


            # Command unrecognized
            else:
                await message_utils.safe_send(message.author,
                                              "Command {} not recognized. For a list of commands, type @help.".format(
                                                  command))


async def warn_missing_player_channels(channel_to_send, players_missing_channels):
    plural = len(players_missing_channels) > 1
    chan = "channels" if plural else "a channel"
    playz = "those players" if plural else "that player"
    await message_utils.safe_send(channel_to_send,
                    f"Missing {chan} for: {', '.join([x.display_name for x in players_missing_channels])}.  Please run `@welcome` for {playz} to create {chan} for them.")


# in_play_voudon has been moved to model/characters/specific.py


async def check_and_print_if_one_or_zero_to_check_in():
    not_checked_in = [
        player
        for player in global_vars.game.seatingOrder
        if not player.has_checked_in and player.alignment != model.player.STORYTELLER_ALIGNMENT
    ]
    if len(not_checked_in) == 1:
        for memb in global_vars.gamemaster_role.members:
            await message_utils.safe_send(
                memb, f"Just waiting on {not_checked_in[0].display_name} to check in."
            )
    if len(not_checked_in) == 0:
        for memb in global_vars.gamemaster_role.members:
            await message_utils.safe_send(memb, "Everyone has checked in!")


@bot_client.client.event
async def on_message_edit(before, after):
    # Handles messages on modification
    if after.author == bot_client.client.user:
        return

    # On pin
    message_author_player = player_utils.get_player(after.author)
    if before.channel == global_vars.channel and before.pinned == False and after.pinned == True:

        # Nomination
        if "nominate " in after.content.lower():

            argument = after.content.lower()[after.content.lower().index("nominate ") + 9:]

            if global_vars.game is game.NULL_GAME:
                await message_utils.safe_send(global_vars.channel, "There's no game right now.")
                await after.unpin()
                return

            if global_vars.game.isDay == False:
                await message_utils.safe_send(global_vars.channel, "It's not day right now.")
                await after.unpin()
                return

            if global_vars.game.days[-1].isNoms == False:
                await message_utils.safe_send(global_vars.channel, "Nominations aren't open right now.")
                await after.unpin()
                return

            if not message_author_player:
                await message_utils.safe_send(
                    global_vars.channel, "You aren't in the game, and so cannot nominate."
                )
                await after.unpin()
                return

            names = await player_utils.generate_possibilities(argument, global_vars.game.seatingOrder)
            traveler_called = len(names) == 1 and isinstance(names[0].character, model.characters.Traveler)

            banshee_ability_of_player = character_utils.the_ability(message_author_player.character,
                                                                    model.characters.Banshee) if message_author_player else None
            banshee_override = banshee_ability_of_player and banshee_ability_of_player.is_screaming and not banshee_ability_of_player.is_poisoned

            if message_author_player.is_ghost and not traveler_called and not message_author_player.riot_nominee and not banshee_override:
                await message_utils.safe_send(global_vars.channel, "You are dead, and so cannot nominate.")
                await after.unpin()
                return
            if (banshee_override and banshee_ability_of_player.remaining_nominations < 1) and not traveler_called:
                await message_utils.safe_send(global_vars.channel, "You have already nominated twice.")
                await after.unpin()
                return
            if global_vars.game.days[-1].riot_active and not message_author_player.riot_nominee:
                await message_utils.safe_send(global_vars.channel, "Riot is active. It is not your turn to nominate.")
                await after.unpin()
                return
            if not (message_author_player).can_nominate and not traveler_called and not banshee_override:
                await message_utils.safe_send(global_vars.channel, "You have already nominated.")
                await after.unpin()
                return

            if global_vars.game.script.is_atheist:
                storyteller_nomination = await model.game.vote.is_storyteller(argument)
                if storyteller_nomination:
                    if None in [x.nominee for x in global_vars.game.days[-1].votes]:
                        await message_utils.safe_send(
                            global_vars.channel,
                            "The storytellers have already been nominated today.",
                        )
                        await after.unpin()
                        return
                    model.game.vote.remove_banshee_nomination(banshee_ability_of_player)
                    await global_vars.game.days[-1].nomination(None, message_author_player)
                    if global_vars.game is not game.NULL_GAME:
                        game_utils.backup("current_game.pckl")
                    await after.unpin()
                    return

            if len(names) == 1:

                if not names[0].can_be_nominated:
                    await message_utils.safe_send(
                        global_vars.channel, "{} has already been nominated.".format(names[0].display_name)
                    )
                    await after.unpin()
                    return

                model.game.vote.remove_banshee_nomination(banshee_ability_of_player)

                await global_vars.game.days[-1].nomination(names[0], message_author_player)
                if global_vars.game is not game.NULL_GAME:
                    game_utils.backup("current_game.pckl")
                await after.unpin()
                return

            elif len(names) > 1:

                await message_utils.safe_send(global_vars.channel, "There are too many matching players.")
                await after.unpin()
                return

            else:

                await message_utils.safe_send(global_vars.channel, "There are no matching players.")
                await after.unpin()
                return

        # Skip
        elif "skip" in after.content.lower():

            if global_vars.game is game.NULL_GAME:
                await message_utils.safe_send(global_vars.channel, "There's no game right now.")
                await after.unpin()
                return

            if not message_author_player:
                await message_utils.safe_send(
                    global_vars.channel, "You aren't in the game, and so cannot nominate."
                )
                await after.unpin()
                return

            if not global_vars.game.isDay:
                await message_utils.safe_send(global_vars.channel, "It's not day right now.")
                await after.unpin()
                return

            (message_author_player).has_skipped = True
            if global_vars.game is not game.NULL_GAME:
                game_utils.backup("current_game.pckl")

            can_nominate = [
                player
                for player in global_vars.game.seatingOrder
                if player.can_nominate == True
                   and player.has_skipped == False
                   and player.alignment != model.player.STORYTELLER_ALIGNMENT
                   and player.is_ghost == False
            ]
            if len(can_nominate) == 1:
                for memb in global_vars.gamemaster_role.members:
                    await message_utils.safe_send(
                        memb,
                        "Just waiting on {} to nominate or skip.".format(
                            can_nominate[0].display_name
                        ),
                    )
            if len(can_nominate) == 0:
                for memb in global_vars.gamemaster_role.members:
                    await message_utils.safe_send(memb, "Everyone has nominated or skipped!")

            global_vars.game.days[-1].skipMessages.append(after.id)

            return

    # On unpin
    elif before.channel == global_vars.channel and before.pinned == True and after.pinned == False:

        # Unskip
        if "skip" in after.content.lower():
            (message_author_player).has_skipped = False
            if global_vars.game is not game.NULL_GAME:
                game_utils.backup("current_game.pckl")


# remove_banshee_nomination has been moved to model/characters/specific.py


@bot_client.client.event
async def on_member_update(before, after):
    # Handles member-level modifications
    if after == bot_client.client.user:
        return

    if global_vars.game is not game.NULL_GAME:
        player = player_utils.get_player(after)
        if player and player.display_name != after.display_name:
            player.display_name = after.display_name
            await global_vars.game.reseat(global_vars.game.seatingOrder)
            await message_utils.safe_send(after, "Your nickname has been updated.")
            game_utils.backup("current_game.pckl")

        if global_vars.gamemaster_role in after.roles and global_vars.gamemaster_role not in before.roles:
            st_player = model.player.Player(model.characters.Storyteller, model.player.STORYTELLER_ALIGNMENT, after,
                                            st_channel=None, position=None)
            global_vars.game.storytellers.append(st_player)
        elif global_vars.gamemaster_role in before.roles and global_vars.gamemaster_role not in after.roles:
            for st in global_vars.game.storytellers:
                if st.user.id == after.id:
                    global_vars.game.storytellers.remove(st)