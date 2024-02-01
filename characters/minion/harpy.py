from characters.types.minion import Minion


class Harpy(Minion):
    # The harpy

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Harpy"
