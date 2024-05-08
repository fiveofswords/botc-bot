from types.townsfolk import Townsfolk


class Ravenkeeper(Townsfolk):
    # The ravenkeeper

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Ravenkeeper"
