"""Utilities for character-related functionality."""


def the_ability(character, ability_class):
    """Get an ability from a character if it has that ability.
    
    Args:
        character: The character to check
        ability_class: The ability class to check for
        
    Returns:
        The ability instance if found, otherwise None
    """
    # Check if character has the abilities attribute
    if hasattr(character, 'abilities'):
        for ability in character.abilities:
            # Try checking if ability is an instance of ability_class
            try:
                if isinstance(ability, ability_class):
                    return ability
            except TypeError:
                # If ability_class is not a type, just compare them directly
                # This is mainly for test mocks
                if ability == ability_class:
                    return ability

    # If character itself is an instance of the ability class
    try:
        if isinstance(character, ability_class):
            return character
    except TypeError:
        # If ability_class is not a type, just compare them directly
        # This is mainly for test mocks
        if character == ability_class:
            return character

    # If character is AbilityModifier, check its abilities
    if hasattr(character, 'abilities') and hasattr(character, 'parent'):
        matching = [the_ability(c, ability_class) for c in character.abilities]
        # Get the first one
        first = next((x for x in matching if x is not None), None)
        return first

    return None


def has_ability(character, ability_class):
    """Check if a character has a specific ability.
    
    Args:
        character: The character to check
        ability_class: The ability class to check for
        
    Returns:
        bool: Whether the character has the ability
    """
    return the_ability(character, ability_class) is not None
