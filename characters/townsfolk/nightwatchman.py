from characters.types.townsfolk import Townsfolk


class Nightwatchman(Townsfolk):
    # The nightwatchman

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Nightwatchman"
