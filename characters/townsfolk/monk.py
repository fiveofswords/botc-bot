from types.townsfolk import Townsfolk


class Monk(Townsfolk):
    # The monk

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Monk"
