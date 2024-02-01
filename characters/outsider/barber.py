from characters.types.outsider import Outsider


class Barber(Outsider):
    # The barber

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Barber"
