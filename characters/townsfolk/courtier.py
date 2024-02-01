from characters.types.townsfolk import Townsfolk


class Courtier(Townsfolk):
    # The courtier

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Courtier"
