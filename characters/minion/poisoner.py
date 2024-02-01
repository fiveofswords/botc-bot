from characters.types.minion import Minion


class Poisoner(Minion):
    # The poisoner

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Poisoner"
