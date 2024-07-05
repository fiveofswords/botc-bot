class Script:
    # Stores booleans for characters which modify the game rules from the script

    def __init__(self, script_list):
        self.isAtheist: bool = "atheist" in script_list
        self.isWitch: bool = "witch" in script_list
        self.list: list[str] = script_list
