from types.townsfolk import Townsfolk


class Dreamer(Townsfolk):
    # The dreamer

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Dreamer"
