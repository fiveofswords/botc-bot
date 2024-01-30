from characters.types.townsfolk import Townsfolk


class Undertaker(Townsfolk):
    # The undertaker

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Undertaker"
