from characters.types.minion import Minion


class Widow(Minion):
    # The widow

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Widow"
