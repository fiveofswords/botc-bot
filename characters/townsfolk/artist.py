from types.townsfolk import Townsfolk


class Artist(Townsfolk):
    # The artist

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Artist"
