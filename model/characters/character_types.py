from __future__ import annotations
from model.characters import Character

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bot import Player


class Townsfolk(Character):
    """A generic townsfolk"""

    def __init__(self, parent: Player):
        super().__init__(parent)
        self.role_name = "Townsfolk"


class Outsider(Character):
    """A generic outsider"""

    def __init__(self, parent: Player):
        super().__init__(parent)
        self.role_name = "Outsider"


class Minion(Character):
    """A generic minion"""

    def __init__(self, parent: Player):
        super().__init__(parent)
        self.role_name = "Minion"


class Demon(Character):
    """A generic demon"""

    def __init__(self, parent: Player):
        super().__init__(parent)
        self.role_name = "Demon"
