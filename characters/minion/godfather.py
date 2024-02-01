from characters.types.minion import Minion


class Godfather(Minion):
    # The godfather

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Godfather"
