from types.townsfolk import Townsfolk


class Clockmaker(Townsfolk):
    # The clockmaker

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Clockmaker"
