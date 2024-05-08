from types.townsfolk import Townsfolk


class Oracle(Townsfolk):
    # The oracle

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Oracle"
