from types.minion import Minion


class Fearmonger(Minion):
    # The fearmonger

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Fearmonger"
