from characters.types.townsfolk import Townsfolk


class Professor(Townsfolk):
    # The professor

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Professor"
