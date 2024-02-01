from characters.types.outsider import Outsider


class Klutz(Outsider):
    # The klutz

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Klutz"
