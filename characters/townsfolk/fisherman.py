from characters.types.townsfolk import Townsfolk


class Fisherman(Townsfolk):
    # The fisherman

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Fisherman"
