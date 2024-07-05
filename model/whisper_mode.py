from typing import Optional


class WhisperMode:
    ALL = 'all'
    NEIGHBORS = 'neighbors'
    STORYTELLERS = 'storytellers'

    @staticmethod
    def to_whisper_mode(argument: str) -> Optional[str]:
        if WhisperMode.ALL.casefold() == argument.casefold():
            new_mode = WhisperMode.ALL
        elif WhisperMode.NEIGHBORS.casefold() == argument.casefold():
            new_mode = WhisperMode.NEIGHBORS
        elif WhisperMode.STORYTELLERS.casefold() == argument.casefold():
            new_mode = WhisperMode.STORYTELLERS
        else:
            new_mode = None
        return new_mode
