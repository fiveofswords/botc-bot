from types.townsfolk import Townsfolk


class Washerwoman(Townsfolk):
    # The washerwoman

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Washerwoman"
