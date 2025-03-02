class Script:
    """Stores booleans for characters which modify the game rules from the script.
    """

    def __init__(self, script_list):
        """Initialize a Script with a list of character ids.

        Args:
            script_list: List of character ids from the script creator
        """
        self._list = script_list

    @property
    def is_atheist(self):
        """Whether the Atheist is on the script."""
        return "atheist" in self._list

    @property
    def is_witch(self):
        """Whether the Witch is on the script."""
        return "witch" in self._list

    @property
    def list(self):
        """The list of character ids from the script."""
        return self._list
