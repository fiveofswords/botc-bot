from types.outsider import Outsider


class Goon(Outsider):
    # The goon

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Goon"
