from characters.types.townsfolk import Townsfolk


class SnakeCharmer(Townsfolk):
    # The snake charmer

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Snake Charmer"
