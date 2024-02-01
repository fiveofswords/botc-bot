from characters.types.townsfolk import Townsfolk


class Balloonist(Townsfolk):
    # The balloonist

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Balloonist"
