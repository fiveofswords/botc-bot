from characters.types.townsfolk import Townsfolk


class Savant(Townsfolk):
    # The savant

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Savant"
