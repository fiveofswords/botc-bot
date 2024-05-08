from types.outsider import Outsider


class Politician(Outsider):
    # The politician

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Politician"
