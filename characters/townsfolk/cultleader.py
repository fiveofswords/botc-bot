from characters.types.townsfolk import Townsfolk


class CultLeader(Townsfolk):
    # The cult leader

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Cult Leader"
