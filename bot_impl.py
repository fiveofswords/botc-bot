from __future__ import annotations

import asyncio
import inspect
import itertools
import math
import os
from collections import OrderedDict
from typing import Optional, TypeVar, Protocol, Sequence

import dill
import discord
from discord import User, Member, TextChannel

import global_vars
from bot_client import client, logger
from config import *
from model.channels import ChannelManager
from model.characters import Character, AbilityModifier, Amnesiac, DayStartModifier, Minion, Demon, Outsider, Townsfolk, \
    DayEndModifier, Voudon, NomsCalledModifier, NominationModifier, SeatingOrderModifier, Traveler, \
    VoteBeginningModifier, VoteModifier
from model.characters import Storyteller, the_ability, Banshee
from model.player import Player, STORYTELLER_ALIGNMENT
from model.settings import GlobalSettings, GameSettings
from time_utils import parse_deadline
from utils.message_utils import safe_send
from utils.player_utils import check_and_print_if_one_or_zero_to_check_in


class WhisperMode:
    ALL = 'all'
    NEIGHBORS = 'neighbors'
    STORYTELLERS = 'storytellers'


### Classes
class Game:
    def __init__(self, seatingOrder, seatingOrderMessage, script, skip_storytellers=False):
        self.days = []
        self.isDay = False
        self.script = script
        self.seatingOrder = seatingOrder
        self.whisper_mode = WhisperMode.ALL
        self.seatingOrderMessage = seatingOrderMessage
        self.storytellers = [
            Player(Storyteller, STORYTELLER_ALIGNMENT, person, st_channel=None, position=None)
            for person in global_vars.gamemaster_role.members
        ] if not skip_storytellers else []
        self.show_tally = False
        self.has_automated_life_and_death = False

    async def end(self, winner):
        # Ends the game

        # remove roles
        for person in self.seatingOrder:
            await person.wipe_roles()

        # unpin messages
        for msg in await global_vars.channel.pins():
            if msg.created_at >= self.seatingOrderMessage.created_at:
                await msg.unpin()

        if global_vars.whisper_channel:
            for msg in await global_vars.whisper_channel.pins():
                await msg.unpin()

        # announcement
        winner = winner.lower()
        await safe_send(
            global_vars.channel,
            f"{global_vars.player_role.mention}, {'The game is over.' if winner == 'tie' else f'{winner} has won.'} Good game!",
        )

        """
        # save backup
        i = 0
        while True:
            i += 1
            if not os.path.isfile('game_{}.pckl'.format(str(i))):
                break
        backup('game_{}.pckl'.format(str(i)))
        """

        # delete old backup
        remove_backup("current_game.pckl")

        # turn off
        global_vars.game = NULL_GAME
        await update_presence(client)

    async def reseat(self, newSeatingOrder):
        # Reseats the table

        # Seating order
        self.seatingOrder = newSeatingOrder

        # Seating order message
        messageText = "**Seating Order:**"
        for index, person in enumerate(self.seatingOrder):

            if person.is_ghost:
                if person.dead_votes <= 0:
                    messageText += "\n{}".format("~~" + person.display_name + "~~ X")
                else:
                    messageText += "\n{}".format(
                        "~~" + person.display_name + "~~ " + "O" * person.dead_votes
                    )

            else:
                messageText += "\n{}".format(person.display_name)

            if isinstance(person.character, SeatingOrderModifier):
                messageText += person.character.seating_order_message(self.seatingOrder)

            person.position = index

        await self.seatingOrderMessage.edit(content=messageText)
        #  fixme: reorder_channels is doing more work than needed. until that is fixed, don't reorder on reseat.
        # await reorder_channels([x.st_channel for x in self.seatingOrder])

    async def add_traveler(self, person):
        self.seatingOrder.insert(person.position, person)
        await person.user.add_roles(global_vars.player_role, global_vars.traveler_role)
        await self.reseat(self.seatingOrder)
        await safe_send(
            global_vars.channel,
            "{} has joined the town as the {}.".format(
                person.display_name, person.character.role_name
            ),
        )

    async def remove_traveler(self, person):
        self.seatingOrder.remove(person)
        await person.user.remove_roles(global_vars.player_role, global_vars.traveler_role)
        await self.reseat(self.seatingOrder)
        announcement = await safe_send(
            global_vars.channel, "{} has left the town.".format(person.display_name)
        )
        await announcement.pin()

    async def start_day(self, kills=None, origin=None):
        if kills is None:
            kills = []

        for person in global_vars.game.seatingOrder:
            await person.morning()
            if isinstance(person.character, DayStartModifier):
                if not await person.character.on_day_start(origin, kills):
                    return

        deaths = [await person.kill() for person in kills]
        if deaths == [] and len(self.days) > 0:
            no_kills = await safe_send(global_vars.channel, "No one has died.")
            await no_kills.pin()
        await safe_send(
            global_vars.channel,
            "{}, wake up! Message the storytellers to set default votes for today.".format(
                global_vars.player_role.mention
            ),
        )
        self.days.append(Day())
        self.isDay = True

        if global_vars.whisper_channel:
            message = await safe_send(global_vars.whisper_channel, f"Start of day {len(self.days)}")
            await message.pin()

        await update_presence(client)


class Script:
    # Stores booleans for characters which modify the game rules from the script

    def __init__(self, scriptList):
        self.isAtheist = "atheist" in scriptList
        self.isWitch = "witch" in scriptList
        self.list = scriptList


class Day:
    # Stores information about a specific day

    def __init__(self):
        self.isExecutionToday = False
        self.isNoms = False
        self.isPms = True
        self.votes = []
        self.voteEndMessages = []
        self.deadlineMessages = []
        self.skipMessages = []
        self.aboutToDie = None
        self.riot_active = False
        self.st_riot_kill_override = False

    async def open_pms(self):
        # Opens PMs
        self.isPms = True
        for memb in global_vars.gamemaster_role.members:
            await safe_send(memb, "PMs are now open.")
        await update_presence(client)

    async def open_noms(self):
        # Opens nominations
        self.isNoms = True
        if len(self.votes) == 0:
            for person in global_vars.game.seatingOrder:
                if isinstance(person.character, NomsCalledModifier):
                    person.character.on_noms_called()
        for memb in global_vars.gamemaster_role.members:
            await safe_send(memb, "Nominations are now open.")
        await update_presence(client)

    async def close_pms(self):
        # Closes PMs
        self.isPms = False
        for memb in global_vars.gamemaster_role.members:
            await safe_send(memb, "PMs are now closed.")
        await update_presence(client)

    async def close_noms(self):
        # Closes nominations
        self.isNoms = False
        for memb in global_vars.gamemaster_role.members:
            await safe_send(memb, "Nominations are now closed.")
        await update_presence(client)

    async def nomination(self, nominee, nominator):
        global_vars.game.whisper_mode = WhisperMode.NEIGHBORS
        await self.close_noms()
        # todo: if organ grinder ability is active, then this first message should not be output.
        if not nominee:
            self.votes.append(Vote(nominee, nominator))
            if self.aboutToDie is not None:
                announcement = await safe_send(
                    global_vars.channel,
                    "{}, the storytellers have been nominated by {}. {} to tie, {} to execute.".format(
                        global_vars.player_role.mention,
                        nominator.display_name if nominator else "the storytellers",
                        str(
                            int(
                                math.ceil(
                                    max(
                                        self.aboutToDie[1].votes,
                                        self.votes[-1].majority,
                                    )
                                )
                            )
                        ),
                        str(int(math.ceil(self.aboutToDie[1].votes + 1))),
                    ),
                )
            else:
                announcement = await safe_send(
                    global_vars.channel,
                    "{}, the storytellers have been nominated by {}. {} to execute.".format(
                        global_vars.player_role.mention,
                        nominator.display_name if nominator else "the storytellers",
                        str(int(math.ceil(self.votes[-1].majority))),
                    ),
                )
            await announcement.pin()
            if nominator and nominee and not isinstance(nominee.character, Traveler):
                nominator.can_nominate = False
            proceed = True
            # FIXME:there might be a case where a player earlier in the seating order makes the nomination not proceed
            #  but one later in the seating order may be relevant. Short circuit here stops two Riot messages, e.g.
            #  There may need to be some rework based on NominationModifier priority
            for person in global_vars.game.seatingOrder:
                if isinstance(person.character, NominationModifier) and proceed:
                    proceed = await person.character.on_nomination(
                        nominee, nominator, proceed
                    )
            if not proceed:
                # do not proceed with collecting votes
                return
        elif isinstance(nominee.character, Traveler):
            nominee.can_be_nominated = False
            self.votes.append(TravelerVote(nominee, nominator))
            announcement = await safe_send(
                global_vars.channel,
                "{}, {} has called for {}'s exile. {} to exile.".format(
                    global_vars.player_role.mention,
                    nominator.display_name if nominator else "The storytellers",
                    nominee.user.mention,
                    str(int(math.ceil(self.votes[-1].majority))),
                ),
            )
            await announcement.pin()
        else:
            nominee.can_be_nominated = False
            self.votes.append(Vote(nominee, nominator))
            # FIXME:there might be a case where a player earlier in the seating order makes the nomination not proceed
            #  but one later in the seating order may be relevant. Short circuit here stops two Riot messages, e.g.
            #  There may need to be some rework based on NominationModifier priority
            proceed = True
            for person in global_vars.game.seatingOrder:
                if isinstance(person.character, NominationModifier) and proceed:
                    proceed = await person.character.on_nomination(
                        nominee, nominator, proceed
                    )
            if not proceed:
                # do not proceed with collecting votes
                return
            if self.aboutToDie is not None:
                announcement = await safe_send(
                    global_vars.channel,
                    "{}, {} has been nominated by {}. {} to tie, {} to execute.".format(
                        global_vars.player_role.mention,
                        nominee.user.mention
                        if not nominee.user in global_vars.gamemaster_role.members
                        else "the storytellers",
                        nominator.display_name if nominator else "the storytellers",
                        str(
                            int(
                                math.ceil(
                                    max(
                                        self.aboutToDie[1].votes,
                                        self.votes[-1].majority,
                                    )
                                )
                            )
                        ),
                        str(int(math.ceil(self.aboutToDie[1].votes + 1))),
                    ),
                )
            else:
                announcement = await safe_send(
                    global_vars.channel,
                    "{}, {} has been nominated by {}. {} to execute.".format(
                        global_vars.player_role.mention,
                        nominee.user.mention
                        if not nominee.user in global_vars.gamemaster_role.members
                        else "the storytellers",
                        nominator.display_name if nominator else "the storytellers",
                        str(int(math.ceil(self.votes[-1].majority))),
                    ),
                )
            await announcement.pin()
            if nominator:
                nominator.can_nominate = False
            proceed = True
            # FIXME:there might be a case where a player earlier in the seating order makes the nomination not proceed
            #  but one later in the seating order may be relevant. Short circuit here stops two Riot messages, e.g.
            #  There may need to be some rework based on NominationModifier priority
            for person in global_vars.game.seatingOrder:
                if isinstance(person.character, NominationModifier) and proceed:
                    proceed = await person.character.on_nomination(
                        nominee, nominator, proceed
                    )
            if not proceed:
                # do not proceed with collecting user input for this vote
                return

        if (global_vars.game.show_tally):
            message_tally = {X: 0 for X in itertools.combinations(global_vars.game.seatingOrder, 2)}

            has_had_multiple_votes = len(self.votes) > 1
            last_vote_message = None if not has_had_multiple_votes else await global_vars.channel.fetch_message(self.votes[-2].announcements[0])

            for person in global_vars.game.seatingOrder:
                for msg in person.message_history:
                    if msg["from"] == person:
                        if has_had_multiple_votes:
                            if msg["time"] >= last_vote_message.created_at:
                                if (person, msg["to"]) in message_tally:
                                    message_tally[(person, msg["to"])] += 1
                                elif (msg["to"], person) in message_tally:
                                    message_tally[(msg["to"], person)] += 1
                                else:
                                    message_tally[(person, msg["to"])] = 1
                        else:
                            if msg["day"] == len(global_vars.game.days):
                                if (person, msg["to"]) in message_tally:
                                    message_tally[(person, msg["to"])] += 1
                                elif (msg["to"], person) in message_tally:
                                    message_tally[(msg["to"], person)] += 1
                                else:
                                    message_tally[(person, msg["to"])] = 1
            sorted_tally = sorted(message_tally.items(), key=lambda x: -x[1])
            messageText = "**Message Tally:**"
            for pair in sorted_tally:
                if pair[1] > 0:
                    messageText += "\n> {person1} - {person2}: {n}".format(
                        person1=pair[0][0].display_name, person2=pair[0][1].display_name, n=pair[1]
                    )
                else:
                    messageText += "\n> All other pairs: 0"
                    break
            await safe_send(global_vars.channel, messageText)

        self.votes[-1].announcements.append(announcement.id)
        await self.votes[-1].call_next()

    async def end(self):
        # Ends the day

        for person in global_vars.game.seatingOrder:
            if isinstance(person.character, DayEndModifier):
                person.character.on_day_end()

        for msg in self.voteEndMessages:
            try:
                await (await global_vars.channel.fetch_message(msg)).unpin()
            except discord.errors.NotFound:
                print("Missing message: ", str(msg))

        for msg in self.deadlineMessages:
            try:
                await (await global_vars.channel.fetch_message(msg)).unpin()
            except discord.errors.NotFound:
                print("Missing message: ", str(msg))

        for msg in self.skipMessages:
            try:
                await (await global_vars.channel.fetch_message(msg)).unpin()
            except discord.errors.NotFound:
                print("Missing message: ", str(msg))

        global_vars.game.isDay = False
        global_vars.game.whisper_mode = WhisperMode.ALL
        self.isNoms = False
        self.isPms = False

        if not self.isExecutionToday:
            await safe_send(global_vars.channel, "No one was executed.")

        await safe_send(global_vars.channel, "{}, go to sleep!".format(global_vars.player_role.mention))

        if not global_vars.game.days[-1].riot_active:
            if (global_vars.game.show_tally):
                message_tally = {X: 0 for X in itertools.combinations(global_vars.game.seatingOrder, 2)}
                has_had_multiple_votes = len(self.votes) > 0

                last_vote_message = None if not has_had_multiple_votes else (
                    await global_vars.channel.fetch_message(self.votes[-1].announcements[0]) if self.votes and self.votes[-1].announcements else None
                )
                for person in global_vars.game.seatingOrder:
                    for msg in person.message_history:
                        if msg["from"] == person:
                            if has_had_multiple_votes:
                                if msg["time"] >= last_vote_message.created_at:
                                    if (person, msg["to"]) in message_tally:
                                        message_tally[(person, msg["to"])] += 1
                                    elif (msg["to"], person) in message_tally:
                                        message_tally[(msg["to"], person)] += 1
                                    else:
                                        message_tally[(person, msg["to"])] = 1
                            else:
                                if msg["day"] == len(global_vars.game.days):
                                    if (person, msg["to"]) in message_tally:
                                        message_tally[(person, msg["to"])] += 1
                                    elif (msg["to"], person) in message_tally:
                                        message_tally[(msg["to"], person)] += 1
                                    else:
                                        message_tally[(person, msg["to"])] = 1
                sorted_tally = sorted(message_tally.items(), key=lambda x: -x[1])
                messageText = "**Message Tally:**"
                for pair in sorted_tally:
                    if pair[1] > 0:
                        messageText += "\n> {person1} - {person2}: {n}".format(
                            person1=pair[0][0].display_name, person2=pair[0][1].display_name, n=pair[1]
                        )
                    else:
                        messageText += "\n> All other pairs: 0"
                        break
                await safe_send(global_vars.channel, messageText)

        await update_presence(client)


