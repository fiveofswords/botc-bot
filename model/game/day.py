import itertools
import math

import discord

import bot_client
import global_vars
import model.characters
import model.game.whisper_mode
import model.nomination_buttons
from utils import message_utils, game_utils


class Day:
    """Stores information about a specific day.
    
    Attributes:
        isExecutionToday: Whether there is an execution today
        isNoms: Whether nominations are open
        isPms: Whether PMs are open
        votes: List of votes
        voteEndMessages: List of vote end messages
        deadlineMessages: List of deadline messages
        skipMessages: List of skip messages
        aboutToDie: The player about to die, as well as the vote object that is about to kill them
        riot_active: Whether riot is active
        st_riot_kill_override: Whether the ST has overridden the riot kill
    """

    isExecutionToday: bool
    isNoms: bool
    isPms: bool
    votes: list['model.game.base_vote.BaseVote']
    voteEndMessages: list[int]
    deadlineMessages: list[int]
    skipMessages: list[int]
    aboutToDie: tuple['model.player.Player | None', 'model.game.base_vote.BaseVote'] | None
    riot_active: bool
    st_riot_kill_override: bool

    def __init__(self):
        """Initialize a Day."""
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
        """Opens PMs."""
        self.isPms = True
        for memb in global_vars.gamemaster_role.members:
            await message_utils.safe_send(memb, "PMs are now open.")

        await game_utils.update_presence(bot_client.client)

    async def open_noms(self):
        """Opens nominations."""
        self.isNoms = True
        if len(self.votes) == 0:
            for person in global_vars.game.seatingOrder:
                if isinstance(person.character, model.characters.NomsCalledModifier):
                    person.character.on_noms_called()
        for memb in global_vars.gamemaster_role.members:
            await message_utils.safe_send(memb, "Nominations are now open.")

        await game_utils.update_presence(bot_client.client)

    async def close_pms(self):
        """Closes PMs."""
        self.isPms = False
        for memb in global_vars.gamemaster_role.members:
            await message_utils.safe_send(memb, "PMs are now closed.")

        await game_utils.update_presence(bot_client.client)

    async def close_noms(self):
        """Closes nominations."""
        self.isNoms = False
        for memb in global_vars.gamemaster_role.members:
            await message_utils.safe_send(memb, "Nominations are now closed.")

        await game_utils.update_presence(bot_client.client)

    async def nomination(self, nominee, nominator):
        """Handle a nomination.
        
        Args:
            nominee: The player being nominated
            nominator: The player making the nomination
        """

        global_vars.game.whisper_mode = model.game.whisper_mode.WhisperMode.NEIGHBORS
        await self.close_noms()

        # todo: if organ grinder ability is active, then this first message should not be output.
        if not nominee:
            self.votes.append(Vote(nominee, nominator))
            if self.aboutToDie is not None:
                announcement = await message_utils.safe_send(
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
                announcement = await message_utils.safe_send(
                    global_vars.channel,
                    "{}, the storytellers have been nominated by {}. {} to execute.".format(
                        global_vars.player_role.mention,
                        nominator.display_name if nominator else "the storytellers",
                        str(int(math.ceil(self.votes[-1].majority))),
                    ),
                )
            await announcement.pin()
            if nominator and nominee and not isinstance(nominee.character, model.characters.Traveler):
                nominator.can_nominate = False

            # Send nomination buttons to ST channels for storyteller nominations
            nominee_name = "the storytellers"
            nominator_name = nominator.display_name if nominator else "the storytellers"

            if self.aboutToDie is not None:
                votes_needed = int(math.ceil(self.aboutToDie[1].votes + 1))
            else:
                votes_needed = int(math.ceil(self.votes[-1].majority))

            await model.nomination_buttons.send_nomination_buttons_to_st_channels(
                nominee_name, nominator_name, votes_needed
            )

            proceed = True
            # FIXME:there might be a case where a player earlier in the seating order makes the nomination not proceed
            #  but one later in the seating order may be relevant. Short circuit here stops two Riot messages, e.g.
            #  There may need to be some rework based on NominationModifier priority
            for person in global_vars.game.seatingOrder:
                if isinstance(person.character, model.characters.NominationModifier) and proceed:
                    proceed = await person.character.on_nomination(
                        nominee, nominator, proceed
                    )
            if not proceed:
                # do not proceed with collecting votes
                return
        elif isinstance(nominee.character, model.characters.Traveler):
            nominee.can_be_nominated = False
            self.votes.append(TravelerVote(nominee, nominator))
            announcement = await message_utils.safe_send(
                global_vars.channel,
                "{}, {} has called for {}'s exile. {} to exile.".format(
                    global_vars.player_role.mention,
                    nominator.display_name if nominator else "The storytellers",
                    nominee.user.mention,
                    str(int(math.ceil(self.votes[-1].majority))),
                ),
            )
            await announcement.pin()

            # Send nomination buttons to ST channels for traveler exile
            nominee_name = nominee.display_name
            nominator_name = nominator.display_name if nominator else "the storytellers"
            votes_needed = int(math.ceil(self.votes[-1].majority))

            await model.nomination_buttons.send_nomination_buttons_to_st_channels(
                nominee_name, nominator_name, votes_needed
            )
        else:
            nominee.can_be_nominated = False
            self.votes.append(Vote(nominee, nominator))
            # FIXME:there might be a case where a player earlier in the seating order makes the nomination not proceed
            #  but one later in the seating order may be relevant. Short circuit here stops two Riot messages, e.g.
            #  There may need to be some rework based on NominationModifier priority
            proceed = True
            for person in global_vars.game.seatingOrder:
                if isinstance(person.character, model.characters.NominationModifier) and proceed:
                    proceed = await person.character.on_nomination(
                        nominee, nominator, proceed
                    )
            if not proceed:
                # do not proceed with collecting votes
                return
            if self.aboutToDie is not None:
                announcement = await message_utils.safe_send(
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
                announcement = await message_utils.safe_send(
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

            # Send nomination buttons to ST channels for active players
            nominee_name = nominee.display_name if nominee.user not in global_vars.gamemaster_role.members else "the storytellers"
            nominator_name = nominator.display_name if nominator else "the storytellers"

            # Calculate votes needed based on whether there's already someone about to die
            if self.aboutToDie is not None:
                votes_needed = int(math.ceil(self.aboutToDie[1].votes + 1))
            else:
                votes_needed = int(math.ceil(self.votes[-1].majority))

            await model.nomination_buttons.send_nomination_buttons_to_st_channels(
                nominee_name, nominator_name, votes_needed
            )

            proceed = True
            # FIXME:there might be a case where a player earlier in the seating order makes the nomination not proceed
            #  but one later in the seating order may be relevant. Short circuit here stops two Riot messages, e.g.
            #  There may need to be some rework based on NominationModifier priority
            for person in global_vars.game.seatingOrder:
                if isinstance(person.character, model.characters.NominationModifier) and proceed:
                    proceed = await person.character.on_nomination(
                        nominee, nominator, proceed
                    )
            if not proceed:
                # do not proceed with collecting user input for this vote
                return

        if (global_vars.game.show_tally):
            message_tally = {X: 0 for X in itertools.combinations(global_vars.game.seatingOrder, 2)}

            has_had_multiple_votes = len(self.votes) > 1
            last_vote_message = None if not has_had_multiple_votes else await global_vars.channel.fetch_message(
                self.votes[-2].announcements[0])

            for person in global_vars.game.seatingOrder:
                for msg in person.message_history:
                    if msg["from_player"] == person:
                        if has_had_multiple_votes:
                            if msg["time"] >= last_vote_message.created_at:
                                if (person, msg["to_player"]) in message_tally:
                                    message_tally[(person, msg["to_player"])] += 1
                                elif (msg["to_player"], person) in message_tally:
                                    message_tally[(msg["to_player"], person)] += 1
                                else:
                                    message_tally[(person, msg["to_player"])] = 1
                        else:
                            if msg["day"] == len(global_vars.game.days):
                                if (person, msg["to_player"]) in message_tally:
                                    message_tally[(person, msg["to_player"])] += 1
                                elif (msg["to_player"], person) in message_tally:
                                    message_tally[(msg["to_player"], person)] += 1
                                else:
                                    message_tally[(person, msg["to_player"])] = 1
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
            await message_utils.safe_send(global_vars.channel, messageText)

        self.votes[-1].announcements.append(announcement.id)
        await self.votes[-1].call_next()

    async def end(self):
        """Ends the day."""
        for person in global_vars.game.seatingOrder:
            if isinstance(person.character, model.characters.DayEndModifier):
                person.character.on_day_end()

        for msg in self.voteEndMessages:
            try:
                await (await global_vars.channel.fetch_message(msg)).unpin()
            except discord.errors.NotFound:
                print("Missing message: ", str(msg))
            except discord.errors.DiscordServerError:
                print("Discord server error: ", str(msg))

        for msg in self.deadlineMessages:
            try:
                await (await global_vars.channel.fetch_message(msg)).unpin()
            except discord.errors.NotFound:
                print("Missing message: ", str(msg))
            except discord.errors.DiscordServerError:
                print("Discord server error: ", str(msg))

        for msg in self.skipMessages:
            try:
                await (await global_vars.channel.fetch_message(msg)).unpin()
            except discord.errors.NotFound:
                print("Missing message: ", str(msg))
            except discord.errors.DiscordServerError:
                print("Discord server error: ", str(msg))

        global_vars.game.isDay = False
        global_vars.game.whisper_mode = model.game.whisper_mode.WhisperMode.ALL
        self.isNoms = False
        self.isPms = False

        if not self.isExecutionToday:
            await message_utils.safe_send(global_vars.channel, "No one was executed.")

        await message_utils.safe_send(global_vars.channel, "{}, go to sleep!".format(global_vars.player_role.mention))

        if not global_vars.game.days[-1].riot_active:
            if global_vars.game.show_tally:
                message_tally = {X: 0 for X in itertools.combinations(global_vars.game.seatingOrder, 2)}
                has_had_multiple_votes = len(self.votes) > 0

                last_vote_message = None if not has_had_multiple_votes else (
                    await global_vars.channel.fetch_message(self.votes[-1].announcements[0]) if self.votes and
                                                                                                self.votes[
                                                                                                    -1].announcements else None
                )
                for person in global_vars.game.seatingOrder:
                    for msg in person.message_history:
                        if msg["from_player"] == person:
                            if has_had_multiple_votes:
                                if msg["time"] >= last_vote_message.created_at:
                                    if (person, msg["to_player"]) in message_tally:
                                        message_tally[(person, msg["to_player"])] += 1
                                    elif (msg["to_player"], person) in message_tally:
                                        message_tally[(msg["to_player"], person)] += 1
                                    else:
                                        message_tally[(person, msg["to_player"])] = 1
                            else:
                                if msg["day"] == len(global_vars.game.days):
                                    if (person, msg["to_player"]) in message_tally:
                                        message_tally[(person, msg["to_player"])] += 1
                                    elif (msg["to_player"], person) in message_tally:
                                        message_tally[(msg["to_player"], person)] += 1
                                    else:
                                        message_tally[(person, msg["to_player"])] = 1
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
                await message_utils.safe_send(global_vars.channel, messageText)

        await game_utils.update_presence(bot_client.client)


# Import at the end to avoid circular imports
from model.game.vote import Vote
from model.game.traveler_vote import TravelerVote
