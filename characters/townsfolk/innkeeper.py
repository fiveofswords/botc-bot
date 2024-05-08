from types.townsfolk import Townsfolk


class Innkeeper(Townsfolk):
    # The innkeeper

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Innkeeper"
