class WhisperMode:
    """Enum-like class for whisper modes.
    
    Defines the types of whisper modes available:
    - ALL: Can whisper to anyone
    - NEIGHBORS: Can only whisper to neighbors
    - STORYTELLERS: Can only whisper to storytellers
    """
    ALL = 'all'
    NEIGHBORS = 'neighbors'
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
    elif WhisperMode.STORYTELLERS.casefold() == argument.casefold():
        return WhisperMode.STORYTELLERS
    else:
        return None


async def chose_whisper_candidates(game, author):
    """Determine which players the author can whisper to based on the current whisper mode.
    
    Args:
        game: The current game
        author: The user who wants to whisper
        
    Returns:
        List of players that the author can whisper to
    """
    from bot_impl import get_player

    if game.whisper_mode == WhisperMode.ALL:
        return game.seatingOrder + game.storytellers
    if game.whisper_mode == WhisperMode.STORYTELLERS:
        return game.storytellers
    if game.whisper_mode == WhisperMode.NEIGHBORS:
        # determine neighbors
        player_self = await get_player(author)
        author_index = game.seatingOrder.index(player_self)
        neighbor_left = game.seatingOrder[(author_index - 1) % len(game.seatingOrder)]
        neighbor_right = game.seatingOrder[(author_index + 1) % len(game.seatingOrder)]
        return [neighbor_left, player_self, neighbor_right] + game.storytellers
    return []
