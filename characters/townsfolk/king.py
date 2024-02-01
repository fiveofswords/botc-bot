from characters.types.townsfolk import Townsfolk


class King(Townsfolk):
    # The king

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "King"
