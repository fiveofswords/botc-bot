from types.outsider import Outsider


class Tinker(Outsider):
    # The tinker

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Tinker"
