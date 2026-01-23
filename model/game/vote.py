import asyncio
import math

import global_vars
import model.characters
from model.game.base_vote import BaseVote, VoteOutcome
from utils import character_utils, player_utils


def in_play_voudon() -> model.player.Player | None:
    """Check if a Voudon is in play.

    Returns:
        The Voudon player if one is in play and not a ghost, otherwise None
    """
    return next((x for x in global_vars.game.seatingOrder if
                 character_utils.the_ability(x.character, model.characters.Voudon) and not x.is_ghost), None)


def remove_banshee_nomination(banshee_ability_of_player) -> None:
    """Remove a nomination from a Banshee.

    Args:
        banshee_ability_of_player: The Banshee ability
    """
    if banshee_ability_of_player and banshee_ability_of_player.is_screaming:
        banshee_ability_of_player.remaining_nominations -= 1


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


class Vote(BaseVote):
    """Stores information about a specific vote.
    
    Inherits all attributes from BaseVote. See BaseVote for detailed attribute documentation.
    """

    def __init__(self, nominee, nominator):
        """Initialize a Vote.
        
        Args:
            nominee: The player being nominated
            nominator: The player making the nomination
        """
        super().__init__(nominee, nominator)

        # Apply vote beginning modifiers
        for person in global_vars.game.seatingOrder:
            if isinstance(person.character, model.characters.VoteBeginningModifier):
                (
                    self.order,
                    self.values,
                    self.majority,
                ) = person.character.modify_vote_values(
                    self.order, self.values, self.majority
                )

    # Abstract method implementations
    def _get_voting_order(self) -> list['model.player.Player']:
        """Get the order of players for voting."""
        seating_order = global_vars.game.seatingOrder
        # When nominating the storyteller, just use the seating order
        if self.nominee is None:
            ordered_voters = seating_order
        else:
            nominee_index = seating_order.index(self.nominee)
            ordered_voters = seating_order[nominee_index + 1:] + seating_order[: nominee_index + 1]

        # augment order with Banshees
        order_with_banshees = []
        for person in ordered_voters:
            order_with_banshees.append(person)
            banshee_ability = character_utils.the_ability(person.character, model.characters.Banshee)
            if banshee_ability and banshee_ability.is_screaming:
                order_with_banshees.append(person)

        return order_with_banshees

    def _calculate_majority(self) -> int:
        """Calculate the majority needed for this vote type."""
        # If a Voudon is in play and alive, majority is 1 (special rule)
        if in_play_voudon():
            return 1
        living_voters = [person for person in self.order if not person.is_ghost]
        return math.ceil(len(living_voters) / 2)

    def _determine_outcome(self) -> VoteOutcome:
        """Determine the outcome of the vote (pure logic only)."""
        about_to_die: tuple[model.player.Player | None, BaseVote] | None = global_vars.game.days[-1].aboutToDie
        dies = tie = False

        if self.votes >= self.majority:
            if about_to_die is None or self.votes > about_to_die[1].votes:
                dies = True
            elif self.votes == about_to_die[1].votes:
                tie = True

        # TODO: Consider removing this logic
        # I think we should remove this logic, it's not currently used and the fact we're just looping through
        # all players in order means if we had more than one VoteModifier in play, the order is effectively arbitrary.
        for person in global_vars.game.seatingOrder:
            if isinstance(person.character, model.characters.VoteModifier):
                dies, tie = person.character.on_vote_conclusion(dies, tie)

        return VoteOutcome.PASS if dies else VoteOutcome.TIE if tie else VoteOutcome.FAIL

    def _get_outcome_message(self, outcome: VoteOutcome) -> str:
        """Get the message for a given vote outcome."""
        outcome_messages = {
            VoteOutcome.PASS: "They are about to be executed",
            VoteOutcome.TIE: "No one is about to be executed",
            VoteOutcome.FAIL: "They are not about to be executed",
        }
        return outcome_messages[outcome]

    # Hook method overrides
    async def _apply_outcome_effects(self, outcome: VoteOutcome) -> None:
        """Apply side effects based on vote outcome."""
        about_to_die: tuple[model.player.Player | None, BaseVote] | None = global_vars.game.days[-1].aboutToDie

        if outcome == VoteOutcome.PASS:
            if about_to_die is not None and about_to_die[0] is not None:
                await self._update_previous_about_to_die_message(" They are not about to be executed.")
            global_vars.game.days[-1].aboutToDie = (self.nominee, self)
        elif outcome == VoteOutcome.TIE:
            if about_to_die is not None:
                await self._update_previous_about_to_die_message(" No one is about to be executed.")
            # If the vote is a tie, we track this vote for the aboutToDie count threshold but not the nominee
            global_vars.game.days[-1].aboutToDie = (None, self)

    def _cleanup_player_state(self) -> None:
        """Clean up riot nominee state for all players."""
        for person in global_vars.game.seatingOrder:
            person.riot_nominee = False

    def _validate_vote(self, voter: 'model.player.Player', vt: int) -> tuple[bool, str]:
        """Validate if a vote is allowed."""
        potential_banshee = character_utils.the_ability(voter.character, model.characters.Banshee)
        voudon_in_play = in_play_voudon()
        player_is_active_banshee = potential_banshee and potential_banshee.is_screaming

        # Check dead votes
        if vt > 0 and voter.is_ghost and voter.dead_votes < 1 and not (
                player_is_active_banshee and not potential_banshee.is_poisoned) and not voudon_in_play:
            return False, "You do not have any dead votes. Entering a no vote."

        return True, ""

    def _apply_vote_effects(self, voter: 'model.player.Player', vt: int) -> None:
        """Apply any special effects when a vote is cast."""
        # Call parent to handle hand state and seating order update
        super()._apply_vote_effects(voter, vt)

        potential_banshee = character_utils.the_ability(voter.character, model.characters.Banshee)
        voudon_in_play = in_play_voudon()
        player_is_active_banshee = potential_banshee and potential_banshee.is_screaming

        # Use dead vote if applicable
        if vt > 0 and voter.is_ghost and not (
                player_is_active_banshee and not potential_banshee.is_poisoned) and not voudon_in_play:
            asyncio.create_task(voter.remove_dead_vote())

        # On vote character powers
        for person in global_vars.game.seatingOrder:
            if isinstance(person.character, model.characters.VoteModifier):
                person.character.on_vote()

    def _should_skip_voter(self, voter: 'model.player.Player') -> bool:
        """Check if a player should be skipped (not asked to vote)."""
        player_banshee_ability = character_utils.the_ability(voter.character, model.characters.Banshee)
        player_is_active_banshee = player_banshee_ability and player_banshee_ability.is_screaming
        voudon_is_active = in_play_voudon()

        # Call vote modifiers
        for person in global_vars.game.seatingOrder:
            if isinstance(person.character, model.characters.VoteModifier):
                person.character.on_vote_call(voter)

        # Skip ghosts without dead votes (unless they have special abilities)
        return voter.is_ghost and voter.dead_votes < 1 and not player_is_active_banshee and not voudon_is_active

    # Helper methods
    async def _update_previous_about_to_die_message(self, suffix: str) -> None:
        """Update the previous about to die message."""
        about_to_die_nom: BaseVote = global_vars.game.days[-1].aboutToDie[1]
        msg = await global_vars.channel.fetch_message(
            global_vars.game.days[-1].voteEndMessages[
                global_vars.game.days[-1].votes.index(about_to_die_nom)
            ]
        )
        await msg.edit(content=msg.content[:-31] + suffix)
