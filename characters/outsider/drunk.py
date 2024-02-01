from characters.types.outsider import Outsider


class Drunk(Outsider):
    # The drunk

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Drunk"
