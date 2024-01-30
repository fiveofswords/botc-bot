from characters.types.townsfolk import Townsfolk


class Slayer(Townsfolk):
    # The slayer

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Slayer"
