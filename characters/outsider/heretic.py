from types.outsider import Outsider


class Heretic(Outsider):
    # The heretic

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Heretic"
