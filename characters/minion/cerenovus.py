from types.minion import Minion


class Cerenovus(Minion):
    # The cerenovus

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Cerenovus"
