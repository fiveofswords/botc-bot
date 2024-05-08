from bot import VoteBeginningModifier, DayEndModifier
from types.townsfolk import Townsfolk


class Amnesiac(Townsfolk, VoteBeginningModifier, DayEndModifier):
    # The amnesiac

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Amnesiac"
        self.vote_mod = 1
        self.player_with_votes = None

    def extra_info(self):
        if self.player_with_votes and self.vote_mod != 1:
            return "{} votes times {}".format(self.player_with_votes.nick, self.vote_mod)
        return super().extra_info()

    def modify_vote_values(self, order, values, majority):
        if self.player_with_votes and not self.isPoisoned and not self.parent.isGhost:
            values[self.player_with_votes] = (values[self.player_with_votes][0], values[self.player_with_votes][1] * self.vote_mod)

        return order, values, majority

    def enhance_votes(self, player, multiplier):
        self.player_with_votes = player
        self.vote_mod = multiplier

    def on_day_end(self):
        self.vote_mod = 1
        self.player_with_votes = None
        super().on_day_end()
