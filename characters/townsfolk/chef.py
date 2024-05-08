from types import Townsfolk


class Chef(Townsfolk):
    # The chef

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Chef"
