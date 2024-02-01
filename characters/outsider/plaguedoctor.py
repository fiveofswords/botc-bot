from characters.types.outsider import Outsider


class PlagueDoctor(Outsider):
    # The plague doctor

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Plague Doctor"
