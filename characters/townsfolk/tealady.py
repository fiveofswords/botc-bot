from bot import DeathModifier
from characters.types.townsfolk import Townsfolk


class TeaLady(Townsfolk, DeathModifier):
    # The tea lady

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Tea Lady"

    def on_death(self, person, dies):
        # look left for living neighbor
        if not dies:
            return dies
        player_count = len(game.seatingOrder)
        ccw = self.parent.position - 1
        neighbor1 = game.seatingOrder[ccw]
        while neighbor1.isGhost:
            ccw = ccw - 1
            neighbor1 = game.seatingOrder[ccw]

        # look right for living neighbor
        cw = self.parent.position + 1 - player_count
        neighbor2 = game.seatingOrder[cw]
        while neighbor2.isGhost:
            cw = cw + 1
            neighbor2 = game.seatingOrder[cw]

        if (
            # fixme: This does not consider neighbors who may falsely register as good or evil (recluse/spy)
            neighbor1.alignment == "good"
            and neighbor2.alignment == "good"
            and (person == neighbor1 or person == neighbor2)
            and not self.isPoisoned
        ):
            return False
        return dies

    def on_death_priority(self):
        return DeathModifier.PROTECTS_OTHERS
