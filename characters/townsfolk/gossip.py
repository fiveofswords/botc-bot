from types.townsfolk import Townsfolk


class Gossip(Townsfolk):
    # The gossip

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Gossip"
