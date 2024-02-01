from characters.types.townsfolk import Townsfolk


class Pacifist(Townsfolk):
    # The pacifist

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Pacifist"
