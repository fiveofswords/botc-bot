from characters.types.townsfolk import Townsfolk


class VillageIdiot(Townsfolk):
    # The village idiot

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Village Idiot"
