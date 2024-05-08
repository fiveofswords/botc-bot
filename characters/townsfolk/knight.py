from types.townsfolk import Townsfolk


class Knight(Townsfolk):
    # The knight

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Knight"