class Vote:
    # Stores information about a specific vote

    def __init__(self, nominee, nominator):
        self.nominee = nominee
        self.nominator = nominator
        if self.nominee is not None:
            ordered_voters = (
                    global_vars.game.seatingOrder[global_vars.game.seatingOrder.index(self.nominee) + 1:]
                    + global_vars.game.seatingOrder[: global_vars.game.seatingOrder.index(self.nominee) + 1]
            )
        else:
            ordered_voters = global_vars.game.seatingOrder
        # augment order with Banshees
        order_with_banshees = []
        for person in ordered_voters:
            order_with_banshees.append(person)
            banshee_ability = the_ability(person.character, Banshee)
            if banshee_ability and banshee_ability.is_screaming:
                order_with_banshees.append(person)

        self.order = order_with_banshees

        self.votes = 0
        self.voted = []
        self.history = []
        self.announcements = []
        self.presetVotes = {}
        self.values = {person: (0, 1) for person in self.order}
        self.majority = 0.0
        for person in self.order:
            if not person.is_ghost:
                self.majority += 0.5
        for person in global_vars.game.seatingOrder:
            if isinstance(person.character, VoteBeginningModifier):
                (
                    self.order,
                    self.values,
                    self.majority,
                ) = person.character.modify_vote_values(
                    self.order, self.values, self.majority
                )
        self.position = 0
        self.done = False

    async def call_next(self):
        # Calls for person to vote

        toCall = self.order[self.position]
        player_banshee_ability = the_ability(toCall.character, Banshee)
        player_is_active_banshee = player_banshee_ability and player_banshee_ability.is_screaming
        voudon_is_active = in_play_voudon()
        for person in global_vars.game.seatingOrder:
            if isinstance(person.character, VoteModifier):
                person.character.on_vote_call(toCall)
        if toCall.is_ghost and toCall.dead_votes < 1 and not player_is_active_banshee and not voudon_is_active:
            await self.vote(0)
            return
        if toCall.user.id in self.presetVotes:
            preset_player_vote = self.presetVotes[toCall.user.id]
            self.presetVotes[toCall.user.id] -= 1
            await self.vote(int(preset_player_vote > 0))
            return
        await safe_send(
            global_vars.channel,
            "{}, your vote on {}.".format(
                toCall.user.mention,
                self.nominee.display_name if self.nominee else "the storytellers",
            ),
        )
        global_settings: GlobalSettings = GlobalSettings.load()
        default = global_settings.get_default_vote(toCall.user.id)
        if default:
            time = default[1]
            await safe_send(toCall.user, "Will enter a {} vote in {} minutes.".format(
                ["no", "yes"][default[0]], str(int(default[1] / 60))
            ))
            for memb in global_vars.gamemaster_role.members:
                await safe_send(
                    memb,
                    "{}'s vote. Their default is {} in {} minutes.".format(
                        toCall.display_name,
                        ["no", "yes"][default[0]],
                        str(int(default[1] / 60)),
                    ),
                )
            await asyncio.sleep(time)
            if toCall == global_vars.game.days[-1].votes[-1].order[global_vars.game.days[-1].votes[-1].position]:
                await self.vote(default[0])
        else:
            for memb in global_vars.gamemaster_role.members:
                await safe_send(
                    memb, "{}'s vote. They have no default.".format(toCall.display_name)
                )

    async def vote(self, vt, operator=None):
        # Executes a vote. vt is binary -- 0 if no, 1 if yes
        # Voter
        voter = self.order[self.position]

        potential_banshee = the_ability(voter.character, Banshee)

        # see if a Voudon is in play
        voudon_in_play = in_play_voudon()
        player_is_active_banshee = potential_banshee and voter.character.is_screaming
        # Check dead votes
        if vt == 1 and voter.is_ghost and voter.dead_votes < 1 and not (player_is_active_banshee and not potential_banshee.is_poisoned) and not voudon_in_play:
            if not operator:
                await safe_send(voter.user, "You do not have any dead votes. Entering a no vote.")
                await self.vote(0)
            else:
                await safe_send(
                    operator,
                    "{} does not have any dead votes. They must vote no. If you want them to vote yes, add a dead vote first:\n```\n@givedeadvote [player]\n```".format(
                        voter.display_name
                    ),
                )
            return
        if vt == 1 and voter.is_ghost and not (player_is_active_banshee and not potential_banshee.is_poisoned) and not voudon_in_play:
            await voter.remove_dead_vote()

        # On vote character powers
        for person in global_vars.game.seatingOrder:
            if isinstance(person.character, VoteModifier):
                person.character.on_vote()

        # Vote tracking
        self.history.append(vt)
        self.votes += self.values[voter][vt]
        if vt == 1:
            self.voted.append(voter)

        # Announcement
        text = "yes" if vt == 1 else "no"
        self.announcements.append(
            (
                await safe_send(
                    global_vars.channel,
                    "{} votes {}. {} votes.".format(voter.display_name, text, str(self.votes)),
                )
            ).id
        )
        await (await global_vars.channel.fetch_message(self.announcements[-1])).pin()

        # Next vote
        self.position += 1
        if self.position == len(self.order):
            await self.end_vote()
            return
        await self.call_next()

    async def end_vote(self):
        # When the vote is over
        tie = False
        aboutToDie = global_vars.game.days[-1].aboutToDie
        if self.votes >= self.majority:
            if aboutToDie is None:
                dies = True
            elif self.votes > aboutToDie[1].votes:
                dies = True
            elif self.votes == aboutToDie[1].votes:
                dies = False
                tie = True
            else:
                dies = False
        else:
            dies = False
        for person in global_vars.game.seatingOrder:
            if isinstance(person.character, VoteModifier):
                dies, tie = person.character.on_vote_conclusion(dies, tie)
        for person in global_vars.game.seatingOrder:
            person.riot_nominee = False
        the_voters = self.voted
        # remove duplicate voters
        the_voters = list(OrderedDict.fromkeys(the_voters))
        if len(the_voters) == 0:
            text = "no one"
        elif len(the_voters) == 1:
            text = the_voters[0].display_name
        elif len(the_voters) == 2:
            text = the_voters[0].display_name + " and " + the_voters[1].display_name
        else:
            text = (", ".join([x.display_name for x in the_voters[:-1]]) + ", and " + the_voters[-1].display_name)
        if dies:
            if aboutToDie is not None and aboutToDie[0] is not None:
                msg = await global_vars.channel.fetch_message(
                    global_vars.game.days[-1].voteEndMessages[
                        global_vars.game.days[-1].votes.index(aboutToDie[1])
                    ]
                )
                await msg.edit(
                    content=msg.content[:-31] + " They are not about to be executed."
                )
            global_vars.game.days[-1].aboutToDie = (self.nominee, self)
            announcement = await safe_send(
                global_vars.channel,
                "{} votes on {} (nominated by {}): {}. They are about to be executed.".format(
                    str(self.votes),
                    self.nominee.display_name if self.nominee else "the storytellers",
                    self.nominator.display_name if self.nominator else "the storytellers",
                    text,
                ),
            )
        elif tie:
            if aboutToDie is not None:
                msg = await global_vars.channel.fetch_message(
                    global_vars.game.days[-1].voteEndMessages[
                        global_vars.game.days[-1].votes.index(aboutToDie[1])
                    ]
                )
                await msg.edit(
                    content=msg.content[:-31] + " No one is about to be executed."
                )
            global_vars.game.days[-1].aboutToDie = (None, self)
            announcement = await safe_send(
                global_vars.channel,
                "{} votes on {} (nominated by {}): {}. No one is about to be executed.".format(
                    str(self.votes),
                    self.nominee.display_name if self.nominee else "the storytellers",
                    self.nominator.display_name if self.nominator else "the storytellers",
                    text,
                ),
            )
        else:
            announcement = await safe_send(
                global_vars.channel,
                "{} votes on {} (nominated by {}): {}. They are not about to be executed.".format(
                    str(self.votes),
                    self.nominee.display_name if self.nominee else "the storytellers",
                    self.nominator.display_name if self.nominator else "the storytellers",
                    text,
                ),
            )

        await announcement.pin()
        global_vars.game.days[-1].voteEndMessages.append(announcement.id)

        for msg in self.announcements:
            try:
                await (await global_vars.channel.fetch_message(msg)).unpin()
            except discord.errors.NotFound:
                print("Missing message: ", str(msg))

        self.done = True

        await global_vars.game.days[-1].open_noms()
        await global_vars.game.days[-1].open_pms()

    async def preset_vote(self, person, vt, operator=None):
        # Check dead votes
        banshee_ability = the_ability(person.character, Banshee)
        banshee_override = banshee_ability and banshee_ability.is_screaming
        if vt > 0 and person.is_ghost and person.dead_votes < 1 and not banshee_override:
            if not operator:
                await safe_send(person.user, "You do not have any dead votes. Please vote no.")
            else:
                await safe_send(
                    operator,
                    "{} does not have any dead votes. They must vote no.".format(
                        person.display_name
                    ),
                )
            return

        self.presetVotes[person.user.id] = vt

    async def cancel_preset(self, person):
        if (person.user.id in self.presetVotes):
            del self.presetVotes[person.user.id]

    async def delete(self):
        # Undoes an unintentional nomination

        if self.nominator:
            self.nominator.can_nominate = True
        if self.nominee:
            self.nominee.can_be_nominated = True

        for msg in self.announcements:
            try:
                await (await global_vars.channel.fetch_message(msg)).unpin()
            except discord.errors.NotFound:
                pass

        self.done = True

        global_vars.game.days[-1].votes.remove(self)


class TravelerVote:
    # Stores information about a specific call for exile

    def __init__(self, nominee, nominator):
        self.nominee = nominee
        self.nominator = nominator
        self.order = (
                global_vars.game.seatingOrder[global_vars.game.seatingOrder.index(self.nominee) + 1:]
                + global_vars.game.seatingOrder[: global_vars.game.seatingOrder.index(self.nominee) + 1]
        )
        self.votes = 0
        self.voted = []
        self.history = []
        self.announcements = []
        self.presetVotes = {}
        self.values = {person: (0, 1) for person in self.order}
        self.majority = len(self.order) / 2
        self.position = 0
        self.done = False

    async def call_next(self):
        # Calls for person to vote

        toCall = self.order[self.position]
        if toCall.user.id in self.presetVotes:
            await self.vote(self.presetVotes[toCall.user.id])
            return
        await safe_send(
            global_vars.channel,
            "{}, your vote on {}.".format(
                toCall.user.mention,
                self.nominee.display_name if self.nominee else "the storytellers",
            ),
        )
        global_settings: GlobalSettings = GlobalSettings.load()
        default = global_settings.get_default_vote(toCall.user.id)
        if default:
            time = default[1]
            await safe_send(toCall.user, "Will enter a {} vote in {} minutes.".format(
                ["no", "yes"][default[0]], str(int(default[1] / 60))
            ))
            await asyncio.sleep(time)
            if toCall == global_vars.game.days[-1].votes[-1].order[global_vars.game.days[-1].votes[-1].position]:
                await self.vote(default[0])
            for memb in global_vars.gamemaster_role.members:
                await safe_send(
                    memb,
                    "{}'s vote. Their default is {} in {} minutes.".format(
                        toCall.display_name,
                        ["no", "yes"][default[0]],
                        str(int(default[1] / 60)),
                    ),
                )
        else:
            for memb in global_vars.gamemaster_role.members:
                await safe_send(
                    memb, "{}'s vote. They have no default.".format(toCall.display_name)
                )

    async def vote(self, vt, operator=None):
        # Executes a vote. vt is binary -- 0 if no, 1 if yes

        # Voter
        voter = self.order[self.position]

        # Vote tracking
        self.history.append(vt)
        self.votes += self.values[voter][vt]
        if vt == 1:
            self.voted.append(voter)

        # Announcement
        text = "yes" if vt == 1 else "no"
        self.announcements.append(
            (
                await safe_send(
                    global_vars.channel,
                    "{} votes {}. {} votes.".format(voter.display_name, text, str(self.votes)),
                )
            ).id
        )
        await (await global_vars.channel.fetch_message(self.announcements[-1])).pin()

        # Next vote
        self.position += 1
        if self.position == len(self.order):
            await self.end_vote()
            return
        await self.call_next()

    async def end_vote(self):
        # When the vote is over
        if len(self.voted) == 0:
            text = "no one"
        elif len(self.voted) == 1:
            text = self.voted[0].display_name
        elif len(self.voted) == 2:
            text = self.voted[0].display_name + " and " + self.voted[1].display_name
        else:
            text = (", ".join([x.display_name for x in self.voted[:-1]]) + ", and " + self.voted[-1].display_name)
        if self.votes >= self.majority:
            announcement = await safe_send(
                global_vars.channel,
                "{} votes on {} (nominated by {}): {}.".format(
                    str(self.votes),
                    self.nominee.display_name if self.nominee else "the storytellers",
                    self.nominator.display_name if self.nominator else "the storytellers",
                    text,
                ),
            )
        else:
            announcement = await safe_send(
                global_vars.channel,
                "{} votes on {} (nominated by {}): {}. They are not exiled.".format(
                    str(self.votes),
                    self.nominee.display_name if self.nominee else "the storytellers",
                    self.nominator.display_name if self.nominator else "the storytellers",
                    text,
                ),
            )

        await announcement.pin()
        global_vars.game.days[-1].voteEndMessages.append(announcement.id)

        for msg in self.announcements:
            try:
                await (await global_vars.channel.fetch_message(msg)).unpin()
            except discord.errors.NotFound:
                print("Missing message: ", str(msg))

        self.done = True

        await global_vars.game.days[-1].open_noms()
        await global_vars.game.days[-1].open_pms()

    async def preset_vote(self, person, vt, operator=None):
        self.presetVotes[person.user.id] = vt

    async def cancel_preset(self, person):
        del self.presetVotes[person.user.id]

    async def delete(self):
        # Undoes an unintentional nomination

        if self.nominator:
            self.nominator.can_nominate = True
        if self.nominee:
            self.nominee.can_be_nominated = True

        for msg in self.announcements:
            try:
                await (await global_vars.channel.fetch_message(msg)).unpin()
            except discord.errors.NotFound:
                print("Missing message: ", str(msg))

        self.done = True

        global_vars.game.days[-1].votes.remove(self)


# Player class has been extracted to model/player.py

# Character classes have been moved to model/characters/ directory

# has_ability and the_ability functions have been moved to model/characters/base.py

# Character Helper functions

def in_play_voudon():
    """Check if a Voudon is in play.

    Returns:
        The Voudon player if one is in play and not a ghost, otherwise None
    """
    return next((x for x in global_vars.game.seatingOrder if the_ability(x.character, Voudon) and not x.is_ghost), None)


def remove_banshee_nomination(banshee_ability_of_player):
    """Remove a nomination from a Banshee.

    Args:
        banshee_ability_of_player: The Banshee ability
    """
    if banshee_ability_of_player and banshee_ability_of_player.is_screaming:
        banshee_ability_of_player.remaining_nominations -= 1

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

### Functions
def str_cleanup(str, chars):
    str = [str]
    for char in chars:
        list = []
        for x in str:
            for x in x.split(char):
                list.append(x)
        str = list
    return "".join([x.capitalize() for x in str])


def str_to_class(role: str) -> type[Character]:
    from model.characters.registry import str_to_class as registry_str_to_class
    return registry_str_to_class(role)


async def generate_possibilities(text: str, people: Sequence[T]) -> list[T]:
    # Generates possible users with name or nickname matching text

    possibilities = []
    for person in people:
        if (
            person.display_name is not None and text.lower() in person.display_name.lower()
        ) or text.lower() in person.name.lower():
            possibilities.append(person)
    return possibilities


async def choices(user: User, possibilities: list[Player], text: str) -> Optional[Player]:
    # Clarifies which user is indended when there are multiple matches

    # Generate clarification message
    if text == "":
        message_text = "Who do you mean? or use 'cancel'"
    else:
        message_text = "Who do you mean by {}? or use 'cancel'".format(text)
    for index, person in enumerate(possibilities):
        message_text += "\n({}). {}".format(
            index + 1, person.display_name if person.display_name else person.name
        )

    # Request clarifciation from user
    reply = await safe_send(user, message_text)
    try:
        choice = await client.wait_for(
            "message",
            check=(lambda x: x.author == user and x.channel == reply.channel),
            timeout=200,
        )
    except asyncio.TimeoutError:
        await safe_send(user, "Timed out.")
        return

    # Cancel
    if choice.content.lower() == "cancel":
        await safe_send(user, "Action cancelled!")
        return

    # If a is an int
    try:
        a = possibilities[int(choice.content) - 1]
        return possibilities[int(choice.content) - 1]

    # If a is a name
    except Exception:
        return await select_player(user, choice.content, possibilities)


