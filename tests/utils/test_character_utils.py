"""Tests for character_utils module that handles ability lookups and checks."""

from unittest.mock import Mock

from model.characters.base import DeathModifier
from model.characters.specific import Fool, Virgin, TeaLady, Sailor, Philosopher
from utils.character_utils import the_ability, has_ability


class TestTheAbility:
    """Tests for the_ability function which retrieves ability instances from characters."""

    def test_character_with_abilities(self):
        """Test that a specific ability can be retrieved from a character's abilities list."""
        # Set up a Philosopher character with a Fool ability
        parent = Mock()
        philosopher = Philosopher(parent)
        fool = Fool(parent)
        philosopher.add_ability(Fool)  # Adds Fool to philosopher's abilities

        # When we search for the Fool ability
        result = the_ability(philosopher, Fool)

        # Then we should get the added Fool instance
        assert isinstance(result, Fool)
        assert result in philosopher.abilities

    def test_character_without_abilities_attribute(self):
        """Test that the_ability returns None when character has no abilities attribute."""
        # Set up a character mock without an abilities attribute
        ability_class = DeathModifier
        character = Mock(spec=[])  # No abilities attribute

        # When we try to find an ability on a character without abilities
        result = the_ability(character, ability_class)

        # Then the result should be None
        assert result is None

    def test_character_is_ability(self):
        """Test that the_ability returns the character itself when it's an instance of the ability class."""
        # Set up a Sailor which is also a DeathModifier
        parent = Mock()
        sailor = Sailor(parent)  # Sailor is also a DeathModifier

        # When we search for the DeathModifier ability
        result = the_ability(sailor, DeathModifier)

        # Then the sailor itself should be returned as it is a DeathModifier
        assert result is sailor

    def test_string_comparison_fallback(self):
        """Test that the_ability falls back to string comparison when using mock objects."""
        # Set up a character with abilities including a string
        ability_class = "Sailor"
        ability = "Sailor"
        character = Mock()
        character.abilities = [Mock(), ability, Mock()]

        # When we search for an ability using a string name
        result = the_ability(character, ability_class)

        # Then it should find the ability via string comparison
        assert result == ability

    def test_character_is_ability_string_comparison(self):
        """Test that the_ability uses string comparison when both character and ability are strings."""
        # Set up string representations
        ability_class = "TestAbility"
        character = "TestAbility"

        # When we compare strings directly
        result = the_ability(character, ability_class)

        # Then the result should match if the strings are equal
        assert result == character

    def test_ability_modifier_with_abilities(self):
        """Test that the_ability can find abilities added to an AbilityModifier."""
        # Set up a Philosopher (an AbilityModifier)
        parent = Mock()
        philosopher = Philosopher(parent)

        # When we search before adding the ability
        result1 = the_ability(philosopher, Fool)

        # And then add the ability and search again
        philosopher.add_ability(Fool)
        result2 = the_ability(philosopher, Fool)

        # Then we should find nothing initially, but find the ability after adding it
        assert result1 is None
        assert isinstance(result2, Fool)


class TestHasAbility:
    """Tests for has_ability function which checks if a character has a specific ability."""

    def test_has_ability_true(self):
        """Test that has_ability returns True when character has the requested ability."""
        # Set up a Sailor which is a DeathModifier
        parent = Mock()
        sailor = Sailor(parent)  # Sailor inherits from DeathModifier

        # When we check if it has the DeathModifier ability
        result = has_ability(sailor, DeathModifier)

        # Then the result should be True
        assert result is True

    def test_has_ability_false(self):
        """Test that has_ability returns False when character does not have the requested ability."""
        # Set up a Virgin which is not a DeathModifier
        parent = Mock()
        virgin = Virgin(parent)  # Virgin does not inherit from DeathModifier

        # When we check if it has the DeathModifier ability
        result = has_ability(virgin, DeathModifier)

        # Then the result should be False
        assert result is False

    def test_has_ability_with_nested_abilities(self):
        """Test that has_ability finds abilities nested within an AbilityModifier character."""
        # Set up a Philosopher which can contain other abilities
        parent = Mock()
        philosopher = Philosopher(parent)

        # When we check before adding an ability
        result1 = has_ability(philosopher, TeaLady)

        # And then add the ability and check again
        philosopher.add_ability(TeaLady)
        result2 = has_ability(philosopher, TeaLady)

        # Then we should get False initially and True after adding it
        assert result1 is False
        assert result2 is True
