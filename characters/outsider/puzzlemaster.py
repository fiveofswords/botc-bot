from characters.types.outsider import Outsider


class Puzzlemaster(Outsider):
    # The puzzlemaster

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Puzzlemaster"
