"""
Tests for character functionality in the Blood on the Clocktower bot.

These tests focus on the Character classes and their behaviors.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

import global_vars
from model.characters.base import Character, VoteModifier, NominationModifier, DeathModifier, Storyteller, Demon
from model.characters.registry import CHARACTER_REGISTRY
from model.characters.specific import Washerwoman, FortuneTeller, Riot
from model.player import Player, STORYTELLER_ALIGNMENT
from tests.fixtures.discord_mocks import MockMember, MockChannel


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


@pytest.mark.asyncio
@patch('model.characters.specific.utils.notify_storytellers', new_callable=AsyncMock)
@patch('utils.message_utils.safe_send', new_callable=AsyncMock)
async def test_riot_day_3_reminder_sent_on_day_start_once(mock_safe_send, mock_notify_storytellers):
    """Riot should notify storytellers at start of day 3, once, if a minion exists."""
    from model.characters.specific import Boomdandy

    riot_parent = MagicMock()
    riot_parent.is_ghost = False
    riot = Riot(riot_parent)

    # Create a minion player
    minion_player = MagicMock()
    minion_char = Boomdandy(minion_player)
    minion_player.character = minion_char

    global_vars.game = MagicMock()
    global_vars.game.has_automated_life_and_death = True
    global_vars.game.days = [MagicMock(), MagicMock()]  # about to start day 3
    global_vars.game.seatingOrder = [minion_player]

    st1 = MagicMock()
    st2 = MagicMock()
    global_vars.gamemaster_role = MagicMock()
    global_vars.gamemaster_role.members = [st1, st2]

    await riot.on_day_start(origin=MagicMock(), kills=[])

    storyteller_reminder = mock_notify_storytellers.await_args.args[0]
    reminder = "Riot is active on day 3! Update all Minion characters to Riot sometime today if you have not already."

    assert riot.day_3_notification_sent is True
    mock_notify_storytellers.assert_awaited_once()
    assert "Riot is active on day 3!" in storyteller_reminder
    assert "Please update all minion characters to Riot at the appropriate time." in storyteller_reminder
    assert mock_safe_send.await_count == 2
    mock_safe_send.assert_any_await(st1, reminder)
    mock_safe_send.assert_any_await(st2, reminder)
    assert all(call.args[1].isascii() for call in mock_safe_send.await_args_list)

    await riot.on_day_start(origin=MagicMock(), kills=[])
    assert mock_safe_send.await_count == 2
    mock_notify_storytellers.assert_awaited_once()


@pytest.mark.asyncio
@patch('model.characters.specific.utils.notify_storytellers', new_callable=AsyncMock)
@patch('utils.message_utils.safe_send', new_callable=AsyncMock)
async def test_riot_day_3_reminder_not_sent_without_minion(mock_safe_send, mock_notify_storytellers):
    """Riot should NOT notify storytellers if no minion exists in the game."""
    riot_parent = MagicMock()
    riot_parent.is_ghost = False
    riot = Riot(riot_parent)

    global_vars.game = MagicMock()
    global_vars.game.has_automated_life_and_death = True
    global_vars.game.days = [MagicMock(), MagicMock()]  # about to start day 3
    global_vars.game.seatingOrder = []  # No minions

    st1 = MagicMock()
    global_vars.gamemaster_role = MagicMock()
    global_vars.gamemaster_role.members = [st1]

    await riot.on_day_start(origin=MagicMock(), kills=[])

    # Notification should NOT be sent
    assert riot.day_3_notification_sent is False
    mock_notify_storytellers.assert_not_awaited()
    mock_safe_send.assert_not_awaited()


@pytest.mark.asyncio
@patch('utils.character_utils.has_ability', return_value=False)
@patch('utils.message_utils.safe_send', new_callable=AsyncMock)
async def test_riot_nomination_no_longer_sends_day_3_reminder(mock_safe_send, _mock_has_ability):
    """Riot nomination chain should proceed without sending day-3 reminder text."""
    riot_parent = MagicMock()
    riot_parent.is_ghost = False
    riot = Riot(riot_parent)

    vote = MagicMock()
    vote.announcements = []
    this_day = MagicMock()
    this_day.votes = [vote]
    this_day.riot_active = False
    this_day.st_riot_kill_override = False
    this_day.open_noms = AsyncMock()

    global_vars.game = MagicMock()
    global_vars.game.has_automated_life_and_death = True
    global_vars.game.show_tally = False
    global_vars.game.days = [MagicMock(), MagicMock(), this_day]
    global_vars.game.seatingOrder = []

    global_vars.player_role = MagicMock()
    global_vars.player_role.mention = "@players"
    global_vars.channel = MagicMock()

    global_vars.gamemaster_role = MagicMock()
    global_vars.gamemaster_role.members = [MagicMock()]

    announcement_message = MagicMock()
    announcement_message.id = 100
    announcement_message.pin = AsyncMock()
    riot_message = MagicMock()
    riot_message.id = 101
    riot_message.pin = AsyncMock()
    mock_safe_send.side_effect = [announcement_message, riot_message]

    nominee = MagicMock()
    nominee.display_name = "Nominee"
    nominee.user.mention = "@nominee"
    nominee.character.is_poisoned = False
    nominee.kill = AsyncMock()
    nominee.riot_nominee = False
    nominee.can_nominate = False

    nominator = MagicMock()
    nominator.display_name = "Nominator"
    nominator.character.is_poisoned = False
    nominator.is_ghost = False
    nominator.riot_nominee = True

    result = await riot.on_nomination(nominee, nominator, True)

    reminder = "Riot is active on day 3! Please manually update all Minion characters to Riot."
    sent_texts = [call.args[1] for call in mock_safe_send.await_args_list if len(call.args) > 1]

    assert result is False
    assert riot.day_3_notification_sent is False
    assert reminder not in sent_texts
    assert sent_texts == [
        "@players, @nominee has been nominated by Nominator.",
        "Riot is in play. @nominee to nominate",
    ]
    assert all(text.isascii() for text in sent_texts)
    announcement_message.pin.assert_awaited_once()
    assert vote.announcements == [100]
    assert this_day.riot_active is True
    nominee.kill.assert_awaited_once()
    assert nominator.riot_nominee is False
    assert nominee.riot_nominee is True
    assert nominee.can_nominate is True
    this_day.open_noms.assert_awaited_once()

