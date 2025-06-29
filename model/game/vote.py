import asyncio
from collections import OrderedDict

import discord

import global_vars
import model.characters
import model.settings
from utils import character_utils, message_utils, player_utils


def in_play_voudon():
    """Check if a Voudon is in play.

    Returns:
        The Voudon player if one is in play and not a ghost, otherwise None
    """
    return next((x for x in global_vars.game.seatingOrder if
                 character_utils.the_ability(x.character, model.characters.Voudon) and not x.is_ghost), None)


def remove_banshee_nomination(banshee_ability_of_player):
    """Remove a nomination from a Banshee.

    Args:
        banshee_ability_of_player: The Banshee ability
    """
    if banshee_ability_of_player and banshee_ability_of_player.is_screaming:
        banshee_ability_of_player.remaining_nominations -= 1


class Vote:
    """Stores information about a specific vote.
    
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
        """Initialize a Vote.
        
        Args:
            nominee: The player being nominated
            nominator: The player making the nomination
        """
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
            banshee_ability = character_utils.the_ability(person.character, model.characters.Banshee)
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
            if isinstance(person.character, model.characters.VoteBeginningModifier):
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
        """Calls for person to vote."""
        toCall = self.order[self.position]
        player_banshee_ability = character_utils.the_ability(toCall.character, model.characters.Banshee)
        player_is_active_banshee = player_banshee_ability and player_banshee_ability.is_screaming
        voudon_is_active = in_play_voudon()
        for person in global_vars.game.seatingOrder:
            if isinstance(person.character, model.characters.VoteModifier):
                person.character.on_vote_call(toCall)
        if toCall.is_ghost and toCall.dead_votes < 1 and not player_is_active_banshee and not voudon_is_active:
            await self.vote(0)
            return
        if toCall.user.id in self.presetVotes:
            preset_player_vote = self.presetVotes[toCall.user.id]
            self.presetVotes[toCall.user.id] -= 1
            await self.vote(int(preset_player_vote > 0))
            return
        await message_utils.safe_send(
            global_vars.channel,
            "{}, your vote on {}.".format(
                toCall.user.mention,
                self.nominee.display_name if self.nominee else "the storytellers",
            ),
        )
        global_settings: model.settings.GlobalSettings = model.settings.GlobalSettings.load()
        default = global_settings.get_default_vote(toCall.user.id)
        if default:
            time = default[1]
            await message_utils.safe_send(toCall.user, "Will enter a {} vote in {} minutes.".format(
                ["no", "yes"][default[0]], str(int(default[1] / 60))
            ))
            for memb in global_vars.gamemaster_role.members:
                await message_utils.safe_send(
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

        # Manage hand state based on vote
        if vt == 1:  # Yes vote
            voter.hand_raised = True
        else:  # No vote
            voter.hand_raised = False
        voter.hand_locked_for_vote = True

        # Update seating order message immediately
        await global_vars.game.update_seating_order_message()

        potential_banshee = character_utils.the_ability(voter.character, model.characters.Banshee)

        # see if a Voudon is in play
        voudon_in_play = in_play_voudon()
        player_is_active_banshee = potential_banshee and voter.character.is_screaming
        # Check dead votes
        if vt == 1 and voter.is_ghost and voter.dead_votes < 1 and not (
                player_is_active_banshee and not potential_banshee.is_poisoned) and not voudon_in_play:
            if not operator:
                await message_utils.safe_send(voter.user, "You do not have any dead votes. Entering a no vote.")
                await self.vote(0)
            else:
                await message_utils.safe_send(
                    operator,
                    "{} does not have any dead votes. They must vote no. If you want them to vote yes, add a dead vote first:\n```\n@givedeadvote [player]\n```".format(
                        voter.display_name
                    ),
                )
            return
        if vt == 1 and voter.is_ghost and not (
                player_is_active_banshee and not potential_banshee.is_poisoned) and not voudon_in_play:
            await voter.remove_dead_vote()

        # On vote character powers
        for person in global_vars.game.seatingOrder:
            if isinstance(person.character, model.characters.VoteModifier):
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
            if isinstance(person.character, model.characters.VoteModifier):
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
            announcement = await message_utils.safe_send(
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
            announcement = await message_utils.safe_send(
                global_vars.channel,
                "{} votes on {} (nominated by {}): {}. No one is about to be executed.".format(
                    str(self.votes),
                    self.nominee.display_name if self.nominee else "the storytellers",
                    self.nominator.display_name if self.nominator else "the storytellers",
                    text,
                ),
            )
        else:
            announcement = await message_utils.safe_send(
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
            except discord.errors.DiscordServerError:
                print("Discord server error: ", str(msg))

        # Lower all hands and reset vote lock
        for person in global_vars.game.seatingOrder:
            person.hand_raised = False
            person.hand_locked_for_vote = False

        # Update seating order message
        await global_vars.game.update_seating_order_message()

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
        # Check dead votes
        banshee_ability = character_utils.the_ability(person.character, model.characters.Banshee)
        banshee_override = banshee_ability and banshee_ability.is_screaming
        if vt > 0 and person.is_ghost and person.dead_votes < 1 and not banshee_override:
            if not operator:
                await message_utils.safe_send(person.user, "You do not have any dead votes. Please vote no.")
            else:
                await message_utils.safe_send(
                    operator,
                    "{} does not have any dead votes. They must vote no.".format(
                        person.display_name
                    ),
                )
            return

        self.presetVotes[person.user.id] = vt

    async def cancel_preset(self, person):
        """Cancel a preset vote.

        Args:
            person: The player to cancel the preset for
        """
        if (person.user.id in self.presetVotes):
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
                pass
        self.done = True
        global_vars.game.days[-1].votes.remove(self)


# Removed: _generate_member_possibilities is now replaced with direct import


async def is_storyteller(arg, member_possibilities_fn=None, server_members=None, server=None, gamemaster_role=None):
    """Check if the argument refers to a storyteller.
    
    Args:
        arg: The argument to check
        member_possibilities_fn: Custom function for member lookup (for testing)
        server_members: Optional server members list for testing
        server: Optional server for testing
        gamemaster_role: Optional gamemaster role for testing
        
    Returns:
        True if the argument refers to a storyteller, False otherwise
    """
    # First check for direct string matches
    if arg in ["storytellers", "the storytellers", "storyteller", "the storyteller"]:
        return True

    # If no direct match, look up members
    import global_vars

    # Use provided objects or get from global_vars for testing
    _server = server if server is not None else global_vars.server
    _gamemaster_role = gamemaster_role if gamemaster_role is not None else global_vars.gamemaster_role

    # Use provided function or default to the imported one
    if member_possibilities_fn is None:
        member_possibilities_fn = player_utils.generate_possibilities

    # Use provided server_members or get from global_vars
    members = server_members if server_members is not None else _server.members

    # Generate possibilities for the provided arg
    options = await member_possibilities_fn(arg, members)

    # If no options found, return False
    if not options or len(options) != 1:
        return False

    # Get the member and check if they have the gamemaster role
    member_id = options[0].id
    member = _server.get_member(member_id)

    # Check if the member has the gamemaster role
    return _gamemaster_role in member.roles
