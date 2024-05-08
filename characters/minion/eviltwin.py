from types.minion import Minion


class EvilTwin(Minion):
    # The evil twin

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Evil Twin"
