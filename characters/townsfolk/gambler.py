from types.townsfolk import Townsfolk


class Gambler(Townsfolk):
    # The gambler

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Gambler"
