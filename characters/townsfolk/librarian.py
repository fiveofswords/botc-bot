from types.townsfolk import Townsfolk


class Librarian(Townsfolk):
    # The librarian

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Librarian"
