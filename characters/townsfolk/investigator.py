from types.townsfolk import Townsfolk


class Investigator(Townsfolk):
    # The investigator

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Investigator"
