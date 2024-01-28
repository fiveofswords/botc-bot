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
