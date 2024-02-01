from characters.types.townsfolk import Townsfolk


class Flowergirl(Townsfolk):
    # The flowergirl

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Flowergirl"
