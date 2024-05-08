from types.townsfolk import Townsfolk


class BountyHunter(Townsfolk):
    # The bounty hunter

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Bounty Hunter"
