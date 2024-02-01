from characters.types.townsfolk import Townsfolk


class Mathematician(Townsfolk):
    # The mathematician

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Mathematician"
