from characters.types.townsfolk import Townsfolk


class Noble(Townsfolk):
    # The noble

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Noble"
