from characters.types.outsider import Outsider


class Lunatic(Outsider):
    # The lunatic

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Lunatic"
