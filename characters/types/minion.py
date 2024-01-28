from ..basecharacter import BaseCharacter


class Minion(BaseCharacter):
    # A generic minion

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Minion"
