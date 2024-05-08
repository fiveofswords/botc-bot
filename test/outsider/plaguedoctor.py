from ..outsider import Outsider


class BaseCharacter:
    # A generic character
    def __init__(self, parent):
        self.parent = parent
        self.role_name = "Character"
        self.isPoisoned = False
        self.refresh()

    def refresh(self):
        pass

    def extra_info(self):
        return ""


class Outsider(BaseCharacter):

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Outsider"


class PlagueDoctor(Outsider):
    # The plague doctor

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Plague Doctor"
