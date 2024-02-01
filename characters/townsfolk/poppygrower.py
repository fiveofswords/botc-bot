from characters.types.townsfolk import Townsfolk


class PoppyGrower(Townsfolk):
    # The poppy grower

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Poppy Grower"
