"""
Tests for the character registry.
"""

import pytest

from model.characters import (
    Character, Storyteller,
    CHARACTER_REGISTRY, str_to_class
)
from model.characters.specific import Chef, Drunk, Poisoner, Imp, Beggar


class TestCharacterRegistry:
    """Tests for the character registry."""

    def test_registry_contains_base_classes(self):
        """Test that the registry contains the base classes."""
        assert CHARACTER_REGISTRY['Character'] == Character
        assert CHARACTER_REGISTRY['Storyteller'] == Storyteller

    def test_registry_contains_specific_classes(self):
        """Test that the registry contains specific character classes."""
        # Test one character from each alignment
        assert CHARACTER_REGISTRY['Chef'] == Chef
        assert CHARACTER_REGISTRY['Drunk'] == Drunk
        assert CHARACTER_REGISTRY['Poisoner'] == Poisoner
        assert CHARACTER_REGISTRY['Imp'] == Imp
        assert CHARACTER_REGISTRY['Beggar'] == Beggar

    def test_str_to_class_valid(self):
        """Test that str_to_class correctly converts valid strings."""
        assert str_to_class('Character') == Character
        assert str_to_class('Chef') == Chef
        assert str_to_class('Drunk') == Drunk
        assert str_to_class('Poisoner') == Poisoner
        assert str_to_class('Imp') == Imp
        assert str_to_class('Beggar') == Beggar

    def test_str_to_class_invalid(self):
        """Test that str_to_class raises AttributeError for invalid strings."""
        with pytest.raises(AttributeError):
            str_to_class('NonexistentCharacter')

    def test_all_specific_characters_are_registered(self):
        """Test that all specific character classes are registered."""
        # Test a representative character from each alignment type
        import inspect
        from model.characters import specific
        
        for name, cls in inspect.getmembers(specific, inspect.isclass):
            # Check if it inherits from Character and is not a base alignment class
            from model.characters import Character, Townsfolk, Outsider, Minion, Demon, Traveler
            base_classes = (Character, Townsfolk, Outsider, Minion, Demon, Traveler)
            
            if issubclass(cls, Character) and cls not in base_classes:
                assert name in CHARACTER_REGISTRY
                assert CHARACTER_REGISTRY[name] == cls