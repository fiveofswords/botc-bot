class Script:
    """Stores booleans for characters which modify the game rules from the script.
    """

    _list: list[str]
    _is_atheist: bool | None = None

    def __init__(self, script_list):
        """Initialize a Script with a list of character ids.

        Args:
            script_list: List of character ids from the script creator
        """
        self._list = script_list
        self._is_atheist = "atheist" in script_list

    @property
    def is_atheist(self):
        """Whether the Atheist is on the script."""
        return self._is_atheist

    @is_atheist.setter
    def is_atheist(self, value: bool):
        """Set whether the Atheist is on the script.

        Args:
            value: True if the Atheist is on the script, False otherwise
        """
        self._is_atheist = value
