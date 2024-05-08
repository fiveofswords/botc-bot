from types.outsider import Outsider


class Acrobat(Outsider):
    # The acrobat

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Acrobat"
