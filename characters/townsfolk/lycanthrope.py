from types.townsfolk import Townsfolk


class Lycanthrope(Townsfolk):
    # The lycanthrope

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Lycanthrope"
