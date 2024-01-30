from characters.types.townsfolk import Townsfolk


class Mayor(Townsfolk):
    # The mayor

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Mayor"
