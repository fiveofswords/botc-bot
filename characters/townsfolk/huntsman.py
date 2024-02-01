from characters.types.townsfolk import Townsfolk


class Huntsman(Townsfolk):
    # The huntsman

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Huntsman"
