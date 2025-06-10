import asyncio

import discord

import global_vars
from model.settings import GlobalSettings
from utils import message_utils


class TravelerVote:
    """Stores information about a specific call for exile.

    Attributes:
        nominee: The player being nominated
        nominator: The player making the nomination
        order: The order of players voting
        votes: The number of votes
        voted: The players who voted
        history: The voting history
        announcements: The announcement messages
        presetVotes: The preset votes
        values: The vote values for each player
        majority: The number of votes needed for a majority
        position: The current position in the vote order
        done: Whether the vote is done
    """

    def __init__(self, nominee, nominator):
        """Initialize a TravelerVote.

        Args:
            nominee: The player being nominated
            nominator: The player making the nomination
        """
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
        """Calls for person to vote."""
        toCall = self.order[self.position]
        if toCall.user.id in self.presetVotes:
            await self.vote(self.presetVotes[toCall.user.id])
            return
        await message_utils.safe_send(
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
            await message_utils.safe_send(toCall.user, "Will enter a {} vote in {} minutes.".format(
                ["no", "yes"][default[0]], str(int(default[1] / 60))
            ))
            await asyncio.sleep(time)
            if toCall == global_vars.game.days[-1].votes[-1].order[global_vars.game.days[-1].votes[-1].position]:
                await self.vote(default[0])
            for memb in global_vars.gamemaster_role.members:
                await message_utils.safe_send(
                    memb,
                    "{}'s vote. Their default is {} in {} minutes.".format(
                        toCall.display_name,
                        ["no", "yes"][default[0]],
                        str(int(default[1] / 60)),
                    ),
                )
        else:
            for memb in global_vars.gamemaster_role.members:
                await message_utils.safe_send(
                    memb, "{}'s vote. They have no default.".format(toCall.display_name)
                )

    async def vote(self, vt, operator=None):
        """Executes a vote.

        Args:
            vt: 0 if no, 1 if yes
            operator: The operator making the vote
        """
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
                await message_utils.safe_send(
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
        """When the vote is over."""
        if len(self.voted) == 0:
            text = "no one"
        elif len(self.voted) == 1:
            text = self.voted[0].display_name
        elif len(self.voted) == 2:
            text = self.voted[0].display_name + " and " + self.voted[1].display_name
        else:
            text = (", ".join([x.display_name for x in self.voted[:-1]]) + ", and " + self.voted[-1].display_name)
        if self.votes >= self.majority:
            announcement = await message_utils.safe_send(
                global_vars.channel,
                "{} votes on {} (nominated by {}): {}.".format(
                    str(self.votes),
                    self.nominee.display_name if self.nominee else "the storytellers",
                    self.nominator.display_name if self.nominator else "the storytellers",
                    text,
                ),
            )
        else:
            announcement = await message_utils.safe_send(
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
            except discord.errors.DiscordServerError:
                print("Discord server error: ", str(msg))

        self.done = True

        await global_vars.game.days[-1].open_noms()
        await global_vars.game.days[-1].open_pms()

    async def preset_vote(self, person, vt, operator=None):
        """Preset a vote.

        Args:
            person: The player to preset
            vt: The vote value
            operator: The operator making the preset
        """
        self.presetVotes[person.user.id] = vt

    async def cancel_preset(self, person):
        """Cancel a preset vote.

        Args:
            person: The player to cancel the preset for
        """
        del self.presetVotes[person.user.id]

    async def delete(self):
        """Undoes an unintentional nomination."""
        if self.nominator:
            self.nominator.can_nominate = True
        if self.nominee:
            self.nominee.can_be_nominated = True

        for msg in self.announcements:
            try:
                await (await global_vars.channel.fetch_message(msg)).unpin()
            except discord.errors.NotFound:
                print("Missing message: ", str(msg))
            except discord.errors.DiscordServerError:
                print("Discord server error: ", str(msg))

        self.done = True

        global_vars.game.days[-1].votes.remove(self)
