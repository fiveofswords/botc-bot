from bot import DeathModifier
from characters.types.townsfolk import Townsfolk


class Sailor(Townsfolk, DeathModifier):
    # The sailor

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Sailor"

    def on_death(self, person, dies):
        if self.parent == person and not self.isPoisoned:
            return False
        return dies

    def on_death_priority(self):
        return DeathModifier.PROTECTS_SELF
