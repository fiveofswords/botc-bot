from types.townsfolk import Townsfolk


class Choirboy(Townsfolk):
    # The choirboy

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Choirboy"
