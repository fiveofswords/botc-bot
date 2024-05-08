from types.townsfolk import Townsfolk


class Chambermaid(Townsfolk):
    # The chambermaid

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Chambermaid"
