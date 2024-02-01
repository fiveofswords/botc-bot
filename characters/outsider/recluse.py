from characters.types.outsider import Outsider


class Recluse(Outsider):
    # The recluse

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Recluse"
