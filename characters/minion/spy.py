from types.minion import Minion


class Spy(Minion):
    # The spy

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Spy"
