from types.outsider import Outsider


class Mutant(Outsider):
    # The mutant

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Mutant"
