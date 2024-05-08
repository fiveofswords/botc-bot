from types.townsfolk import Townsfolk


class TownCrier(Townsfolk):
    # The town crier

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Town Crier"
