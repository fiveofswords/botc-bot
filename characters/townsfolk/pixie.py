from characters.types.townsfolk import Townsfolk


class Pixie(Townsfolk):
    # The pixie

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Pixie"
