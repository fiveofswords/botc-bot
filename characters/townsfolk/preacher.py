from types.townsfolk import Townsfolk


class Preacher(Townsfolk):
    # The preacher

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Preacher"
