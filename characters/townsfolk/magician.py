from types.townsfolk import Townsfolk


class Magician(Townsfolk):
    # The magician

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Magician"
