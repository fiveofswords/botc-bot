from types.outsider import Outsider


class Butler(Outsider):
    # The butler

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Butler"
