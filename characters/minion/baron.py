from types.minion import Minion


class Baron(Minion):
    # The baron

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Baron"
