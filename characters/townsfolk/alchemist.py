from bot import AbilityModifier
from characters.types.townsfolk import Townsfolk


class Alchemist(Townsfolk, AbilityModifier):
    # The alchemist

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Alchemist"

    def extra_info(self):
        return "\n".join([("Alchemy: {}\n{}".format(x.role_name, x.extra_info())) for x in self.abilities])

    def add_ability(self, role):
        is_set = False
        for ability in self.abilities:
            if isinstance(ability, AbilityModifier):
                ability.add_ability(role)
                is_set = True
        if not is_set:
            self.abilities = [role(self.parent)]
