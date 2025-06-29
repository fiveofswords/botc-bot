"""
Utility functions for text processing and manipulation.
"""

from typing import Generator


def str_cleanup(text: str, chars: list[str]) -> str:
    """
    Cleanup a string by splitting on specified characters and capitalizing each part.
    
    Args:
        text: The text to clean up
        chars: List of characters to split on
        
    Returns:
        The cleaned up string with each part capitalized
    """
    parts = [text]
    for char in chars:
        new_parts = []
        for part in parts:
            for sub_part in part.split(char):
                new_parts.append(sub_part)
        parts = new_parts
    return "".join([part.capitalize() for part in parts])


def find_all(pattern: str, text: str) -> Generator[int, None, None]:
    """
    Find all occurrences of a pattern in text.
    
    Args:
        pattern: The pattern to search for
        text: The text to search in
        
    Yields:
        The index of each occurrence
    """
    i = text.find(pattern)
    while i != -1:
        yield i
        i = text.find(pattern, i + 1)