async def select_player(user: User, text: str, possibilities: Sequence[T]) -> Optional[T]:
    # Finds a player from players matching a string

    new_possibilities = await generate_possibilities(text, possibilities)

    # If no users found
    if len(new_possibilities) == 0:
        await safe_send(user, "User {} not found. Try again!".format(text))
        return

    # If exactly one user found
    elif len(new_possibilities) == 1:
        return new_possibilities[0]

    # If too many users found
    elif len(new_possibilities) > 1:
        return await choices(user, new_possibilities, text)


async def yes_no(user, text):
    # Ask a yes or no question of a user

    reply = await safe_send(user, "{}? yes or no".format(text))
    try:
        choice = await client.wait_for(
            "message",
            check=(lambda x: x.author == user and x.channel == reply.channel),
            timeout=200,
        )
    except asyncio.TimeoutError:
        await safe_send(user, "Timed out.")
        return

    # Cancel
    if choice.content.lower() == "cancel":
        await safe_send(user, "Action cancelled!")
        return

    # Yes
    if choice.content.lower() == "yes" or choice.content.lower() == "y":
        return True

    # No
    elif choice.content.lower() == "no" or choice.content.lower() == "n":
        return False

    else:
        return await safe_send(
            user, "Your answer must be 'yes,' 'y,' 'no,' or 'n' exactly. Try again."
        )


async def reorder_channels(st_channels: list[TextChannel]):
    for st in global_vars.gamemaster_role.members:
        await safe_send(st, "Setting up channels for game...")
    await ChannelManager(client).setup_channels_in_order(st_channels)
    for st in global_vars.gamemaster_role.members:
        await safe_send(st, "Channels setup successfully!")


async def get_player(user) -> Optional[Player]:
    # returns the Player object corresponding to user
    if global_vars.game is NULL_GAME:
        return

    for person in global_vars.game.seatingOrder:
        if person.user == user:
            return person

    return None


async def active_in_st_chat(user):
    # Makes user active

    person: Player = await get_player(user)

    if not person:
        return

    # updates last active timestamp when posting in ST chat.
    person.update_last_active()

    if person.has_checked_in or global_vars.game.isDay:
        return

    person.has_checked_in = True
    await check_and_print_if_one_or_zero_to_check_in()


async def make_active(user):
    # Makes user active

    if not await get_player(user):
        return

    person = await get_player(user)

    person.update_last_active()

    if person.is_active or not global_vars.game.isDay:
        return

    person.is_active = True
    notActive = [
        player
        for player in global_vars.game.seatingOrder
        if player.is_active == False and player.alignment != STORYTELLER_ALIGNMENT
    ]
    if len(notActive) == 1:
        for memb in global_vars.gamemaster_role.members:
            await safe_send(
                memb, "Just waiting on {} to speak.".format(notActive[0].display_name)
            )
    if len(notActive) == 0:
        for memb in global_vars.gamemaster_role.members:
            await safe_send(memb, "Everyone has spoken!")


async def cannot_nominate(user):
    # Uses user's nomination

    (await get_player(user)).can_nominate = False
    can_nominate = [
        player
        for player in global_vars.game.seatingOrder
        if player.can_nominate == True
           and player.has_skipped == False
           and player.is_ghost == False
    ]
    if len(can_nominate) == 1:
        for memb in global_vars.gamemaster_role.members:
            await safe_send(
                memb,
                "Just waiting on {} to nominate or skip.".format(can_nominate[0].display_name),
            )
    if len(can_nominate) == 0:
        for memb in global_vars.gamemaster_role.members:
            await safe_send(memb, "Everyone has nominated or skipped!")


async def update_presence(client):
    # Updates Discord Presence

    if global_vars.game is NULL_GAME:
        await client.change_presence(
            status=discord.Status.dnd, activity=discord.Game(name="No ongoing game!")
        )
    elif global_vars.game.isDay == False:
        await client.change_presence(
            status=discord.Status.idle, activity=discord.Game(name="It's nighttime!")
        )
    else:
        clopen = ["Closed", "Open"]

        whisper_state = "to " + global_vars.game.whisper_mode if global_vars.game.days[-1].isPms and global_vars.game.whisper_mode != WhisperMode.ALL else clopen[
            global_vars.game.days[-1].isPms]
        status = "PMs {}, Nominations {}!".format(whisper_state, clopen[global_vars.game.days[-1].isNoms])
        await client.change_presence(
            status=discord.Status.online,
            activity=discord.Game(
                name=status
            ),
        )


def backup(fileName):
    # Backs up the game-state
    if not global_vars.game or global_vars.game is NULL_GAME:
        return

    objects = [
        x
        for x in dir(global_vars.game)
        if not x.startswith("__") and not callable(getattr(global_vars.game, x))
    ]
    with open(fileName, "wb") as file:
        dill.dump(objects, file)

    for obj in objects:
        with open(obj + "_" + fileName, "wb") as file:
            if obj == "seatingOrderMessage":
                dill.dump(getattr(global_vars.game, obj).id, file)
            else:
                dill.dump(getattr(global_vars.game, obj), file)


async def load(fileName):
    # Loads the game-state

    with open(fileName, "rb") as file:
        objects = dill.load(file)

    game = Game([], None, Script([]))
    for obj in objects:
        if not os.path.isfile(obj + "_" + fileName):
            print("Incomplete backup found.")
            return
        with open(obj + "_" + fileName, "rb") as file:
            if obj == "seatingOrderMessage":
                id = dill.load(file)
                msg = await global_vars.channel.fetch_message(id)
                setattr(game, obj, msg)
            else:
                setattr(game, obj, dill.load(file))

    return game


def remove_backup(fileName):
    os.remove(fileName)
    for obj in [
        x
        for x in dir(global_vars.game)
        if not x.startswith("__") and not callable(getattr(global_vars.game, x))
    ]:
        os.remove(obj + "_" + fileName)


def find_all(p, s):
    i = s.find(p)
    while i != -1:
        yield i
        i = s.find(p, i + 1)


async def aexec(code):
    # Make an async function with the code and `exec` it
    exec(f"async def __ex(): " + "".join(f"\n {l}" for l in code.split("\n")))

    # Get `__ex` from local variables, call it and return the result
    return await locals()["__ex"]()


async def safe_send(target: discord.abc.Messageable, msg: str):
    """Messages target, with protection from message length errors.

    Returns the first message.
    """

    try:
        # This is the only place that should send the message raw. all other message sendings should use this function
        return await target.send(msg)

    except discord.HTTPException as e:
        if e.code == 50035:

            n = len(msg) // 2
            out = await safe_send(target, msg[:n])
            await safe_send(target, msg[n:])
            return out

        else:
            raise (e)

NULL_GAME = Game(seatingOrder=[], seatingOrderMessage=0, script=[], skip_storytellers=True)

