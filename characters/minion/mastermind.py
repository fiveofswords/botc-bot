from types.minion import Minion


class Mastermind(Minion):
    # The mastermind

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Mastermind"
