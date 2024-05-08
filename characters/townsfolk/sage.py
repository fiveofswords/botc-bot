from types.townsfolk import Townsfolk


class Sage(Townsfolk):
    # The sage

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Sage"
