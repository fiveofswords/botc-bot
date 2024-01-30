from bot import DeathModifier
from characters.types.townsfolk import Townsfolk


class Fool(Townsfolk, DeathModifier):
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Fool"

    def refresh(self):
        super().refresh()
        self.can_escape_death = True

    def on_death(self, person, dies):
        if self.parent == person and not self.isPoisoned and self.can_escape_death and dies:
            self.can_escape_death = False
            return False
        return dies

    def on_death_priority(self):
        return DeathModifier.PROTECTS_SELF

    def extra_info(self):
        if (self.can_escape_death):
            return "Fool: Not Used"
        return "Fool: Used"
