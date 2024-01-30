from characters.types.townsfolk import Townsfolk


class Exorcist(Townsfolk):
    # The exorcist

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Exorcist"
