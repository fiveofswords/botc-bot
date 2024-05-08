from basecharacter import BaseCharacter

class Outsider(BaseCharacter):

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Outsider"
