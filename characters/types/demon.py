from ..basecharacter import BaseCharacter

class Demon(BaseCharacter):
    # A generic demon

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Demon"
