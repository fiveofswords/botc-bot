from ..basecharacter import BaseCharacter


class Townsfolk(BaseCharacter):
    # A generic townsfolk

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Townsfolk"
