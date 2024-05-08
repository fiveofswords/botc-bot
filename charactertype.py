from characters.basecharacter import BaseCharacter

class Townsfolk(BaseCharacter):
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Townsfolk"


class Outsider(BaseCharacter):
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Outsider"


class Minion(BaseCharacter):
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Minion"


class Demon(BaseCharacter):
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Demon"
