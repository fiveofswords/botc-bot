from types.townsfolk import Townsfolk


class Steward(Townsfolk):
    # The steward

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Steward"
