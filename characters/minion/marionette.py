from characters.types.minion import Minion


class Marionette(Minion):
    # The marionette

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Marionette"
