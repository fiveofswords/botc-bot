from characters.types.townsfolk import Townsfolk


class Atheist(Townsfolk):
    # The atheist

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Atheist"
