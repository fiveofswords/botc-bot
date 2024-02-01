from characters.types.townsfolk import Townsfolk


class Minstrel(Townsfolk):
    # The minstrel

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Minstrel"
