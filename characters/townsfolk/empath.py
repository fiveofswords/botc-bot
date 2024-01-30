from ..types.townsfolk import Townsfolk


class Empath(Townsfolk):
    # The empath

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Empath"
