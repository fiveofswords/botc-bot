from types.townsfolk import Townsfolk


class Shugenja(Townsfolk):
    # The shugenja

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Shugenja"
