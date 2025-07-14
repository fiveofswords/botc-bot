from utils import player_utils


class WhisperMode:
    """Enum-like class for whisper modes.
    
    Defines the types of whisper modes available:
    - ALL: Can whisper to anyone
    - NEIGHBORS: Can only whisper to neighbors
    - NEIGHBORS2: Can only whisper to neighbors and their neighbors
    - STORYTELLERS: Can only whisper to storytellers
    """
    ALL = 'all'
    NEIGHBORS = 'neighbors'
    NEIGHBORS2 = 'neighbors2'
    STORYTELLERS = 'storytellers'


def to_whisper_mode(argument):
    """Convert a string to a WhisperMode.
    
    Args:
        argument: The string to convert
        
    Returns:
        The corresponding WhisperMode value, or None if not found
        
    Raises:
        AttributeError: If argument is None or not a string
    """
    if argument is None:
        raise AttributeError("Argument cannot be None")
        
    if not isinstance(argument, str):
        raise AttributeError("Argument must be a string")
        
    if WhisperMode.ALL.casefold() == argument.casefold():
        return WhisperMode.ALL
    elif WhisperMode.NEIGHBORS.casefold() == argument.casefold():
        return WhisperMode.NEIGHBORS
    elif WhisperMode.NEIGHBORS2.casefold() == argument.casefold():
        return WhisperMode.NEIGHBORS2
    elif WhisperMode.STORYTELLERS.casefold() == argument.casefold():
        return WhisperMode.STORYTELLERS
    else:
        return None


async def choose_whisper_candidates(game, author):
    """Determine which players the author can whisper to based on the current whisper mode.
    
    Args:
        game: The current game
        author: The user who wants to whisper
        
    Returns:
        List of players that the author can whisper to
    """

    if game.whisper_mode == WhisperMode.ALL:
        return game.seatingOrder + game.storytellers
    if game.whisper_mode == WhisperMode.STORYTELLERS:
        return game.storytellers
    if game.whisper_mode == WhisperMode.NEIGHBORS:
        # determine neighbors
        player_self = player_utils.get_player(author)
        author_index = game.seatingOrder.index(player_self)
        neighbor_left = game.seatingOrder[(author_index - 1) % len(game.seatingOrder)]
        neighbor_right = game.seatingOrder[(author_index + 1) % len(game.seatingOrder)]
        return [neighbor_left, player_self, neighbor_right] + game.storytellers
    if game.whisper_mode == WhisperMode.NEIGHBORS2:
        # determine neighbors and their neighbors (2 steps away)
        player_self = player_utils.get_player(author)
        author_index = game.seatingOrder.index(player_self)
        seating_length = len(game.seatingOrder)

        # Get players within 2 steps in each direction
        candidates = set()
        for i in range(-2, 3):  # -2, -1, 0, 1, 2
            candidate_index = (author_index + i) % seating_length
            candidates.add(game.seatingOrder[candidate_index])
        
        return list(candidates) + game.storytellers
    return []
