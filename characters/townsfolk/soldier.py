from types.townsfolk import Townsfolk


class Soldier(Townsfolk):
    # The soldier

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Soldier"
