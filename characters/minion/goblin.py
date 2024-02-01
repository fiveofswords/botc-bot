from characters.types.minion import Minion


class Goblin(Minion):
    # The goblin

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Goblin"
