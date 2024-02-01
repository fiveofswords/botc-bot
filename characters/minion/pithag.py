from characters.types.minion import Minion


class PitHag(Minion):
    # The pit-hag

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Pit-Hag"
