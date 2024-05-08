from types.minion import Minion


class Psychopath(Minion):
    # The psychopath

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Psychopath"
