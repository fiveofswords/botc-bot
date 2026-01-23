import math

import global_vars
import model
from model.game.base_vote import BaseVote, VoteOutcome


class TravelerVote(BaseVote):
    """Stores information about a specific call for exile.

    Inherits all attributes from BaseVote. See BaseVote for detailed attribute documentation.
    """

    # Abstract method implementations
    def _get_voting_order(self) -> list[model.player.Player]:
        """Get the order of players for voting."""
        seating_order = global_vars.game.seatingOrder
        nominee_index = seating_order.index(self.nominee)
        return seating_order[nominee_index + 1:] + seating_order[:nominee_index + 1]

    def _calculate_majority(self) -> int:
        """Calculate the majority needed for this vote type."""

        total_players = len(global_vars.game.seatingOrder)
        return math.ceil(total_players / 2)

    def _determine_outcome(self) -> VoteOutcome:
        """Determine the outcome of the vote."""
        return VoteOutcome.PASS if self.votes >= self.majority else VoteOutcome.FAIL

    def _get_outcome_message(self, outcome: VoteOutcome) -> str:
        """Get the message for a given vote outcome."""
        return "They are not exiled" if outcome == VoteOutcome.FAIL else ""
