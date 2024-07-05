from typing import Any


class Character:
    # A generic character
    def __init__(self, parent: Any) -> None:
        self.parent: Any = parent
        self.role_name: str = "Character"
        self._is_poisoned: bool = False
        self.refresh()

    def refresh(self) -> None:
        pass

    def extra_info(self) -> str:
        return ""

    @property
    def is_poisoned(self) -> bool:
        return self._is_poisoned

    def poison(self) -> None:
        self._is_poisoned = True

    def unpoison(self) -> None:
        self._is_poisoned = False
