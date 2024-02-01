from characters.types.townsfolk import Townsfolk


class HighPriestess(Townsfolk):
    # The high priestess

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "High Priestess"
