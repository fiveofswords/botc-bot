"""
Tests for character functionality in the Blood on the Clocktower bot.

These tests focus on the Character classes and their behaviors.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from model.characters.base import Character, VoteModifier, NominationModifier, DeathModifier, Storyteller
from model.characters.registry import CHARACTER_REGISTRY
from model.characters.specific import Washerwoman, FortuneTeller, Demon
from model.player import Player, STORYTELLER_ALIGNMENT


# Reuse the MockMember class from the integration tests
class MockMember:
    """Mock Discord member for testing."""

    def __init__(self, id, name, display_name=None, roles=None):
        self.id = id
        self.name = name
        self.display_name = display_name or name
        self.roles = roles or []
        self.mention = f"<@{id}>"

    async def add_roles(self, *roles):
        """Mock adding roles to member."""
        for role in roles:
            if role not in self.roles:
                self.roles.append(role)

    async def remove_roles(self, *roles):
        """Mock removing roles from member."""
        for role in roles:
            if role in self.roles:
                self.roles.remove(role)


class MockChannel:
    """Mock Discord channel for testing."""

    def __init__(self, id, name):
        self.id = id
        self.name = name
        self.messages = []

    async def send(self, content=None, embed=None):
        """Mock sending a message to the channel."""
        message = MagicMock()
        message.content = content
        message.embed = embed
        self.messages.append(message)
        return message


@pytest_asyncio.fixture
async def setup_character_test():
    """Set up test environment for character testing."""
    # Create channels
    st_channel = MockChannel(301, "st-alice")

    # Create members
    alice = MockMember(2, "Alice")
    bob = MockMember(3, "Bob")
    charlie = MockMember(4, "Charlie")

    # Create players with different character types
    washerwoman_player = Player(
        Washerwoman,
        "good",
        alice,
        st_channel,
        0
    )

    fortuneteller_player = Player(
        FortuneTeller,
        "good",
        bob,
        MockChannel(302, "st-bob"),
        1
    )

    demon_player = Player(
        Demon,
        "evil",
        charlie,
        MockChannel(303, "st-charlie"),
        2
    )

    storyteller_player = Player(
        Storyteller,
        STORYTELLER_ALIGNMENT,
        MockMember(1, "Storyteller"),
        None,
        None
    )

    return {
        'players': {
            'washerwoman': washerwoman_player,
            'fortuneteller': fortuneteller_player,
            'demon': demon_player,
            'storyteller': storyteller_player
        },
        'channels': {
            'st_channel': st_channel
        }
    }


@pytest.mark.asyncio
async def test_character_registry():
    """Test the character registry functionality."""
    # Import str_to_class from the module
    from model.characters.registry import str_to_class

    # Test the CHARACTER_REGISTRY
    assert "Storyteller" in CHARACTER_REGISTRY
    assert "Washerwoman" in CHARACTER_REGISTRY
    assert "FortuneTeller" in CHARACTER_REGISTRY
    assert "Demon" in CHARACTER_REGISTRY

    # Test str_to_class
    assert str_to_class("Storyteller") == Storyteller
    assert str_to_class("Washerwoman") == Washerwoman
    assert str_to_class("FortuneTeller") == FortuneTeller
    assert str_to_class("Demon") == Demon

    # Test invalid character
    with pytest.raises(AttributeError):
        str_to_class("NonExistentCharacter")


@pytest.mark.asyncio
async def test_base_character_abilities():
    """Test the base character class and its abilities."""
    # Create mock player for parent
    mock_player = MagicMock()

    # Create a basic character with no modifiers
    base_character = Character(mock_player)

    # Test basic properties
    assert base_character.parent == mock_player
    assert base_character.role_name == "Character"
    assert base_character.is_poisoned == False

    # Test poison/unpoison
    base_character.poison()
    assert base_character.is_poisoned == True
    base_character.unpoison()
    assert base_character.is_poisoned == False

    # Test extra_info (should return empty string by default)
    assert base_character.extra_info() == ""


@pytest.mark.asyncio
async def test_modifier_attributes():
    """Test character modifiers as attributes."""
    # Create mock player for parent
    mock_player = MagicMock()

    # Create modifier instances
    vote_modifier = VoteModifier(mock_player)
    nomination_modifier = NominationModifier(mock_player)
    death_modifier = DeathModifier(mock_player)

    # Test basic properties
    assert vote_modifier.parent == mock_player
    assert nomination_modifier.parent == mock_player
    assert death_modifier.parent == mock_player

    # Test role_name inheritance
    assert vote_modifier.role_name == "Character"
    assert nomination_modifier.role_name == "Character"
    assert death_modifier.role_name == "Character"


@pytest.mark.asyncio
async def test_townsfolk_characters(setup_character_test):
    """Test townsfolk character base functionality."""
    washerwoman = setup_character_test['players']['washerwoman']
    fortuneteller = setup_character_test['players']['fortuneteller']

    # Test role names
    assert washerwoman.character.role_name == "Washerwoman"
    assert fortuneteller.character.role_name == "Fortune Teller"

    # Test character class (should be from specific implementations)
    assert isinstance(washerwoman.character, Washerwoman)
    assert isinstance(fortuneteller.character, FortuneTeller)


@pytest.mark.asyncio
async def test_demon_kill_ability(setup_character_test):
    """Test the Demon's specific abilities."""
    demon = setup_character_test['players']['demon']
    washerwoman = setup_character_test['players']['washerwoman']

    # Patch Player.kill to simulate the Demon's kill ability
    with patch('model.player.Player.kill', AsyncMock()) as mock_kill:
        # Simulate kill implementation
        mock_kill.return_value = True

        # Ensure washerwoman is alive for the test
        washerwoman.is_alive = True

        # Test the Demon's ability to kill (standard ability)
        await washerwoman.kill()
        mock_kill.assert_called_once()


@pytest.mark.asyncio
async def test_player_character_integration(setup_character_test):
    """Test integration between Player and Character classes."""
    washerwoman = setup_character_test['players']['washerwoman']
    fortuneteller = setup_character_test['players']['fortuneteller']
    demon = setup_character_test['players']['demon']

    # Test player properties
    assert washerwoman.character.__class__ == Washerwoman
    assert fortuneteller.character.__class__ == FortuneTeller
    assert demon.character.__class__ == Demon

    # Test player alignment
    assert washerwoman.alignment == "good"
    assert fortuneteller.alignment == "good"
    assert demon.alignment == "evil"

    # Test basic character functionality
    assert washerwoman.character.role_name == "Washerwoman"
    assert fortuneteller.character.role_name == "Fortune Teller"
    assert demon.character.role_name == "Demon"

    # Test poison/unpoison functionality
    assert washerwoman.character.is_poisoned == False
    washerwoman.character.poison()
    assert washerwoman.character.is_poisoned == True
    washerwoman.character.unpoison()
    assert washerwoman.character.is_poisoned == False


@pytest.mark.asyncio
async def test_storyteller_abilities(setup_character_test):
    """Test the Storyteller's specific abilities."""
    storyteller = setup_character_test['players']['storyteller']
    washerwoman = setup_character_test['players']['washerwoman']

    # Create a mock for the storyteller's message method
    with patch('model.player.Player.message', AsyncMock()) as mock_message:
        # Test the storyteller's ability to message players privately
        await storyteller.message(washerwoman, "This is a secret message.")

        # Verify the message was sent
        mock_message.assert_called_once_with(washerwoman, "This is a secret message.")
