from types.outsider import Outsider


class Hatter(Outsider):
    # The hatter

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Hatter"
