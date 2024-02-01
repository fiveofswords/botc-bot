from characters.types.minion import Minion


class Vizier(Minion):
    # The vizier

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Vizier"
