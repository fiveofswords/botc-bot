from types.townsfolk import Townsfolk


class Farmer(Townsfolk):
    # The farmer

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Farmer"
