"""
Character registry for str_to_class conversions.
"""

import inspect
from typing import Dict, Type

import model.characters.specific as specific_module
from model.characters.base import Character, Storyteller, Townsfolk, Outsider, Minion, Demon, Traveler

# Automatically build character registry by inspecting module contents
CHARACTER_REGISTRY: Dict[str, Type[Character]] = {
    'Character': Character,
    'Storyteller': Storyteller,
    'Townsfolk': Townsfolk,
    'Outsider': Outsider,
    'Minion': Minion,
    'Demon': Demon,
    'Traveler': Traveler
}

# Add base classes

# Get all classes from the specific module
for name, cls in inspect.getmembers(specific_module, inspect.isclass):
    # Only register classes that inherit from Character
    if issubclass(cls, Character) and cls is not Character:
        CHARACTER_REGISTRY[name] = cls


def str_to_class(role_name: str) -> Type[Character]:
    """Convert a string to a character class.
    
    Args:
        role_name: The name of the character class
        
    Returns:
        The character class
        
    Raises:
        AttributeError: If the character class is not found
    """
    if role_name in CHARACTER_REGISTRY:
        return CHARACTER_REGISTRY[role_name]
    raise AttributeError(f"Character class {role_name} not found")