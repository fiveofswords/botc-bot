from types.townsfolk import Townsfolk


class FortuneTeller(Townsfolk):
    # The fortune teller

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Fortune Teller"
