from characters.types.townsfolk import Townsfolk


class Juggler(Townsfolk):
    # The juggler

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Juggler"
