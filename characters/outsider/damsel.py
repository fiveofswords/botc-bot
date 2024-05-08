from types.outsider import Outsider


class Damsel(Outsider):
    # The damsel

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Damsel"
