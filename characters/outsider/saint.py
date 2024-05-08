from types.outsider import Outsider


class Saint(Outsider):
    # The saint

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Saint"
