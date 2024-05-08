from types.townsfolk import Townsfolk


class Engineer(Townsfolk):
    # The engineer

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Engineer"
