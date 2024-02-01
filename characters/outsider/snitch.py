from characters.types.outsider import Outsider


class Snitch(Outsider):
    # The snitch

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Snitch"
