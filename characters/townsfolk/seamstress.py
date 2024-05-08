from types.townsfolk import Townsfolk


class Seamstress(Townsfolk):
    # The seamstress

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Seamstress"
