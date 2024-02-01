from characters.types.townsfolk import Townsfolk


class General(Townsfolk):
    # The general

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "General"