### Event Handling
@client.event
async def on_ready():
    # On startup

    global_vars.game = NULL_GAME
    global_vars.observer_role = None

    global_vars.server = client.get_guild(SERVER_ID)
    global_vars.game_category = client.get_channel(GAME_CATEGORY_ID)
    global_vars.hands_channel = client.get_channel(HANDS_CHANNEL_ID)
    global_vars.observer_channel = client.get_channel(OBSERVER_CHANNEL_ID)
    global_vars.info_channel = client.get_channel(INFO_CHANNEL_ID)
    global_vars.whisper_channel = client.get_channel(WHISPER_CHANNEL_ID)
    global_vars.channel = client.get_channel(TOWN_SQUARE_CHANNEL_ID)
    global_vars.out_of_play_category = client.get_channel(OUT_OF_PLAY_CATEGORY_ID)
    global_vars.channel_suffix = CHANNEL_SUFFIX
    logger.info(
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
        if role.name == PLAYER_ROLE:
            global_vars.player_role = role
        elif role.name == TRAVELER_ROLE:
            global_vars.traveler_role = role
        elif role.name == GHOST_ROLE:
            global_vars.ghost_role = role
        elif role.name == DEAD_VOTE_ROLE:
            global_vars.dead_vote_role = role
        elif role.name == STORYTELLER_ROLE:
            global_vars.gamemaster_role = role
        elif role.name == INACTIVE_ROLE:
            global_vars.inactive_role = role
        elif role.name == OBSERVER_ROLE:
            global_vars.observer_role = role

    if os.path.isfile("current_game.pckl"):
        global_vars.game = await load("current_game.pckl")
        print("Backup restored!")

    else:
        print("No backup found.")

    await update_presence(client)
    print("Logged in as")
    print(client.user.name)
    print(client.user.id)
    print("------")


@client.event
async def on_message(message):
    # Handles messages

    backup("current_game.pckl")

    # Don't respond to self
    if message.author == client.user:
        return

    # Update activity from town square message
    if message.channel == global_vars.channel:
        if global_vars.game is not NULL_GAME:
            await make_active(message.author)
            backup("current_game.pckl")

        # Votes
        if message.content.startswith(PREFIXES):

            if " " in message.content:
                command = message.content[1: message.content.index(" ")].lower()
                argument = message.content[message.content.index(" ") + 1:].lower()
            else:
                command = message.content[1:].lower()
                argument = ""

            if command == "vote":

                if global_vars.game is NULL_GAME:
                    await safe_send(global_vars.channel, "There's no game right now.")
                    return

                if global_vars.game.isDay == False:
                    await safe_send(global_vars.channel, "It's not day right now.")
                    return

                if global_vars.game.days[-1].votes == [] or global_vars.game.days[-1].votes[-1].done == True:
                    await safe_send(global_vars.channel, "There's no vote right now.")
                    return

                if (
                    argument != "yes"
                    and argument != "y"
                    and argument != "no"
                    and argument != "n"
                ):
                    await safe_send(
                        global_vars.channel,
                        "{} is not a valid vote. Use 'yes', 'y', 'no', or 'n'.".format(
                            argument
                        )
                    )
                    return

                vote = global_vars.game.days[-1].votes[-1]

                voting_player = (await get_player(message.author))
                if not voting_player:
                    await safe_send(global_vars.channel, "You are not a player in the game.")
                    return
                if (
                    vote.order[vote.position].user
                    != voting_player.user
                ):
                    await safe_send(global_vars.channel, "It's not your vote right now.")
                    return

                vt = int(argument == "yes" or argument == "y")
                voudon_in_play = in_play_voudon()
                if vt > 0 and voudon_in_play and voting_player != voudon_in_play and not voting_player.is_ghost:
                    await safe_send(global_vars.channel, "Voudon is in play. Only the Voudon and dead may vote.")
                    return

                await vote.vote(vt)
                if global_vars.game is not NULL_GAME:
                    backup("current_game.pckl")
                return

    # Update activity from a player's Storyteller channel
    if global_vars.game is not NULL_GAME:
        if message.channel.id == GameSettings.load().get_st_channel(message.author.id):
            await active_in_st_chat(message.author)
            backup("current_game.pckl")
            return

    # Responding to dms
    if message.guild is None:

        # Check if command
        if message.content.startswith(PREFIXES):

            # Generate command and arguments
            if " " in message.content:
                # VERY DANGEROUS TESTING COMMAND
                # if message.content[1:message.content.index(' ')].lower() == 'exec':
                # if message.author.id == 149969652141785088:
                # await aexec(message.content[message.content.index(' ') + 1:])
                # return
                command = message.content[1: message.content.index(" ")].lower()
                argument = message.content[message.content.index(" ") + 1:].lower()
            else:
                command = message.content[1:].lower()
                argument = ""

            alias = GlobalSettings.load().get_alias(message.author.id, command)
            if alias:
                command = alias

            # Opens pms
            if command == "openpms":
                if global_vars.game is NULL_GAME:
                    await safe_send(message.author, "There's no game right now.")
                    return

                if not global_vars.gamemaster_role in global_vars.server.get_member(message.author.id).roles:
                    await safe_send(message.author, "You don't have permission to open PMs.")
                    return

                if global_vars.game.isDay == False:
                    await safe_send(message.author, "It's not day right now.")
                    return

                await global_vars.game.days[-1].open_pms()
                if global_vars.game is not NULL_GAME:
                    backup("current_game.pckl")

            # Opens nominations
            elif command == "opennoms":
                if global_vars.game is NULL_GAME:
                    await safe_send(message.author, "There's no game right now.")
                    return

                if not global_vars.gamemaster_role in global_vars.server.get_member(message.author.id).roles:
                    await safe_send(message.author, "You don't have permission to open nominations.")
                    return

                if global_vars.game.isDay == False:
                    await safe_send(message.author, "It's not day right now.")
                    return

                await global_vars.game.days[-1].open_noms()
                if global_vars.game is not NULL_GAME:
                    backup("current_game.pckl")

            # Opens pms and nominations
            elif command == "open":
                if global_vars.game is NULL_GAME:
                    await safe_send(message.author, "There's no game right now.")
                    return

                if not global_vars.gamemaster_role in global_vars.server.get_member(message.author.id).roles:
                    await safe_send(message.author, "You don't have permission to open PMs and nominations.")
                    return

                if global_vars.game.isDay == False:
                    await safe_send(message.author, "It's not day right now.")
                    return

                await global_vars.game.days[-1].open_pms()
                await global_vars.game.days[-1].open_noms()
                if global_vars.game is not NULL_GAME:
                    backup("current_game.pckl")

            # Closes pms
            elif command == "closepms":
                if global_vars.game is NULL_GAME:
                    await safe_send(message.author, "There's no game right now.")
                    return

                if not global_vars.gamemaster_role in global_vars.server.get_member(message.author.id).roles:
                    await safe_send(message.author, "You don't have permission to close PMs.")
                    return

                if global_vars.game.isDay == False:
                    await safe_send(message.author, "It's not day right now.")
                    return

                await global_vars.game.days[-1].close_pms()
                if global_vars.game is not NULL_GAME:
                    backup("current_game.pckl")

            # Closes nominations
            elif command == "closenoms":
                if global_vars.game is NULL_GAME:
                    await safe_send(message.author, "There's no game right now.")
                    return

                if not global_vars.gamemaster_role in global_vars.server.get_member(message.author.id).roles:
                    await safe_send(message.author, "You don't have permission to close nominations.")
                    return

                if global_vars.game.isDay == False:
                    await safe_send(message.author, "It's not day right now.")
                    return

                await global_vars.game.days[-1].close_noms()
                if global_vars.game is not NULL_GAME:
                    backup("current_game.pckl")

            # set whisper mode
            elif command == "whispermode":
                if global_vars.game is NULL_GAME:
                    await safe_send(message.author, "There's no game right now.")
                    return

                if not global_vars.gamemaster_role in global_vars.server.get_member(message.author.id).roles:
                    await safe_send(message.author, "You don't have permission to change the whispermode.")
                    return

                new_mode = to_whisper_mode(argument)

                if (new_mode):
                    global_vars.game.whisper_mode = new_mode
                    await update_presence(client)
                    #  for each gamemaster let them know
                    for memb in global_vars.gamemaster_role.members:
                        await safe_send(memb, "{} has set whisper mode to {}.".format(message.author.display_name, global_vars.game.whisper_mode))
                else:
                    await safe_send(message.author, "Invalid whisper mode: {}\nUsage is `@whispermode [all/neighbors/storytellers]`".format(argument))
            # Closes pms and nominations
            elif command == "close":
                if global_vars.game is NULL_GAME:
                    await safe_send(message.author, "There's no game right now.")
                    return

                if not global_vars.gamemaster_role in global_vars.server.get_member(message.author.id).roles:
                    await safe_send(message.author, "You don't have permission to close PMs and nominations.")
                    return

                if global_vars.game.isDay == False:
                    await safe_send(message.author, "It's not day right now.")
                    return

                await global_vars.game.days[-1].close_pms()
                await global_vars.game.days[-1].close_noms()
                if global_vars.game is not NULL_GAME:
                    backup("current_game.pckl")
                return

            # Welcomes players
            elif command == "welcome":
                player = await select_player(message.author, argument, global_vars.server.members)
                if player is None:
                    return

                if global_vars.gamemaster_role not in global_vars.server.get_member(message.author.id).roles:
                    await safe_send(message.author, "You don't have permission to do that.")
                    return

                bot_nick = global_vars.server.get_member(client.user.id).display_name
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

                game_settings = GameSettings.load()
                st_channel = client.get_channel(game_settings.get_st_channel(player.id))
                if not st_channel:
                    st_channel = await ChannelManager(client).create_channel(game_settings, player)
                    await safe_send(message.author,
                                    f'Successfully created the channel https://discord.com/channels/{global_vars.server.id}/{st_channel.id}!')

                await safe_send(
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
                await safe_send(message.author, f'Welcomed {player.display_name} successfully!')
                return

            # Starts game
            elif command == "startgame":
                game_settings: GameSettings = GameSettings.load()

                if global_vars.game is not NULL_GAME:
                    await safe_send(message.author, "There's already an ongoing game!")
                    return

                if not global_vars.gamemaster_role in global_vars.server.get_member(message.author.id).roles:
                    await safe_send(message.author, "You don't have permission to start a game.")
                    return

                msg = await safe_send(message.author, "What is the seating order? (separate users with line breaks)")
                try:
                    order_message = await client.wait_for(
                        "message",
                        check=(lambda x: x.author == message.author and x.channel == msg.channel),
                        timeout=200,
                    )
                except asyncio.TimeoutError:
                    await safe_send(message.author, "Time out.")
                    return

                if order_message.content == "cancel":
                    await safe_send(message.author, "Game cancelled!")
                    return

                order: list[str] = order_message.content.split("\n")

                users: list[Member] = []
                for person in order:
                    name = await select_player(message.author, person, global_vars.server.members)
                    if name is None:
                        return
                    users.append(name)

                st_channels: list[TextChannel] = [client.get_channel(game_settings.get_st_channel(x.id)) for
                                                  x in users]

                players_missing_channels = [users[index] for index, channel in enumerate(st_channels) if channel is None]
                if players_missing_channels:
                    await safe_send(message.author,
                                    f"Missing channels for: {', '.join([x.display_name for x in players_missing_channels])}.  Please run `@welcome` for those players to create channels for them.")
                    return

                await safe_send(message.author, "What are the corresponding roles? (also separated with line breaks)")
                try:
                    roles_message = await client.wait_for(
                        "message",
                        check=(lambda x: x.author == message.author and x.channel == msg.channel),
                        timeout=200,
                    )
                except asyncio.TimeoutError:
                    await safe_send(message.author, "Timed out.")
                    return

                if roles_message.content == "cancel":
                    await safe_send(message.author, "Game cancelled!")
                    return

                roles: list[str] = roles_message.content.split("\n")

                if len(roles) != len(order):
                    await safe_send(message.author, "Players and roles do not match.")
                    return

                characters: list[type[Character]] = []
                for text in roles:
                    role = str_cleanup(text, [",", " ", "-", "'"])
                    try:
                        role = str_to_class(role)
                    except AttributeError:
                        await safe_send(message.author, "Role not found: {}.".format(text))
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
                    if issubclass(characters[index], Traveler):
                        await user.add_roles(global_vars.traveler_role)

                alignments: list[str] = []
                for role in characters:
                    if issubclass(role, Traveler):
                        msg = await safe_send(
                            message.author,
                            "What alignment is the {}?".format(role(None).role_name)
                        )
                        try:
                            alignment = await client.wait_for(
                                "message",
                                check=(lambda x: x.author == message.author and x.channel == msg.channel),
                                timeout=200,
                            )
                        except asyncio.TimeoutError:
                            await safe_send(message.author, "Timed out.")
                            return

                        if alignment.content == "cancel":
                            await safe_send(message.author, "Game cancelled!")
                            return

                        if (
                            alignment.content.lower() != "good"
                            and alignment.content.lower() != "evil"
                        ):
                            await safe_send(message.author, "The alignment must be 'good' or 'evil' exactly.")
                            return

                        alignments.append(alignment.content.lower())

                    elif issubclass(role, Townsfolk) or issubclass(role, Outsider):
                        alignments.append("good")

                    elif issubclass(role, Minion) or issubclass(role, Demon):
                        alignments.append("evil")

                indicies = [x for x in range(len(users))]

                seating_order: list[Player] = []
                for x in indicies:
                    seating_order.append(
                        Player(characters[x], alignments[x], users[x], st_channels[x], position=x)
                    )

                msg = await safe_send(
                    message.author,
                    "What roles are on the script? (send the text of the json file from the script creator)"
                )
                try:
                    script_message = await client.wait_for(
                        "message",
                        check=(lambda x: x.author == message.author and x.channel == msg.channel),
                        timeout=200,
                    )
                except asyncio.TimeoutError:
                    await safe_send(message.author, "Timed out.")
                    return

                if script_message.content == "cancel":
                    await safe_send(message.author, "Game cancelled!")
                    return

                script_list = ''.join(script_message.content.split())[8:-3].split('"},{"id":"')

                script = Script(script_list)

                # Setup ST channels
                tasks = [ChannelManager(client).remove_ghost(st_channel.id) for st_channel in st_channels]
                await asyncio.gather(*tasks)
                await reorder_channels(st_channels)

                await safe_send(
                    global_vars.channel,
                    "{}, welcome to Blood on the Clocktower! Go to sleep.".format(
                        global_vars.player_role.mention
                    ),
                )

                message_text = "**Seating Order:**"
                for person in seating_order:
                    message_text += "\n{}".format(person.display_name)
                    if isinstance(person.character, SeatingOrderModifier):
                        message_text += person.character.seating_order_message(
                            seating_order
                        )
                seating_order_message = await safe_send(global_vars.channel, message_text)
                await seating_order_message.pin()

                num_full_players = len([x for x in characters if not issubclass(x, Traveler)])
                distribution: tuple[int, int, int, int] = (-1, -1, -1, -1)
                if num_full_players == 5:
                    distribution = (3, 0, 1, 1)
                elif num_full_players == 6:
                    distribution = (3, 1, 1, 1)
                elif 7 <= num_full_players <= 15:
                    outsiders = int((num_full_players - 1) % 3)
                    minions = int(math.floor((num_full_players - 1) / 3) - 1)
                    distribution = (num_full_players - (outsiders + minions + 1), outsiders, minions, 1)

                msg = await safe_send(
                    global_vars.channel,
                    f"There are {num_full_players} non-Traveler players. The default distribution is {distribution[0]} Townsfolk, {distribution[1]} Outsider{'s' if distribution[1] != 1 else ''}, {distribution[2]} Minion{'s' if distribution[2] != 1 else ''}, and {distribution[3]} Demon."
                )
                await msg.pin()

                global_vars.game = Game(seating_order, seating_order_message, script)

                backup("current_game.pckl")
                await update_presence(client)

                return

            # Ends game
            elif command == "endgame":

                if global_vars.game is NULL_GAME:
                    await safe_send(message.author, "There's no game right now.")
                    return

                if not global_vars.gamemaster_role in global_vars.server.get_member(message.author.id).roles:
                    await safe_send(message.author, "You don't have permission to end the game.")
                    return

                argument = argument.lower()

                if argument != "good" and argument != "evil" and argument != "tie":
                    await safe_send(message.author, "The winner must be 'good' or 'evil' or 'tie' exactly.")
                    return

                for memb in global_vars.game.storytellers:
                    await safe_send(
                        memb.user,
                        f"{message.author.display_name} has ended the game! {'Good won!' if argument == 'good' else 'Evil won!' if argument == 'evil' else ''}  Please wait for the bot to finish.",
                    )

                await global_vars.game.end(argument.lower())
                if global_vars.game is not NULL_GAME:
                    backup("current_game.pckl")
                return

            # Starts day
            elif command == "startday":

                if global_vars.game is NULL_GAME:
                    await safe_send(message.author, "There's no game right now.")
                    return

                if not global_vars.gamemaster_role in global_vars.server.get_member(message.author.id).roles:
                    await safe_send(message.author, "You don't have permission to start the day.")
                    return

                if global_vars.game.isDay == True:
                    await safe_send(message.author, "It's already day!")
                    return

                if argument == "":
                    await global_vars.game.start_day(origin=message.author)
                    if global_vars.game is not NULL_GAME:
                        backup("current_game.pckl")
                    return

                people = [
                    await select_player(message.author, person, global_vars.game.seatingOrder)
                    for person in argument.split(" ")
                ]
                if None in people:
                    return

                await global_vars.game.start_day(kills=people, origin=message.author)
                if global_vars.game is not NULL_GAME:
                    backup("current_game.pckl")
                return

            # Ends day
            elif command == "endday":

                if global_vars.game is NULL_GAME:
                    await safe_send(message.author, "There's no game right now.")
                    return

                if not global_vars.gamemaster_role in global_vars.server.get_member(message.author.id).roles:
                    await safe_send(message.author, "You don't have permission to end the day.")
                    return

                if global_vars.game.isDay == False:
                    await safe_send(message.author, "It's already night!")
                    return

                await global_vars.game.days[-1].end()
                if global_vars.game is not NULL_GAME:
                    backup("current_game.pckl")
                return

            # Kills a player
            elif command == "kill":

                if global_vars.game is NULL_GAME:
                    await safe_send(message.author, "There's no game right now.")
                    return

                if not global_vars.gamemaster_role in global_vars.server.get_member(message.author.id).roles:
                    await safe_send(message.author, "You don't have permission to kill players.")
                    return

                person = await select_player(
                    message.author, argument, global_vars.game.seatingOrder
                )
                if person is None:
                    return

                if person.is_ghost:
                    await safe_send(message.author, "{} is already dead.".format(person.display_name))
                    return

                await person.kill(force=True)
                if global_vars.game is not NULL_GAME:
                    backup("current_game.pckl")
                return

            # Executes a player
            elif command == "execute":

                if global_vars.game is NULL_GAME:
                    await safe_send(message.author, "There's no game right now.")
                    return

                if not global_vars.gamemaster_role in global_vars.server.get_member(message.author.id).roles:
                    await safe_send(message.author, "You don't have permission to execute players.")
                    return

                person = await select_player(
                    message.author, argument, global_vars.game.seatingOrder
                )
                if person is None:
                    return

                await person.execute(message.author)
                if global_vars.game is not NULL_GAME:
                    backup("current_game.pckl")
                return

            # Exiles a traveler
            elif command == "exile":

                if global_vars.game is NULL_GAME:
                    await safe_send(message.author, "There's no game right now.")
                    return

                if not global_vars.gamemaster_role in global_vars.server.get_member(message.author.id).roles:
                    await safe_send(message.author, "You don't have permission to exile travelers.")
                    return

                person = await select_player(
                    message.author, argument, global_vars.game.seatingOrder
                )
                if person is None:
                    return

                if not isinstance(person.character, Traveler):
                    await safe_send(message.author, "{} is not a traveler.".format(person.display_name))

                await person.character.exile(person, message.author)
                if global_vars.game is not NULL_GAME:
                    backup("current_game.pckl")
                return

            # Revives a player
            elif command == "revive":

                if global_vars.game is NULL_GAME:
                    await safe_send(message.author, "There's no game right now.")
                    return

                if not global_vars.gamemaster_role in global_vars.server.get_member(message.author.id).roles:
                    await safe_send(message.author, "You don't have permission to revive players.")
                    return

                person = await select_player(
                    message.author, argument, global_vars.game.seatingOrder
                )
                if person is None:
                    return

                if not person.is_ghost:
                    await safe_send(message.author, "{} is not dead.".format(person.display_name))
                    return

                await person.revive()
                if global_vars.game is not NULL_GAME:
                    backup("current_game.pckl")
                return

            # Changes role
            elif command == "changerole":

                if global_vars.game is NULL_GAME:
                    await safe_send(message.author, "There's no game right now.")
                    return

                if not global_vars.gamemaster_role in global_vars.server.get_member(message.author.id).roles:
                    await safe_send(message.author, "You don't have permission to change roles.")
                    return

                person = await select_player(
                    message.author, argument, global_vars.game.seatingOrder
                )
                if person is None:
                    return

                msg = await safe_send(message.author, "What is the new role?")
                try:
                    role = await client.wait_for(
                        "message",
                        check=(lambda x: x.author == message.author and x.channel == msg.channel),
                        timeout=200,
                    )
                except asyncio.TimeoutError:
                    await safe_send(message.author, "Timed out.")
                    return

                role = role.content.lower()

                if role == "cancel":
                    await safe_send(message.author, "Role change cancelled!")
                    return

                role = str_cleanup(role, [",", " ", "-", "'"])
                try:
                    role = str_to_class(role)
                except AttributeError:
                    await safe_send(message.author, "Role not found: {}.".format(role))
                    return

                await person.change_character(role)
                await safe_send(message.author, "Role change successful!")
                if global_vars.game is not NULL_GAME:
                    backup("current_game.pckl")
                return

            # Changes alignment
            elif command == "changealignment":

                if global_vars.game is NULL_GAME:
                    await safe_send(message.author, "There's no game right now.")
                    return

                if not global_vars.gamemaster_role in global_vars.server.get_member(message.author.id).roles:
                    await safe_send(message.author, "You don't have permission to change alignments.")
                    return

                person = await select_player(
                    message.author, argument, global_vars.game.seatingOrder
                )
                if person is None:
                    return

                msg = await safe_send(message.author, "What is the new alignment?")
                try:
                    alignment = await client.wait_for(
                        "message",
                        check=(lambda x: x.author == message.author and x.channel == msg.channel),
                        timeout=200,
                    )
                except asyncio.TimeoutError:
                    await safe_send(message.author, "Timed out.")
                    return

                alignment = alignment.content.lower()

                if alignment == "cancel":
                    await safe_send(message.author, "Alignment change cancelled!")
                    return

                if alignment != "good" and alignment != "evil":
                    await safe_send(message.author, "The alignment must be 'good' or 'evil' exactly.")
                    return

                await person.change_alignment(alignment)
                await safe_send(message.author, "Alignment change successful!")
                if global_vars.game is not NULL_GAME:
                    backup("current_game.pckl")
                return

            # Adds an ability to an AbilityModifier character
            elif command == "changeability":
                if global_vars.game is NULL_GAME:
                    await safe_send(message.author, "There's no game right now.")
                    return

                if not global_vars.gamemaster_role in global_vars.server.get_member(message.author.id).roles:
                    await safe_send(message.author, "You don't have permission to give abilities.")
                    return

                person = await select_player(
                    message.author, argument, global_vars.game.seatingOrder
                )
                if person is None:
                    return

                if not isinstance(person.character, AbilityModifier):
                    await safe_send(message.author, "The {} cannot gain abilities.".format(person.character.role_name))
                    return

                msg = await safe_send(message.author, "What is the new ability role?")
                try:
                    role = await client.wait_for(
                        "message",
                        check=(lambda x: x.author == message.author and x.channel == msg.channel),
                        timeout=200,
                    )
                except asyncio.TimeoutError:
                    await safe_send(message.author, "Timed out.")
                    return

                role = role.content.lower()

                if role == "cancel":
                    await safe_send(message.author, "New ability cancelled!")
                    return

                role = str_cleanup(role, [",", " ", "-", "'"])
                try:
                    role = str_to_class(role)
                except AttributeError:
                    await safe_send(message.author, "Role not found: {}.".format(role))
                    return

                person.character.add_ability(role)
                await safe_send(message.author, "New ability added.")
                return

            # removes an ability from an AbilityModifier ability (useful if a nested ability is gained)
            elif command == "removeability":
                if global_vars.game is NULL_GAME:
                    await safe_send(message.author, "There's no game right now.")
                    return

                if not global_vars.gamemaster_role in global_vars.server.get_member(message.author.id).roles:
                    await safe_send(message.author, "You don't have permission to remove abilities.")
                    return

                person = await select_player(
                    message.author, argument, global_vars.game.seatingOrder
                )
                if person is None:
                    return

                if not isinstance(person.character, AbilityModifier):
                    await safe_send(message.author, "The {} cannot gain abilities to clear.".format(person.character.role_name))
                    return

                removed_ability = person.character.clear_ability()
                if (removed_ability):
                    await safe_send(message.author, "Ability removed: {}".format(removed_ability.role_name))
                else:
                    await safe_send(message.author, "No ability to remove")
                return

            # Marks as inactive
            elif command == "makeinactive":

                if global_vars.game is NULL_GAME:
                    await safe_send(message.author, "There's no game right now.")
                    return

                if not global_vars.gamemaster_role in global_vars.server.get_member(message.author.id).roles:
                    await safe_send(message.author, "You don't have permission to make players inactive.")
                    return

                person = await select_player(
                    message.author, argument, global_vars.game.seatingOrder
                )
                if person is None:
                    return

                await person.make_inactive()
                if global_vars.game is not NULL_GAME:
                    backup("current_game.pckl")
                return

            # Marks as inactive
            elif command == "undoinactive":

                if global_vars.game is NULL_GAME:
                    await safe_send(message.author, "There's no game right now.")
                    return

                if not global_vars.gamemaster_role in global_vars.server.get_member(message.author.id).roles:
                    await safe_send(message.author, "You don't have permission to make players active.")
                    return

                person = await select_player(
                    message.author, argument, global_vars.game.seatingOrder
                )
                if person is None:
                    return

                await person.undo_inactive()
                if global_vars.game is not NULL_GAME:
                    backup("current_game.pckl")
                return

            # Marks as checked in
            elif command == "checkin":

                if global_vars.game is NULL_GAME:
                    await safe_send(message.author, "There's no game right now.")
                    return

                if global_vars.gamemaster_role not in global_vars.server.get_member(message.author.id).roles:
                    await safe_send(message.author, "You don't have permission to mark a player cheacked in.")
                    return

                people = [
                    await select_player(message.author, person, global_vars.game.seatingOrder)
                    for person in argument.split(" ")
                ]
                if None in people:
                    return
                for person in people:
                    person.has_checked_in = True

                await safe_send(message.author, "Successfully marked as checked in: {}".format(", ".join([person.display_name for person in people])))
                if global_vars.game is not NULL_GAME:
                    backup("current_game.pckl")

                await check_and_print_if_one_or_zero_to_check_in()
                return

            # Marks as not checked in
            elif command == "undocheckin":

                if global_vars.game is NULL_GAME:
                    await safe_send(message.author, "There's no game right now.")
                    return

                if global_vars.gamemaster_role not in global_vars.server.get_member(message.author.id).roles:
                    await safe_send(message.author, "You don't have permission to make players active.")
                    return

                people = [
                    await select_player(message.author, person, global_vars.game.seatingOrder)
                    for person in argument.split(" ")
                ]
                if None in people:
                    return

                for person in people:
                    person.has_checked_in = False

                await safe_send(message.author, "Successfully marked as not checked in: {}".format(", ".join([person.display_name for person in people])))

                if global_vars.game is not NULL_GAME:
                    backup("current_game.pckl")

                await check_and_print_if_one_or_zero_to_check_in()
                return

            # Adds traveler
            elif command == "addtraveler" or command == "addtraveller":

                if global_vars.game is NULL_GAME:
                    await safe_send(message.author, "There's no game right now.")
                    return

                if global_vars.gamemaster_role not in global_vars.server.get_member(message.author.id).roles:
                    await safe_send(message.author, "You don't have permission to add travelers.")
                    return

                person = await select_player(message.author, argument, global_vars.server.members)
                if person is None:
                    return

                if await get_player(person) is not None:
                    await safe_send(message.author, "{} is already in the game.".format(person.display_name if person.display_name else person.name))
                    return

                st_channel = global_vars.server.get_channel(GameSettings.load().get_st_channel(person.id))

                msg = await safe_send(message.author, "What role?")
                try:
                    text = await client.wait_for(
                        "message",
                        check=(lambda x: x.author == message.author and x.channel == msg.channel),
                        timeout=200,
                    )
                except asyncio.TimeoutError:
                    await safe_send(message.author, "Timed out.")
                    return

                if text.content == "cancel":
                    await safe_send(message.author, "Traveler cancelled!")
                    return

                text = text.content

                role = str_cleanup(text, [",", " ", "-", "'"])

                try:
                    role = str_to_class(role)
                except AttributeError:
                    await safe_send(message.author, "Role not found: {}.".format(text))
                    return

                if not issubclass(role, Traveler):
                    await safe_send(message.author, "{} is not a traveler role.".format(text))
                    return

                # Determine position in order
                msg = await safe_send(message.author, "Where in the order are they? (send the player before them or a one-indexed integer)")
                try:
                    pos = await client.wait_for(
                        "message",
                        check=(lambda x: x.author == message.author and x.channel == msg.channel),
                        timeout=200,
                    )

                except asyncio.TimeoutError:
                    await safe_send(message.author, "Timed out.")
                    return

                if pos.content == "cancel":
                    await safe_send(message.author, "Traveler cancelled!")
                    return

                pos = pos.content

                try:
                    pos = int(pos) - 1
                except ValueError:
                    player = await select_player(message.author, pos, global_vars.game.seatingOrder)
                    if player is None:
                        return
                    pos = player.position + 1

                # Determine alignment
                msg = await safe_send(message.author, "What alignment are they?")
                try:
                    alignment = await client.wait_for(
                        "message",
                        check=(lambda x: x.author == message.author and x.channel == msg.channel),
                        timeout=200,
                    )

                except asyncio.TimeoutError:
                    await safe_send(message.author, "Timed out.")
                    return

                if alignment.content == "cancel":
                    await safe_send(message.author, "Traveler cancelled!")
                    return

                if (
                    alignment.content.lower() != "good"
                    and alignment.content.lower() != "evil"
                ):
                    await safe_send(message.author, "The alignment must be 'good' or 'evil' exactly.")
                    return

                await global_vars.game.add_traveler(
                    Player(role, alignment.content.lower(), person, st_channel, position=pos)
                )
                if global_vars.game is not NULL_GAME:
                    backup("current_game.pckl")
                return

            # Removes traveler
            elif command == "removetraveler" or command == "removetraveller":

                if global_vars.game is NULL_GAME:
                    await safe_send(message.author, "There's no game right now.")
                    return

                if not global_vars.gamemaster_role in global_vars.server.get_member(message.author.id).roles:
                    await safe_send(message.author, "You don't have permission to remove travelers.")
                    return

                person = await select_player(
                    message.author, argument, global_vars.game.seatingOrder
                )
                if person is None:
                    return

                await global_vars.game.remove_traveler(person)
                if global_vars.game is not NULL_GAME:
                    backup("current_game.pckl")
                return

            # Resets the seating chart
            elif command == "resetseats":
                if global_vars.game is NULL_GAME:
                    await safe_send(message.author, "There's no game right now.")

                if not global_vars.gamemaster_role in global_vars.server.get_member(message.author.id).roles:
                    await safe_send(message.author, "You don't have permission to change the seating chart.")
                    return

                await global_vars.game.reseat(global_vars.game.seatingOrder)
                return

            # Changes seating chart
            elif command == "reseat":

                if global_vars.game is NULL_GAME:
                    await safe_send(message.author, "There's no game right now.")

                if not global_vars.gamemaster_role in global_vars.server.get_member(message.author.id).roles:
                    await safe_send(message.author, "You don't have permission to change the seating chart.")
                    return

                msg = await safe_send(message.author, "What is the seating order? (separate users with line breaks)")
                try:
                    order_message = await client.wait_for(
                        "message",
                        check=(lambda x: x.author == message.author and x.channel == msg.channel),
                        timeout=200,
                    )

                except asyncio.TimeoutError:
                    await safe_send(message.author, "Timed out.")
                    return

                if order_message.content == "cancel":
                    await safe_send(message.author, "Reseating cancelled!")
                    return

                if order_message.content == "none":
                    await global_vars.game.reseat(global_vars.game.seatingOrder)

                order = [
                    await select_player(message.author, person, global_vars.game.seatingOrder)
                    for person in order_message.content.split("\n")
                ]
                if None in order:
                    return

                await global_vars.game.reseat(order)
                if global_vars.game is not NULL_GAME:
                    backup("current_game.pckl")
                return

            # Poisons
            elif command == "poison":
                if global_vars.game is NULL_GAME:
                    await safe_send(message.author, "There's no game right now.")
                    return

                if not global_vars.gamemaster_role in global_vars.server.get_member(message.author.id).roles:
                    await safe_send(message.author, "You don't have permission to poison players.")
                    return

                person = await select_player(
                    message.author, argument, global_vars.game.seatingOrder
                )
                if person is None:
                    return

                person.character.poison()

                await safe_send(message.author, "Successfully poisoned {}!".format(person.display_name))
                return

            # Unpoisons
            elif command == "unpoison":
                if global_vars.game is NULL_GAME:
                    await safe_send(message.author, "There's no game right now.")
                    return

                if not global_vars.gamemaster_role in global_vars.server.get_member(message.author.id).roles:
                    await safe_send(message.author, "You don't have permission to revive players.")
                    return

                person = await select_player(
                    message.author, argument, global_vars.game.seatingOrder
                )
                if person is None:
                    return

                person.character.unpoison()
                await safe_send(message.author, "Successfully unpoisoned {}!".format(person.display_name))
                return

            # Cancels a nomination
            elif command == "cancelnomination":
                if global_vars.game is NULL_GAME:
                    await safe_send(message.author, "There's no game right now.")
                    return

                if not global_vars.gamemaster_role in global_vars.server.get_member(message.author.id).roles:
                    await safe_send(message.author, "You don't have permission to cancel nominations.")
                    return

                if global_vars.game.isDay == False:
                    await safe_send(message.author, "It's not day right now.")
                    return

                if global_vars.game.days[-1].votes == [] or global_vars.game.days[-1].votes[-1].done == True:
                    await safe_send(message.author, "There's no vote right now.")
                    return

                if global_vars.game.days[-1].votes[-1].nominator:
                    # check for storyteller
                    global_vars.game.days[-1].votes[-1].nominator.can_nominate = True

                await global_vars.game.days[-1].votes[-1].delete()
                await global_vars.game.days[-1].open_pms()
                await global_vars.game.days[-1].open_noms()
                await safe_send(global_vars.channel, "Nomination canceled!")
                if global_vars.game is not NULL_GAME:
                    backup("current_game.pckl")
                return

            # Sets a deadline
            elif command == "setdeadline":
                if global_vars.game is NULL_GAME:
                    await safe_send(message.author, "There's no game right now.")
                    return

                if global_vars.gamemaster_role not in global_vars.server.get_member(message.author.id).roles:
                    await safe_send(message.author, "You don't have permission to set deadlines.")
                    return

                if not global_vars.game.isDay:
                    await safe_send(message.author, "It's not day right now.")
                    return

                deadline = parse_deadline(argument)

                if deadline is None:
                    await safe_send(message.author, "Unrecognized format. Please provide a deadline in the format 'HH:MM', '+[HHh][MMm]', or a Unix timestamp.")
                    return

                if len(global_vars.game.days[-1].deadlineMessages) > 0:
                    previous_deadline = global_vars.game.days[-1].deadlineMessages[-1]
                    try:
                        await (
                            await global_vars.channel.fetch_message(previous_deadline)
                        ).unpin()
                    except discord.errors.NotFound:
                        print("Missing message: ", str(previous_deadline))
                announcement = await safe_send(
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
                if global_vars.game is NULL_GAME:
                    await safe_send(message.author, "There's no game right now.")
                    return

                if not global_vars.gamemaster_role in global_vars.server.get_member(message.author.id).roles:
                    await safe_send(message.author, "You don't have permission to give dead votes.")
                    return

                person = await select_player(
                    message.author, argument, global_vars.game.seatingOrder
                )
                if person is None:
                    return

                await person.add_dead_vote()
                if global_vars.game is not NULL_GAME:
                    backup("current_game.pckl")
                return

            # Removes a dead vote
            elif command == "removedeadvote":
                if global_vars.game is NULL_GAME:
                    await safe_send(message.author, "There's no game right now.")
                    return

                if not global_vars.gamemaster_role in global_vars.server.get_member(message.author.id).roles:
                    await safe_send(message.author, "You don't have permission to remove dead votes.")
                    return

                person = await select_player(
                    message.author, argument, global_vars.game.seatingOrder
                )
                if person is None:
                    return

                await person.remove_dead_vote()
                if global_vars.game is not NULL_GAME:
                    backup("current_game.pckl")
                return

            # Sends a message tally
            elif command == "messagetally":
                if global_vars.game is NULL_GAME:
                    await safe_send(message.author, "There's no game right now.")
                    return

                if global_vars.gamemaster_role not in global_vars.server.get_member(message.author.id).roles:
                    await safe_send(message.author, "You don't have permission to report the message tally.")
                    return

                if global_vars.game.days == []:
                    await safe_send(message.author, "There have been no days.")
                    return

                try:
                    idn = int(argument)
                except ValueError:
                    await safe_send(message.author, "Invalid message ID: {}".format(argument))
                    return

                try:
                    origin_msg = await global_vars.channel.fetch_message(idn)
                except discord.errors.NotFound:
                    await safe_send(message.author, "Message not found by ID: {}".format(argument))
                    return

                message_tally = {
                    X: 0 for X in itertools.combinations(global_vars.game.seatingOrder, 2)
                }
                for person in global_vars.game.seatingOrder:
                    for msg in person.message_history:
                        if msg["from"] == person:
                            if msg["time"] >= origin_msg.created_at:
                                if (person, msg["to"]) in message_tally:
                                    message_tally[(person, msg["to"])] += 1
                                elif (msg["to"], person) in message_tally:
                                    message_tally[(msg["to"], person)] += 1
                                else:
                                    message_tally[(person, msg["to"])] = 1
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
                await safe_send(global_vars.channel, message_text)
            elif command == "whispers":
                person = None
                if global_vars.gamemaster_role in global_vars.server.get_member(message.author.id).roles:
                    argument = argument.split(" ")
                    if len(argument) != 1:
                        await safe_send(message.author, "Usage: @whispers <player>")
                        return
                    if len(argument) == 1:
                        person = await select_player(
                            message.author, argument[0], global_vars.game.seatingOrder + global_vars.game.storytellers
                        )
                else:
                    person = await get_player(message.author)
                if not person:
                    await safe_send(message.author, "You are not in the game. You have no message history.")
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
                        await safe_send(message.author, message_text)
                        counts = OrderedDict([(player, 0) for player in global_vars.game.seatingOrder])
                        day = msg["day"]
                    if msg["from"] == person:
                        if (msg["to"] in counts):
                            counts[msg["to"]] += 1
                        else:
                            if "Storytellers" in counts:
                                counts["Storytellers"] += 1
                            else:
                                counts["Storytellers"] = 1
                    else:
                        counts[msg["from"]] += 1

                message_text = "Day {}\n".format(day)
                for player, count in counts.items():
                    message_text += "{}: {}\n".format(player if player == "Storytellers" else player.display_name, count)
                await safe_send(message.author, message_text)
                return
            elif command == "enabletally":
                if global_vars.game is NULL_GAME:
                    await safe_send(message.author, "There's no game right now.")
                    return

                if not global_vars.gamemaster_role in global_vars.server.get_member(message.author.id).roles:
                    await safe_send(message.author, "You don't have permission to enable tally.")
                    return
                global_vars.game.show_tally = True
                for memb in global_vars.game.storytellers:
                    await safe_send(memb.user, "The message tally has been enabled by {}.".format(message.author.display_name))
            elif command == "disabletally":
                if global_vars.game is NULL_GAME:
                    await safe_send(message.author, "There's no game right now.")
                    return

                if not global_vars.gamemaster_role in global_vars.server.get_member(message.author.id).roles:
                    await safe_send(message.author, "You don't have permission to disable tally.")
                    return
                global_vars.game.show_tally = False
                for memb in global_vars.game.storytellers:
                    await safe_send(memb.user, "The message tally has been disabled by {}.".format(message.author.display_name))
            # Views relevant information about a player
            elif command == "info":
                if global_vars.game is NULL_GAME:
                    await safe_send(message.author, "There's no game right now.")
                    return

                if not global_vars.gamemaster_role in global_vars.server.get_member(message.author.id).roles:
                    await safe_send(message.author, "You don't have permission to view player information.")
                    return

                person = await select_player(
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
                await safe_send(message.author, "\n".join([base_info, person.character.extra_info()]))
                return
            # Views relevant information about a player
            elif command == "votehistory":
                if global_vars.game is NULL_GAME:
                    await safe_send(message.author, "There's no game right now.")
                    return

                if global_vars.gamemaster_role not in global_vars.server.get_member(message.author.id).roles:
                    await safe_send(message.author, "You don't have permission to view player information.")
                    return

                for index, day in enumerate(global_vars.game.days):
                    votes_for_day = f"Day {index + 1}\n"
                    for vote in day.votes:  # type: Vote
                        nominator_name = vote.nominator.display_name if vote.nominator else "the storytellers"
                        nominee_name = vote.nominee.display_name if vote.nominee else "the storytellers"
                        voters = ", ".join([voter.display_name for voter in vote.voted])
                        votes_for_day += f"{nominator_name} -> {nominee_name} ({vote.votes}): {voters}\n"
                    await safe_send(message.author, f"```\n{votes_for_day}\n```")
                return
            elif command == "setatheist":
                if global_vars.game is NULL_GAME:
                    await safe_send(message.author, "There's no game right now.")
                    return

                if not global_vars.gamemaster_role in global_vars.server.get_member(message.author.id).roles:
                    await safe_send(message.author, "You don't have permission to configure the game.")
                    return

                # argument is true or false
                global_vars.game.script.isAtheist = argument.lower() == "true" or argument.lower() == "t"
                #  message storytellers that atheist game is set to false
                for memb in global_vars.gamemaster_role.members:
                    await safe_send(memb, "Atheist game is set to {} by {}".format(global_vars.game.script.isAtheist, message.author.display_name))
                pass
            elif command == "automatekills":
                if global_vars.game is NULL_GAME:
                    await safe_send(message.author, "There's no game right now.")
                    return
                if not global_vars.gamemaster_role in global_vars.server.get_member(message.author.id).roles:
                    await safe_send(message.author, "You don't have permission to configure the game.")
                    return
                global_vars.game.has_automated_life_and_death = argument.lower() == "true" or argument.lower() == "t"
                for memb in global_vars.gamemaster_role.members:
                    await safe_send(memb, f"Automated life and death is set to {global_vars.game.has_automated_life_and_death} by {message.author.display_name}")

                pass
            # Views the grimoire
            elif command == "grimoire":
                if global_vars.game is NULL_GAME:
                    await safe_send(message.author, "There's no game right now.")
                    return

                if not global_vars.gamemaster_role in global_vars.server.get_member(message.author.id).roles:
                    await safe_send(message.author, "You don't have permission to view player information.")
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

                await safe_send(message.author, message_text)
                return

            # Clears history
            elif command == "clear":
                await safe_send(message.author, "{}Clearing\n{}".format("\u200B\n" * 25, "\u200B\n" * 25))
                return

            # Checks active players
            elif command == "notactive":

                if not global_vars.gamemaster_role in global_vars.server.get_member(message.author.id).roles:
                    await safe_send(message.author, "You don't have permission to view that information.")
                    return

                if global_vars.game is NULL_GAME:
                    await safe_send(message.author, "There's no game right now.")
                    return

                if global_vars.game.isDay == False:
                    await safe_send(message.author, "It's not day right now.")
                    return

                notActive = [
                    player
                    for player in global_vars.game.seatingOrder
                    if player.is_active == False and player.alignment != STORYTELLER_ALIGNMENT
                ]

                if notActive == []:
                    await safe_send(message.author, "Everyone has spoken!")
                    return

                message_text = "These players have not spoken:"
                for player in notActive:
                    message_text += "\n{}".format(player.display_name)

                await safe_send(message.author, message_text)
                return

            # Checks who can nominate
            elif command == "tocheckin":

                if global_vars.game is NULL_GAME:
                    await safe_send(message.author, "There's no game right now.")
                    return

                if not global_vars.gamemaster_role in global_vars.server.get_member(message.author.id).roles:
                    await safe_send(message.author, "You don't have permission to view that information.")
                    return

                if global_vars.game.isDay:
                    await safe_send(message.author, "It's day right now.")
                    return

                to_check_in = [
                    player
                    for player in global_vars.game.seatingOrder
                    if player.has_checked_in == False
                ]
                if not to_check_in:
                    await safe_send(message.author, "Everyone has checked in!")
                    return

                message_text = "These players have not checked in:"
                for player in to_check_in:
                    message_text += "\n{}".format(player.display_name)

                await safe_send(message.author, message_text)
                return

            # Checks who can nominate
            elif command == "cannominate":

                if global_vars.game is NULL_GAME:
                    await safe_send(message.author, "There's no game right now.")
                    return

                if global_vars.game.isDay == False:
                    await safe_send(message.author, "It's not day right now.")
                    return

                can_nominate = [
                    player
                    for player in global_vars.game.seatingOrder
                    if player.can_nominate == True
                       and player.has_skipped == False
                       and player.alignment != STORYTELLER_ALIGNMENT
                       and player.is_ghost == False
                ]
                if can_nominate == []:
                    await safe_send(message.author, "Everyone has nominated or skipped!")
                    return

                message_text = "These players have not nominated or skipped:"
                for player in can_nominate:
                    message_text += "\n{}".format(player.display_name)

                await safe_send(message.author, message_text)
                return

            # Checks who can be nominated
            elif command == "canbenominated":

                if global_vars.game is NULL_GAME:
                    await safe_send(message.author, "There's no game right now.")
                    return

                if global_vars.game.isDay == False:
                    await safe_send(message.author, "It's not day right now.")
                    return

                can_be_nominated = [
                    player
                    for player in global_vars.game.seatingOrder
                    if player.can_be_nominated == True
                ]
                if can_be_nominated == []:
                    await safe_send(message.author, "Everyone has been nominated!")
                    return

                message_text = "These players have not been nominated:"
                for player in can_be_nominated:
                    message_text += "\n{}".format(player.display_name)

                await safe_send(message.author, message_text)
                return

            # Checks when a given player was last active
            elif command == "lastactive":
                if global_vars.game is NULL_GAME:
                    await safe_send(message.author, "There's no game right now.")
                    return

                author_roles = global_vars.server.get_member(message.author.id).roles
                if global_vars.gamemaster_role not in author_roles and global_vars.observer_role not in author_roles:
                    await safe_send(message.author, "You don't have permission to view player information.")
                    return

                last_active = sorted(global_vars.game.seatingOrder, key=lambda p: p.last_active)
                message_text = "Last active time for these players:"
                for player in last_active:
                    last_active_str = str(int(player.last_active))
                    message_text += "\n{}:<t:{}:R> at <t:{}:t>".format(
                        player.display_name, last_active_str, last_active_str)

                await safe_send(message.author, message_text)
                return

            # Nominates
            elif command == "nominate":

                if global_vars.game is NULL_GAME:
                    await safe_send(message.author, "There's no game right now.")
                    return

                if global_vars.game.isDay == False:
                    await safe_send(message.author, "It's not day right now.")
                    return

                if global_vars.game.days[-1].isNoms == False:
                    await safe_send(message.author, "Nominations aren't open right now.")
                    return

                nominator_player = await get_player(message.author)
                story_teller_is_nominated = await is_storyteller(argument)
                person = await select_player(
                    message.author, argument, global_vars.game.seatingOrder
                ) if not story_teller_is_nominated else None

                traveler_called = person is not None and isinstance(person.character, Traveler)

                banshee_ability_of_player = the_ability(nominator_player.character, Banshee) if nominator_player else None
                banshee_override = banshee_ability_of_player is not None and banshee_ability_of_player.is_screaming

                if not nominator_player:
                    if not global_vars.gamemaster_role in global_vars.server.get_member(message.author.id).roles:
                        await safe_send(message.author, "You aren't in the game, and so cannot nominate.")
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
                            msg = await safe_send(st_user, "Do they die? yes or no")
                            try:
                                choice = await client.wait_for(
                                    "message",
                                    check=(lambda x: x.author == st_user and x.channel == msg.channel),
                                    timeout=200,
                                )
                            except asyncio.TimeoutError:
                                await safe_send(st_user, "Message timed out!")
                                return
                            # Cancel
                            if choice.content.lower() == "cancel":
                                await safe_send(st_user, "Action cancelled!")
                                return
                            player_dies = False
                            # Yes
                            if choice.content.lower() == "yes" or choice.content.lower() == "y":
                                player_dies = True
                            # No
                            elif choice.content.lower() == "no" or choice.content.lower() == "n":
                                player_dies = False
                            else:
                                await safe_send(
                                    st_user, "Your answer must be 'yes,' 'y,' 'no,' or 'n' exactly."
                                )
                                return
                            global_vars.game.days[-1].st_riot_kill_override = player_dies
                else:
                    if global_vars.game.days[-1].riot_active:
                        if not nominator_player.riot_nominee:
                            await safe_send(message.author, "Riot is active, you may not nominate.")
                            return
                    if nominator_player.is_ghost and not traveler_called and not nominator_player.riot_nominee and not banshee_override:
                        await safe_send(
                            message.author, "You are dead, and so cannot nominate."
                        )
                        return
                    if banshee_override and banshee_ability_of_player.remaining_nominations < 1:
                        await safe_send(message.author, "You have already nominated twice.")
                        return
                    if not nominator_player.can_nominate and not traveler_called and not banshee_override:
                        await safe_send(message.author, "You have already nominated.")
                        return

                if global_vars.game.script.isAtheist:
                    if story_teller_is_nominated:
                        if None in [x.nominee for x in global_vars.game.days[-1].votes]:
                            await safe_send(message.author, "The storytellers have already been nominated today.")
                            await message.unpin()
                            return
                        await global_vars.game.days[-1].nomination(None, nominator_player)
                        if global_vars.game is not NULL_GAME:
                            backup("current_game.pckl")
                        await message.unpin()
                        return

                if person is None:
                    return

                if global_vars.gamemaster_role in global_vars.server.get_member(message.author.id).roles:
                    await global_vars.game.days[-1].nomination(person, None)
                    if global_vars.game is not NULL_GAME:
                        backup("current_game.pckl")
                    return

                #  make sure that the nominee has not been nominated yet
                if not person.can_be_nominated:
                    await safe_send(message.author, "{} has already been nominated".format(person.display_name))
                    return

                remove_banshee_nomination(banshee_ability_of_player)

                await global_vars.game.days[-1].nomination(person, nominator_player)
                if global_vars.game is not NULL_GAME:
                    backup("current_game.pckl")
                return

            # Votes
            elif command == "vote":

                if global_vars.game is NULL_GAME:
                    await safe_send(message.author, "There's no game right now.")
                    return

                if global_vars.game.isDay == False:
                    await safe_send(message.author, "It's not day right now.")
                    return

                if global_vars.game.days[-1].votes == [] or global_vars.game.days[-1].votes[-1].done == True:
                    await safe_send(message.author, "There's no vote right now.")
                    return

                if (
                    argument != "yes"
                    and argument != "y"
                    and argument != "no"
                    and argument != "n"
                ):
                    await safe_send(message.author, "{} is not a valid vote. Use 'yes', 'y', 'no', or 'n'.".format(argument))
                    return

                voudon_in_play = in_play_voudon()

                vote = global_vars.game.days[-1].votes[-1]

                if global_vars.gamemaster_role in global_vars.server.get_member(message.author.id).roles:
                    msg = await safe_send(message.author, "Whose vote is this?")
                    try:
                        reply = await client.wait_for(
                            "message",
                            check=(lambda x: x.author == message.author and x.channel == msg.channel),
                            timeout=200,
                        )

                    except asyncio.TimeoutError:
                        await safe_send(message.author, "Timed out.")
                        return

                    if reply.content.lower() == "cancel":
                        await safe_send(message.author, "Vote cancelled!")
                        return

                    reply = reply.content.lower()

                    person = await select_player(
                        message.author, reply, global_vars.game.seatingOrder
                    )
                    if person is None:
                        return

                    if vote.order[vote.position].user != person.user:
                        await safe_send(message.author, "It's not their vote right now. Do you mean @presetvote?")
                        return

                    vt = int(argument == "yes" or argument == "y")

                    if voudon_in_play and voudon_in_play != person and not person.is_ghost and vt > 0:
                        await safe_send(message.author, "Voudon is in play. Only the Voudon and dead may vote.")
                        return

                    await vote.vote(vt, operator=message.author)
                    if global_vars.game is not NULL_GAME:
                        backup("current_game.pckl")
                    return

                voting_player = (await get_player(message.author))
                if vote.order[vote.position].user != voting_player.user:
                    await safe_send(message.author, "It's not your vote right now. Do you mean @presetvote?")
                    return

                vt = int(argument == "yes" or argument == "y")

                if voudon_in_play and voting_player != voudon_in_play and not voting_player.is_ghost and vt > 0:
                    await safe_send(message.author, "Voudon is in play. Only the Voudon and dead may vote.")
                    return

                await vote.vote(vt)
                if global_vars.game is not NULL_GAME:
                    backup("current_game.pckl")
                return

            # Presets a vote
            elif command == "presetvote" or command == "prevote":

                if global_vars.game is NULL_GAME:
                    await safe_send(message.author, "There's no game right now.")
                    return

                if global_vars.game.isDay == False:
                    await safe_send(message.author, "It's not day right now.")
                    return

                if global_vars.game.days[-1].votes == [] or global_vars.game.days[-1].votes[-1].done == True:
                    await safe_send(message.author, "There's no vote right now.")
                    return

                # if player has active banshee ability then they can prevote 0, 1, or 2 as well
                if (
                    argument != "yes"
                    and argument != "y"
                    and argument != "no"
                    and argument != "n"
                    and argument not in ["0", "1", "2"]
                ):
                    await safe_send(message.author, "{} is not a valid vote. Use 'yes', 'y', 'no', or 'n'.".format(argument))
                    return

                vote = global_vars.game.days[-1].votes[-1]
                voudon_in_play = in_play_voudon()

                if global_vars.gamemaster_role in global_vars.server.get_member(message.author.id).roles:
                    msg = await safe_send(message.author, "Whose vote is this?")
                    try:
                        reply = await client.wait_for(
                            "message",
                            check=(lambda x: x.author == message.author and x.channel == msg.channel),
                            timeout=200,
                        )

                    except asyncio.TimeoutError:
                        await safe_send(message.author, "Timed out.")
                        return

                    if reply.content.lower() == "cancel":
                        await safe_send(message.author, "Preset vote cancelled!")
                        return

                    reply = reply.content.lower()

                    person = await select_player(
                        message.author, reply, global_vars.game.seatingOrder
                    )
                    if person is None:
                        return

                    player_banshee_ability = the_ability(person.character, Banshee)
                    banshee_override = player_banshee_ability and player_banshee_ability.is_screaming

                    if argument in ["0", "1", "2"]:
                        if not banshee_override:
                            await safe_send(message.author, "{} is not a valid vote for this player.".format(argument))
                            return
                        vt = int(argument)
                    else:
                        yes_entered = argument == "yes" or argument == "y"
                        vt = int(yes_entered) * (2 if banshee_override else 1)
                    if voudon_in_play and person != voudon_in_play and not person.is_ghost and vt > 0:
                        await safe_send(message.author, "Voudon is in play. Only the Voudon and dead may vote. Consider killing this player before prevoting yes.")
                        return

                    await vote.preset_vote(person, vt, operator=message.author)
                    if (banshee_override):
                        await safe_send(message.author, "Successfully preset to {}!".format(vt))
                    else:
                        await safe_send(message.author, "Successfully preset to {}!".format(argument))
                    if global_vars.game is not NULL_GAME:
                        backup("current_game.pckl")
                    return

                the_player = await get_player(message.author)
                player_banshee_ability = the_ability(the_player.character, Banshee)
                banshee_override = player_banshee_ability and player_banshee_ability.is_screaming

                if argument in ["0", "1", "2"]:
                    if not banshee_override:
                        await safe_send(message.author, "is not a valid vote. Use 'yes', 'y', 'no', or 'n'.".format(argument))
                        return
                    vt = int(argument)
                else:
                    vt = int(argument == "yes" or argument == "y")

                if voudon_in_play and the_player != voudon_in_play and not the_player.is_ghost and vt > 0:
                    await safe_send(message.author, "Voudon is in play. Only the Voudon and dead may vote. Wait to see if you die before voting yes.")
                    return

                await vote.preset_vote(the_player, vt)
                await safe_send(message.author, "Successfully preset! For more nuanced presets, contact the storytellers.")
                if global_vars.game is not NULL_GAME:
                    backup("current_game.pckl")
                return

            # Cancels a preset vote
            elif command == "cancelpreset" or command == "cancelprevote":

                if global_vars.game is NULL_GAME:
                    await safe_send(message.author, "There's no game right now.")
                    return

                if global_vars.game.isDay == False:
                    await safe_send(message.author, "It's not day right now.")
                    return

                if global_vars.game.days[-1].votes == [] or global_vars.game.days[-1].votes[-1].done == True:
                    await safe_send(message.author, "There's no vote right now.")
                    return

                vote = global_vars.game.days[-1].votes[-1]

                if global_vars.gamemaster_role in global_vars.server.get_member(message.author.id).roles:
                    msg = await safe_send(message.author, "Whose vote do you want to cancel?")
                    try:
                        reply = await client.wait_for(
                            "message",
                            check=(lambda x: x.author == message.author and x.channel == msg.channel),
                            timeout=200,
                        )

                    except asyncio.TimeoutError:
                        await safe_send(message.author, "Timed out.")
                        return

                    if reply.content.lower() == "cancel":
                        await safe_send(message.author, "Cancelling preset cancelled!")
                        return

                    reply = reply.content.lower()

                    person = await select_player(
                        message.author, reply, global_vars.game.seatingOrder
                    )
                    if person is None:
                        return

                    await vote.cancel_preset(person)
                    await safe_send(message.author, "Successfully canceled!")
                    if global_vars.game is not NULL_GAME:
                        backup("current_game.pckl")
                    return

                await vote.cancel_preset(await get_player(message.author))
                await safe_send(message.author, "Successfully canceled! For more nuanced presets, contact the storytellers.")
                if global_vars.game is not NULL_GAME:
                    backup("current_game.pckl")
                return

            elif command == "adjustvotes" or command == "adjustvote":
                if global_vars.game is NULL_GAME or global_vars.gamemaster_role not in global_vars.server.get_member(message.author.id).roles:
                    await safe_send(message.author, "Command {} not recognized. For a list of commands, type @help.".format(command))
                    return
                argument = argument.split(" ")
                if len(argument) != 3:
                    await safe_send(message.author, "adjustvotes takes three arguments: `@adjustvotes amnesiac target multiplier`. For example `@adjustvotes alfred charlie 2`")
                    return
                try:
                    multiplier = int(argument[2])
                except ValueError:
                    await safe_send(message.author, "The third argument must be a whole number")
                    return
                amnesiac = await select_player(message.author, argument[0], global_vars.game.seatingOrder)
                target_player = await select_player(message.author, argument[1], global_vars.game.seatingOrder)
                if not amnesiac or not target_player:
                    return
                if not isinstance(amnesiac.character, Amnesiac):
                    await safe_send(message.author, "{} isn't an amnesiac".format(amnesiac.display_name))
                    return
                amnesiac.character.enhance_votes(target_player, multiplier)
                await safe_send(message.author, "Amnesiac {} is currently multiplying the vote of {} by a factor of {}".format(amnesiac.display_name, target_player.display_name, multiplier))

            # Set a default vote
            elif command == "defaultvote":

                global_settings: GlobalSettings = GlobalSettings.load()

                if argument == "":
                    if global_settings.get_default_vote(message.author.id):
                        global_settings.clear_default_vote(message.author.id)
                        global_settings.save()
                        await safe_send(message.author, "Removed your default vote.")
                    else:
                        await safe_send(message.author, "You have no default vote to remove.")
                    return

                else:
                    argument = argument.split(" ")
                    if len(argument) > 2:
                        await safe_send(message.author, "defaultvote takes at most two arguments: @defaultvote <vote = no> <time = 3600>")
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
                                await safe_send(message.author, "{} is not a valid number of minutes or vote.".format(argument[0]))
                                return
                    else:
                        if argument[0] in ["yes", "y", "no", "n"]:
                            vt = argument[0] in ["yes", "y"]
                        else:
                            await safe_send(message.author, "{} is not a valid vote.".format(argument[0]))
                            return
                        try:
                            time = int(argument[1]) * 60
                        except ValueError:
                            await safe_send(message.author, "{} is not a valid number of minutes.".format(argument[1]))
                            return

                    global_settings.set_default_vote(message.author.id, vt, time)
                    global_settings.save()
                    await safe_send(message.author, "Successfully set default {} vote at {} minutes.".format(["no", "yes"][vt], str(int(time / 60))))
                    return

            # Sends pm
            elif command == "pm" or command == "message":

                if global_vars.game is NULL_GAME:
                    await safe_send(message.author, "There's no game right now.")
                    return

                if not global_vars.game.isDay:
                    await safe_send(message.author, "It's not day right now.")
                    return

                if not global_vars.game.days[-1].isPms:  # Check if PMs open
                    await safe_send(message.author, "PMs are closed.")
                    return

                if not await get_player(message.author):
                    await safe_send(message.author, "You are not in the game. You may not send messages.")
                    return

                candidates_for_whispers = await chose_whisper_candidates(global_vars.game, message.author)
                person = await select_player(
                    # fixme: get players from everyone and then provide feedback if it is not appropriate
                    message.author, argument, global_vars.game.seatingOrder + global_vars.game.storytellers
                )
                if person is None:
                    return

                if person not in candidates_for_whispers:
                    await safe_send(message.author, "You cannot whisper to this player at this time.")
                    return

                message_text = "Messaging {}. What would you like to send?".format(
                    person.display_name
                )
                reply = await safe_send(message.author, message_text)

                # Process reply
                try:
                    intendedMessage = await client.wait_for(
                        "message",
                        check=(lambda x: x.author == message.author and x.channel == reply.channel),
                        timeout=200,
                    )

                # Timeout
                except asyncio.TimeoutError:
                    await safe_send(message.author, "Message timed out!")
                    return

                # Cancel
                if intendedMessage.content.lower() == "cancel":
                    await safe_send(message.author, "Message canceled!")
                    return

                await person.message(
                    await get_player(message.author),
                    intendedMessage.content,
                    message.jump_url,
                )

                await make_active(message.author)
                if global_vars.game is not NULL_GAME:
                    backup("current_game.pckl")
                return

            # Message history
            elif command == "history":
                if global_vars.game is NULL_GAME:
                    await safe_send(message.author, "There's no game right now.")
                    return

                author_roles = global_vars.server.get_member(message.author.id).roles
                if global_vars.gamemaster_role in author_roles or global_vars.observer_role in author_roles:

                    argument = argument.split(" ")
                    if len(argument) > 2:
                        await safe_send(message.author, "There must be exactly one or two comma-separated inputs.")
                        return

                    if len(argument) == 1:
                        person = await select_player(
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
                                await safe_send(message.author, message_text)
                                message_text = ""
                            while msg["day"] != day:
                                await safe_send(message.author, message_text)
                                day += 1
                                message_text = "**Day {}:**".format(str(day))
                            message_text += (
                                "\nFrom: {} | To: {} | Time: {}\n**{}**".format(
                                    msg["from"].display_name,
                                    msg["to"].display_name,
                                    msg["time"].strftime("%m/%d, %H:%M:%S"),
                                    msg["content"],
                                )
                            )

                        await safe_send(message.author, message_text)
                        return

                    person1 = await select_player(
                        message.author, argument[0], global_vars.game.seatingOrder + global_vars.game.storytellers
                    )
                    if person1 is None:
                        return

                    person2 = await select_player(
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
                            (msg["from"] == person1 and msg["to"] == person2)
                            or (msg["to"] == person1 and msg["from"] == person2)
                        ):
                            continue
                        if len(message_text) > 1500:
                            await safe_send(message.author, message_text)
                            message_text = ""
                        while msg["day"] != day:
                            if message_text != "":
                                await safe_send(message.author, message_text)
                            day += 1
                            message_text = "**Day {}:**".format(str(day))
                        message_text += "\nFrom: {} | To: {} | Time: {}\n**{}**".format(
                            msg["from"].display_name,
                            msg["to"].display_name,
                            msg["time"].strftime("%m/%d, %H:%M:%S"),
                            msg["content"],
                        )

                    await safe_send(message.author, message_text)
                    return

                if not await get_player(message.author):
                    await safe_send(message.author, "You are not in the game. You have no message history.")
                    return

                person = await select_player(
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
                for msg in (await get_player(message.author)).message_history:
                    if not msg["from"] == person and not msg["to"] == person:
                        continue
                    if len(message_text) > 1500:
                        await safe_send(message.author, message_text)
                        message_text = ""
                    while msg["day"] != day:
                        if message_text != "":
                            await safe_send(message.author, message_text)
                        day += 1
                        message_text = "\n\n**Day {}:**".format(str(day))
                    message_text += "\nFrom: {} | To: {} | Time: {}\n**{}**".format(
                        msg["from"].display_name,
                        msg["to"].display_name,
                        msg["time"].strftime("%m/%d, %H:%M:%S"),
                        msg["content"],
                    )

                await safe_send(message.author, message_text)
                return

            # Message search
            elif command == "search":
                if global_vars.game is NULL_GAME:
                    await safe_send(message.author, "There's no game right now.")
                    return

                author_roles = global_vars.server.get_member(message.author.id).roles
                if global_vars.gamemaster_role in author_roles or global_vars.observer_role in author_roles:

                    history = []
                    people = []
                    for person in global_vars.game.seatingOrder:
                        for msg in person.message_history:
                            if not msg["from"] in people and not msg["to"] in people:
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
                            await safe_send(message.author, message_text)
                            day += 1
                            message_text = "**Day {}:**".format(str(day))
                        message_text += "\nFrom: {} | To: {} | Time: {}\n**{}**".format(
                            msg["from"].display_name,
                            msg["to"].display_name,
                            msg["time"].strftime("%m/%d, %H:%M:%S"),
                            msg["content"],
                        )

                    await safe_send(message.author, message_text)
                    return

                if not await get_player(message.author):
                    await safe_send(message.author, "You are not in the game. You have no message history.")
                    return

                message_text = (
                    "**Messages mentioning {} (Times in UTC):**\n\n**Day 1:**".format(
                        argument
                    )
                )
                day = 1
                for msg in (await get_player(message.author)).message_history:
                    if not (argument.lower() in msg["content"].lower()):
                        continue
                    while msg["day"] != day:
                        await safe_send(message.author, message_text)
                        day += 1
                        message_text = "**Day {}:**".format(str(day))
                    message_text += "\nFrom: {} | To: {} | Time: {}\n**{}**".format(
                        msg["from"].display_name,
                        msg["to"].display_name,
                        msg["time"].strftime("%m/%d, %H:%M:%S"),
                        msg["content"],
                    )
                await safe_send(message.author, message_text)
                return

            # Create custom alias
            elif command == "makealias":

                argument = argument.split(" ")
                if len(argument) != 2:
                    await safe_send(message.author, "makealias takes exactly two arguments: @makealias <alias> <command>")
                    return

                global_settings: GlobalSettings = GlobalSettings.load()
                alias_term = argument[0]
                command_term = argument[1]
                if "makealias" == alias_term:
                    await safe_send(message.author, "Cannot alias the makealias command.")
                    return
                global_settings.set_alias(message.author.id, alias_term, command_term)
                global_settings.save()
                await safe_send(message.author, "Successfully created alias {} for command {}.".format(alias_term, command_term))
                return

            # Help dialogue
            elif command == "help":
                if global_vars.gamemaster_role in global_vars.server.get_member(message.author.id).roles:
                    if argument == "":
                        embed = discord.Embed(
                            title="Storyteller Help",
                            description="Welcome to the storyteller help dialogue!",
                        )
                        embed.add_field(
                            name="New to storytelling online?",
                            value="Try the tutorial command! (not yet implemented)",
                            inline=False,
                        )
                        embed.add_field(
                            name="Formatting commands",
                            value="Prefixes on this server are {}; any multiple arguments are space-separated".format(
                                "'" + "".join(list(PREFIXES)) + "'"
                            ),
                        )
                        embed.add_field(
                            name="help common",
                            value="Prints commonly used storyteller commands.",
                            inline=False,
                        )
                        embed.add_field(
                            name="help progression",
                            value="Prints commands which progress game-time.",
                            inline=False,
                        )
                        embed.add_field(
                            name="help day",
                            value="Prints commands related to the day.",
                            inline=False,
                        )
                        embed.add_field(
                            name="help gamestate",
                            value="Prints commands which affect the game-state.",
                            inline=False,
                        )
                        embed.add_field(
                            name="help info",
                            value="Prints commands which display game information.",
                            inline=False,
                        )
                        embed.add_field(
                            name="help configure",
                            value="Prints commands which configures how the bot works.",
                            inline=False,
                        )
                        embed.add_field(
                            name="help player",
                            value="Prints the player help dialogue.",
                            inline=False,
                        )
                        embed.add_field(
                            name="help misc",
                            value="Prints miscellaneous commands.",
                            inline=False,
                        )
                        embed.add_field(
                            name="Bot Questions?",
                            value="Discuss or provide feedback at https://github.com/fiveofswords/botc-bot",
                            inline=False,
                        )
                        # this is a rare place that should use .send -- it is sending an embed and safe_send is not set up to split if needed
                        await message.author.send(embed=embed)
                        return
                    elif argument == "common":
                        embed = discord.Embed(
                            title="Common Commands",
                            description="Multiple arguments are space-separated.",
                        )
                        embed.add_field(
                            name="startgame", value="starts the game", inline=False
                        )
                        embed.add_field(
                            name="endgame <<team>>",
                            value="ends the game, with winner team",
                            inline=False,
                        )
                        embed.add_field(
                            name="startday <<players>>",
                            value="starts the day, killing players",
                            inline=False,
                        )
                        embed.add_field(
                            name="endday",
                            value="ends the day. if there is an execution, execute is preferred",
                            inline=False,
                        )
                        embed.add_field(
                            name="kill <<player>>", value="kills player", inline=False
                        )
                        embed.add_field(
                            name="execute <<player>>",
                            value="executes player",
                            inline=False,
                        )
                        embed.add_field(
                            name="exile <<traveler>>",
                            value="exiles traveler",
                            inline=False,
                        )
                        embed.add_field(
                            name="setdeadline <time>",
                            value="sends a message with time in UTC as the deadline and opens nominations. The format can be HH:MM to specify a UTC time, or +HHhMMm to specify a relative time from now e.g. +3h15m; alternatively an epoch timestamp can be used - see https://www.epochconverter.com/",
                            inline=False,
                        )
                        embed.add_field(
                            name="poison <<player>>",
                            value="poisons player",
                            inline=False,
                        )
                        embed.add_field(
                            name="unpoison <<player>>",
                            value="unpoisons player",
                            inline=False,
                        )
                        # this is a rare place that should use .send -- it is sending an embed and safe_send is not set up to split if needed
                        await message.author.send(embed=embed)
                        return
                    elif argument == "player":
                        pass
                    elif argument == "progression":
                        embed = discord.Embed(
                            title="Game Progression",
                            description="Commands which progress game-time.",
                        )
                        embed.add_field(
                            name="startgame", value="starts the game", inline=False
                        )
                        embed.add_field(
                            name="endgame <<team>>",
                            value="ends the game, with winner team",
                            inline=False,
                        )
                        embed.add_field(
                            name="startday <<players>>",
                            value="starts the day, killing players",
                            inline=False,
                        )
                        embed.add_field(
                            name="endday",
                            value="ends the day. if there is an execution, execute is preferred",
                            inline=False,
                        )
                        # this is a rare place that should use .send -- it is sending an embed and safe_send is not set up to split if needed
                        await message.author.send(embed=embed)
                        return
                    elif argument == "day":
                        embed = discord.Embed(
                            title="Day-related",
                            description="Commands which affect variables related to the day.",
                        )
                        embed.add_field(
                            name="setdeadline <time>",
                            value="sends a message with time in UTC as the deadline and opens nominations. The format can be HH:MM to specify a UTC time, or +HHhMMm to specify a relative time from now e.g. +3h15m; alternatively an epoch timestamp can be used - see https://www.epochconverter.com/",
                            inline=False,
                        )
                        embed.add_field(name="openpms", value="opens pms", inline=False)
                        embed.add_field(
                            name="opennoms", value="opens nominations", inline=False
                        )
                        embed.add_field(
                            name="open", value="opens pms and nominations", inline=False
                        )
                        embed.add_field(
                            name="closepms", value="closes pms", inline=False
                        )
                        embed.add_field(
                            name="closenoms", value="closes nominations", inline=False
                        )
                        embed.add_field(
                            name="close",
                            value="closes pms and nominations",
                            inline=False,
                        )
                        embed.add_field(
                            name="vote",
                            value="votes for the current player",
                            inline=False,
                        )
                        # this is a rare place that should use .send -- it is sending an embed and safe_send is not set up to split if needed
                        await message.author.send(embed=embed)
                        return
                    elif argument == "gamestate":
                        embed = discord.Embed(
                            title="Game-State",
                            description="Commands which directly affect the game-state.",
                        )
                        embed.add_field(
                            name="kill <<player>>", value="kills player", inline=False
                        )
                        embed.add_field(
                            name="execute <<player>>",
                            value="executes player",
                            inline=False,
                        )
                        embed.add_field(
                            name="exile <<traveler>>",
                            value="exiles traveler",
                            inline=False,
                        )
                        embed.add_field(
                            name="revive <<player>>",
                            value="revives player",
                            inline=False,
                        )
                        embed.add_field(
                            name="changerole <<player>>",
                            value="changes player's role",
                            inline=False,
                        )
                        embed.add_field(
                            name="changealignment <<player>>",
                            value="changes player's alignment",
                            inline=False,
                        )
                        embed.add_field(
                            name="changeability <<player>>",
                            value="changes player's ability, if applicable to their character (ex apprentice)",
                            inline=False,
                        )
                        embed.add_field(
                            name="removeability <<player>>",
                            value="clears a player's modified ability, if applicable to their character (ex cannibal)",
                            inline=False,
                        )
                        embed.add_field(
                            name="givedeadvote <<player>>",
                            value="adds a dead vote for player",
                            inline=False,
                        )
                        embed.add_field(
                            name="removedeadvote <<player>>",
                            value="removes a dead vote from player. not necessary for ordinary usage",
                            inline=False,
                        )
                        embed.add_field(
                            name="poison <<player>>",
                            value="poisons player",
                            inline=False,
                        )
                        embed.add_field(
                            name="unpoison <<player>>",
                            value="unpoisons player",
                            inline=False,
                        )
                        # this is a rare place that should use .send -- it is sending an embed and safe_send is not set up to split if needed
                        await message.author.send(embed=embed)
                        return
                    elif argument == "configure":
                        embed = discord.Embed(
                            title="Configuration",
                            description="Commands which configure how the bot works.",
                        )
                        embed.add_field(
                            name="whispermode <<all/neighbors/storytellers>>", value="sets whisper mode", inline=False
                        )
                        embed.add_field(
                            name="enabletally", value="enables display of whisper counts", inline=False
                        )
                        embed.add_field(
                            name="disabletally", value="disables display of whisper counts", inline=False
                        )
                        embed.add_field(
                            name="setatheist <<true/false>>",
                            value="sets whether the atheist is on the script - this allows the storyteller to be nominated",
                            inline=False,
                        )
                        embed.add_field(
                            name="automatekills <<true/false>>",
                            value="sets whether deaths are automated for certain characters (Riot, Golem, etc.)."
                            "\nThis is not recommended for most games, as more work is needed from the Storytellers",
                            inline=False,
                        )
                        await message.author.send(embed=embed)
                        return
                    elif argument == "info":
                        embed = discord.Embed(
                            title="Informative",
                            description="Commands which display information about the game.",
                        )
                        embed.add_field(
                            name="history <<player1>> <<player2>>",
                            value="views the message history between player1 and player2",
                            inline=False,
                        )
                        embed.add_field(
                            name="history <<player>>",
                            value="views all of player's messages",
                            inline=False,
                        )
                        embed.add_field(
                            name="votehistory",
                            value="views all nominations and votes for those nominations",
                            inline=False,
                        )
                        embed.add_field(
                            name="search <<content>>",
                            value="views all messages containing content",
                            inline=False,
                        )
                        embed.add_field(
                            name="whispers <<player>>",
                            value="view a count of messages for the player per day",
                            inline=False,
                        )
                        embed.add_field(
                            name="info <<player>>",
                            value="views game information about player",
                            inline=False,
                        )
                        embed.add_field(
                            name="grimoire", value="views the grimoire", inline=False
                        )
                        # this is a rare place that should use .send -- it is sending an embed and safe_send is not set up to split if needed
                        await message.author.send(embed=embed)
                        return
                    elif argument == "misc":
                        embed = discord.Embed(
                            title="Miscellaneous",
                            description="Commands with miscellaneous uses, primarily for troubleshooting and seating.",
                        )
                        embed.add_field(
                            name="notactive",
                            value="lists players who are yet to speak",
                            inline=False,
                        )
                        embed.add_field(
                            name="makeinactive <<player>>",
                            value="marks player as inactive. must be done in all games player is participating in",
                            inline=False,
                        )
                        embed.add_field(
                            name="undoinactive <<player>>",
                            value="undoes an inactivity mark. must be done in all games player is participating in",
                            inline=False,
                        )
                        embed.add_field(
                            name="checkin <<players>>",
                            value="Marks players as checked in for tonight.  Resets each day.",
                            inline=False,
                        )
                        embed.add_field(
                            name="undocheckin <<players>>",
                            value="Marks players as not checked in for tonight.",
                            inline=False,
                        )
                        embed.add_field(
                            name="addtraveler <<player>> or addtraveller <<player>>",
                            value="adds player as a traveler",
                            inline=False,
                        )
                        embed.add_field(
                            name="removetraveler <<traveler>> or removetraveller <<traveler>>",
                            value="removes traveler from the game",
                            inline=False,
                        )
                        embed.add_field(
                            name="cancelnomination",
                            value="cancels the previous nomination",
                            inline=False,
                        )
                        embed.add_field(
                            name="reseat", value="reseats the game", inline=False
                        )
                        # this is a rare place that should use .send -- it is sending an embed and safe_send is not set up to split if needed
                        await message.author.send(embed=embed)
                        return
                embed = discord.Embed(
                    title="Player Commands",
                    description="Multiple arguments are space-separated.",
                )
                embed.add_field(
                    name="New to playing online?",
                    value="Try the tutorial command! (not yet implemented)",
                    inline=False,
                )
                embed.add_field(
                    name="Formatting commands",
                    value="Prefixes on this server are {}; any multiple arguments are space-separated".format(
                        "'" + "".join(list(PREFIXES)) + "'"
                    ),
                )
                embed.add_field(
                    name="pm <<player>> or message <<player>>",
                    value="sends player a message",
                    inline=False,
                )
                embed.add_field(
                    name="history <<player>>",
                    value="views your message history with player",
                    inline=False,
                )
                embed.add_field(
                    name="search <<content>>",
                    value="views all of your messages containing content",
                    inline=False,
                )
                embed.add_field(
                    name="whispers",
                    value="view a count of your messages with other players per day",
                    inline=False,
                )
                embed.add_field(
                    name="vote <<yes/no>>",
                    value="votes on an ongoing nomination",
                    inline=False,
                )
                embed.add_field(
                    name="nominate <<player>>", value="nominates player", inline=False
                )
                embed.add_field(
                    name="presetvote <<yes/no>> or prevote <<yes/no>>",
                    value="submits a preset vote. will not work if it is your turn to vote. not reccomended -- contact the storytellers instead",
                    inline=False,
                )
                embed.add_field(
                    name="cancelprevote",
                    value="cancels an existing prevote",
                    inline=False,
                )
                embed.add_field(
                    name="defaultvote <<vote = 'no'>> <<time=60>>",
                    value="will always vote vote in time minutes. if no arguments given, deletes existing defaults.",
                    inline=False,
                )
                embed.add_field(
                    name="makealias <<alias>> <<command>>",
                    value="creats an alias for a command",
                    inline=False,
                )
                embed.add_field(name="clear", value="returns whitespace", inline=False)
                embed.add_field(
                    name="cannominate",
                    value="lists players who are yet to nominate or skip",
                    inline=False,
                )
                embed.add_field(
                    name="canbenominated",
                    value="lists players who are yet to be nominated",
                    inline=False,
                )
                embed.add_field(
                    name="tocheckin",
                    value="lists players who are yet to check in",
                    inline=False,
                )
                embed.add_field(
                    name="Bot Questions?", value="Discuss or provide feedback at https://github.com/fiveofswords/botc-bot", inline=False
                )
                # this is a rare place that should use .send -- it is sending an embed and safe_send is not set up to split if needed
                await message.author.send(embed=embed)
                return

            # Command unrecognized
            else:
                await safe_send(message.author, "Command {} not recognized. For a list of commands, type @help.".format(command))


# in_play_voudon has been moved to model/characters/specific.py


async def check_and_print_if_one_or_zero_to_check_in():
    not_checked_in = [
        player
        for player in global_vars.game.seatingOrder
        if not player.has_checked_in and player.alignment != STORYTELLER_ALIGNMENT
    ]
    if len(not_checked_in) == 1:
        for memb in global_vars.gamemaster_role.members:
            await safe_send(
                memb, f"Just waiting on {not_checked_in[0].display_name} to check in."
            )
    if len(not_checked_in) == 0:
        for memb in global_vars.gamemaster_role.members:
            await safe_send(memb, "Everyone has checked in!")


def to_whisper_mode(argument):
    new_mode = WhisperMode.ALL
    if WhisperMode.ALL.casefold() == argument.casefold():
        new_mode = WhisperMode.ALL
    elif WhisperMode.NEIGHBORS.casefold() == argument.casefold():
        new_mode = WhisperMode.NEIGHBORS
    elif WhisperMode.STORYTELLERS.casefold() == argument.casefold():
        new_mode = WhisperMode.STORYTELLERS
    else:
        new_mode = None
    return new_mode


async def chose_whisper_candidates(game, author):
    if game.whisper_mode == WhisperMode.ALL:
        return game.seatingOrder + game.storytellers
    if game.whisper_mode == WhisperMode.STORYTELLERS:
        return game.storytellers
    if game.whisper_mode == WhisperMode.NEIGHBORS:
        # determine neighbors
        player_self = await get_player(author)
        author_index = game.seatingOrder.index(player_self)
        neighbor_left = game.seatingOrder[(author_index - 1) % len(game.seatingOrder)]
        neighbor_right = game.seatingOrder[(author_index + 1) % len(game.seatingOrder)]
        return [neighbor_left, player_self, neighbor_right] + game.storytellers


async def is_storyteller(arg):
    if arg in ["storytellers", "the storytellers", "storyteller", "the storyteller"]:
        return True
    options = await generate_possibilities(arg, global_vars.server.members)
    return len(options) == 1 and global_vars.gamemaster_role in global_vars.server.get_member((options)[0].id).roles


@client.event
async def on_message_edit(before, after):
    # Handles messages on modification
    if after.author == client.user:
        return

    # On pin
    message_author_player = await get_player(after.author)
    if before.channel == global_vars.channel and before.pinned == False and after.pinned == True:

        # Nomination
        if "nominate " in after.content.lower():

            argument = after.content.lower()[after.content.lower().index("nominate ") + 9:]

            if global_vars.game is NULL_GAME:
                await safe_send(global_vars.channel, "There's no game right now.")
                await after.unpin()
                return

            if global_vars.game.isDay == False:
                await safe_send(global_vars.channel, "It's not day right now.")
                await after.unpin()
                return

            if global_vars.game.days[-1].isNoms == False:
                await safe_send(global_vars.channel, "Nominations aren't open right now.")
                await after.unpin()
                return

            if not message_author_player:
                await safe_send(
                    global_vars.channel, "You aren't in the game, and so cannot nominate."
                )
                await after.unpin()
                return

            names = await generate_possibilities(argument, global_vars.game.seatingOrder)
            traveler_called = len(names) == 1 and isinstance(names[0].character, Traveler)

            banshee_ability_of_player = the_ability(message_author_player.character, Banshee) if message_author_player else None
            banshee_override = banshee_ability_of_player and banshee_ability_of_player.is_screaming and not banshee_ability_of_player.is_poisoned

            if message_author_player.is_ghost and not traveler_called and not message_author_player.riot_nominee and not banshee_override:
                await safe_send(global_vars.channel, "You are dead, and so cannot nominate.")
                await after.unpin()
                return
            if (banshee_override and banshee_ability_of_player.remaining_nominations < 1) and not traveler_called:
                await safe_send(global_vars.channel, "You have already nominated twice.")
                await after.unpin()
                return
            if global_vars.game.days[-1].riot_active and not message_author_player.riot_nominee:
                await safe_send(global_vars.channel, "Riot is active. It is not your turn to nominate.")
                await after.unpin()
                return
            if not (message_author_player).can_nominate and not traveler_called and not banshee_override:
                await safe_send(global_vars.channel, "You have already nominated.")
                await after.unpin()
                return

            if global_vars.game.script.isAtheist:
                storyteller_nomination = await is_storyteller(argument)
                if storyteller_nomination:
                    if None in [x.nominee for x in global_vars.game.days[-1].votes]:
                        await safe_send(
                            global_vars.channel,
                            "The storytellers have already been nominated today.",
                        )
                        await after.unpin()
                        return
                    remove_banshee_nomination(banshee_ability_of_player)
                    await global_vars.game.days[-1].nomination(None, message_author_player)
                    if global_vars.game is not NULL_GAME:
                        backup("current_game.pckl")
                    await after.unpin()
                    return

            if len(names) == 1:

                if not names[0].can_be_nominated:
                    await safe_send(
                        global_vars.channel, "{} has already been nominated.".format(names[0].display_name)
                    )
                    await after.unpin()
                    return

                remove_banshee_nomination(banshee_ability_of_player)

                await global_vars.game.days[-1].nomination(names[0], message_author_player)
                if global_vars.game is not NULL_GAME:
                    backup("current_game.pckl")
                await after.unpin()
                return

            elif len(names) > 1:

                await safe_send(global_vars.channel, "There are too many matching players.")
                await after.unpin()
                return

            else:

                await safe_send(global_vars.channel, "There are no matching players.")
                await after.unpin()
                return

        # Skip
        elif "skip" in after.content.lower():

            if global_vars.game is NULL_GAME:
                await safe_send(global_vars.channel, "There's no game right now.")
                await after.unpin()
                return

            if not message_author_player:
                await safe_send(
                    global_vars.channel, "You aren't in the game, and so cannot nominate."
                )
                await after.unpin()
                return

            if not global_vars.game.isDay:
                await safe_send(global_vars.channel, "It's not day right now.")
                await after.unpin()
                return

            (message_author_player).has_skipped = True
            if global_vars.game is not NULL_GAME:
                backup("current_game.pckl")

            can_nominate = [
                player
                for player in global_vars.game.seatingOrder
                if player.can_nominate == True
                   and player.has_skipped == False
                   and player.alignment != STORYTELLER_ALIGNMENT
                   and player.is_ghost == False
            ]
            if len(can_nominate) == 1:
                for memb in global_vars.gamemaster_role.members:
                    await safe_send(
                        memb,
                        "Just waiting on {} to nominate or skip.".format(
                            can_nominate[0].display_name
                        ),
                    )
            if len(can_nominate) == 0:
                for memb in global_vars.gamemaster_role.members:
                    await safe_send(memb, "Everyone has nominated or skipped!")

            global_vars.game.days[-1].skipMessages.append(after.id)

            return

    # On unpin
    elif before.channel == global_vars.channel and before.pinned == True and after.pinned == False:

        # Unskip
        if "skip" in after.content.lower():
            (message_author_player).has_skipped = False
            if global_vars.game is not NULL_GAME:
                backup("current_game.pckl")


# remove_banshee_nomination has been moved to model/characters/specific.py


@client.event
async def on_member_update(before, after):
    # Handles member-level modifications
    if after == client.user:
        return

    if global_vars.game is not NULL_GAME:
        player = await get_player(after)
        if player and player.display_name != after.display_name:
            player.display_name = after.display_name
            await global_vars.game.reseat(global_vars.game.seatingOrder)
            await safe_send(after, "Your nickname has been updated.")
            backup("current_game.pckl")

        if global_vars.gamemaster_role in after.roles and global_vars.gamemaster_role not in before.roles:
            st_player = Player(Storyteller, STORYTELLER_ALIGNMENT, after, st_channel=None, position=None)
            global_vars.game.storytellers.append(st_player)
        elif global_vars.gamemaster_role in before.roles and global_vars.gamemaster_role not in after.roles:
            for st in global_vars.game.storytellers:
                if st.user.id == after.id:
                    global_vars.game.storytellers.remove(st)


#######################
# TypeVar Magic
#######################
class HasNick(Protocol):
    nick: Optional[str]


T = TypeVar('T', bound=HasNick)