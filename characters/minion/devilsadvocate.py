from types.minion import Minion


class DevilsAdvocate(Minion):
    # The devil's advocate

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Devil's Advocate"
