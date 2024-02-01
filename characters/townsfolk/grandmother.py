from characters.types.townsfolk import Townsfolk


class Grandmother(Townsfolk):
    # The grandmother

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Grandmother"
