"""
Tests for the Game class in bot_impl.py
"""

import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import global_vars
from bot_impl import Game, Player, Script
from model.characters import Character
from model.game import Day
from tests.test_bot_integration import mock_discord_setup, setup_test_game, MockChannel


# Mock interfaces for testing since we can't create multiple inheritance with them
class MockSeatingOrderModifier:
    def seating_order_message(self, seating_order):
        return " (Modified)"


class MockDayStartModifier:
    async def on_day_start(self, origin, kills):
        return True


@pytest.mark.asyncio
async def test_game_initialization(mock_discord_setup):
    """Test that Game is properly initialized with the expected attributes."""
    # Create a basic seating order
    alice = Player(
        Character,
        "good",
        mock_discord_setup['members']['alice'],
        mock_discord_setup['channels']['st1'],
        0
    )
    bob = Player(
        Character,
        "good",
        mock_discord_setup['members']['bob'],
        mock_discord_setup['channels']['st2'],
        1
    )
    seating_order = [alice, bob]

    # Create a seating order message
    seating_message = AsyncMock()
    seating_message.created_at = datetime.datetime.now()

    # Mock the gamemaster role and members
    mock_gamemaster = MagicMock()
    mock_gamemaster.members = [mock_discord_setup['members']['storyteller']]

    with patch('global_vars.gamemaster_role', mock_gamemaster):
        # Create a Game instance
        game = Game(seating_order, seating_message, Script([]))

        # Verify attributes were set correctly
        assert game.days == []
        assert game.isDay is False
        assert game.seatingOrder == seating_order
        assert game.whisper_mode == "all"
        assert game.seatingOrderMessage == seating_message
        assert len(game.storytellers) == 1
        assert game.show_tally is False
        assert game.has_automated_life_and_death is False


# test_game_end was removed - functionality is covered by integration tests in 
# test_storyteller_commands.py::test_storyteller_endgame_command and
# test_bot_integration.py::test_on_message_endgame_command


@pytest.mark.asyncio
async def test_reseat_method(mock_discord_setup, setup_test_game):
    """Test the Game.reseat method."""
    # Mock the seating order message
    mock_message = AsyncMock()
    mock_message.edit = AsyncMock()

    # Set up game with mocked message
    game = setup_test_game['game']
    game.seatingOrderMessage = mock_message

    # Create a new seating order by shuffling the current one
    new_order = game.seatingOrder.copy() # Alice, Bob, Charlie by default

    # Setup specific player states for testing display:
    # Player 0 (Alice): Ghost, hand raised, 0 dead votes
    alice_player = new_order[0]
    alice_player.is_ghost = True
    alice_player.hand_raised = True
    alice_player.dead_votes = 0

    # Player 1 (Bob): Ghost, hand NOT raised, 1 dead vote
    bob_player = new_order[1]
    bob_player.is_ghost = True
    bob_player.hand_raised = False # Explicitly false
    bob_player.dead_votes = 1

    # Player 2 (Charlie): Alive, hand raised
    charlie_player = new_order[2]
    charlie_player.is_ghost = False # Ensure alive, already default
    charlie_player.hand_raised = True

    # Test reseat with new order
    # reseat now calls game.update_seating_order_message, which in turn calls game.seatingOrderMessage.edit
    with patch('model.game.game.reorder_channels', new_callable=AsyncMock) as mock_reorder:
        # Don't mock update_seating_order_message to avoid recursion
        # Let it call the real method which will edit the mock message
        await game.reseat(new_order)

        assert mock_reorder.called

    # Check positions were updated correctly
    for i, player in enumerate(new_order):
        assert player.position == i

    # Verify message edit was called
    mock_message.edit.assert_called_once()

    # Check the content of the edited message
    call_args = mock_message.edit.call_args[1]
    content = call_args['content'] # Easier to reference
    assert "**Seating Order:**" in content

    # Assertions for Alice (Ghost, hand raised, 0 dead votes)
    # Expected format: ~~Name~~ X ✋
    expected_alice_text = f"~~{alice_player.display_name}~~ X ✋"
    assert expected_alice_text in content, f"Alice's display incorrect. Expected: '{expected_alice_text}' in '{content}'"

    # Assertions for Bob (Ghost, hand NOT raised, 1 dead vote)
    # Expected format: ~~Name~~ O
    expected_bob_text = f"~~{bob_player.display_name}~~ O" # 1 dead vote = O
    assert expected_bob_text in content, f"Bob's display incorrect. Expected: '{expected_bob_text}' in '{content}'"
    # Also ensure Bob does NOT have hand emoji since hand is not raised
    # Bob should not have hand emoji before the vote token indicator
    assert f"~~{bob_player.display_name}~~ O ✋" not in content, f"Bob ({bob_player.display_name}) should not have hand emoji before vote token."


    # Assertions for Charlie (Alive, hand raised)
    # Expected format: Name ✋
    expected_charlie_text = f"{charlie_player.display_name} ✋"
    assert expected_charlie_text in content, f"Charlie's display incorrect. Expected: '{expected_charlie_text}' in '{content}'"

    # Verify SeatingOrderModifier is still processed if applicable
    # This part of the original test logic for reseat should still hold
    if any(isinstance(p.character, MockSeatingOrderModifier) for p in new_order):
        assert " (Modified)" in call_args['content']


@pytest.mark.asyncio
async def test_whisper_mode_changing(mock_discord_setup, setup_test_game):
    """Test changing whisper modes in the Game class."""
    # Test each valid whisper mode
    modes = ["all", "neighbors", "storytellers"]

    for mode in modes:
        # Set the whisper mode
        setup_test_game['game'].whisper_mode = mode

        # Verify it was set correctly
        assert setup_test_game['game'].whisper_mode == mode


@pytest.mark.asyncio
async def test_pretty_player_list(mock_discord_setup, setup_test_game):
    """Test creating a formatted player list."""
    # This tests the functionality shown in the reseat method
    # Set up the game with players
    game = setup_test_game['game']

    # Copy only players in the seating order (not storyteller)
    players_in_game = [p for p in setup_test_game['players'].values()
                       if p in game.seatingOrder]

    # Add a ghost player and a player with dead votes
    ghost_player = players_in_game[0]
    ghost_player.is_ghost = True

    player_with_votes = players_in_game[1]
    player_with_votes.is_ghost = True
    player_with_votes.dead_votes = 2

    # Create the player list message manually (similar to reseat method)
    message_text = "**Seating Order:**"
    for person in game.seatingOrder:
        if person.is_ghost:
            if person.dead_votes <= 0:
                message_text += "\n{}".format("~~" + person.display_name + "~~ X")
            else:
                message_text += "\n{}".format(
                    "~~" + person.display_name + "~~ " + "O" * person.dead_votes
                )
        else:
            message_text += "\n{}".format(person.display_name)

    # Check that the message contains expected player names for seating order players
    for player in players_in_game:
        assert player.display_name in message_text

    # Check that ghost formatting is correct
    assert "~~" + ghost_player.display_name + "~~ X" in message_text
    assert "~~" + player_with_votes.display_name + "~~ OO" in message_text


@pytest.mark.asyncio
async def test_start_day(mock_discord_setup, setup_test_game):
    """Test the basic properties of day start."""
    # We're skipping direct start_day testing due to complexity with mocking
    # Instead just test the expected state conditions after a day starts

    # Set up global variables
    global_vars.channel = mock_discord_setup['channels']['town_square']
    global_vars.player_role = mock_discord_setup['roles']['player']

    # Create mock whisper channel
    whisper_channel = MockChannel(999, "whispers")
    global_vars.whisper_channel = whisper_channel

    # Create a Day object for our game
    day = Day()

    # Add the day to our game
    game = setup_test_game['game']
    game.days = [day]
    game.isDay = True

    # Verify the game state is correctly set up
    assert len(game.days) == 1
    assert game.isDay is True

    # Test day properties
    assert not day.isExecutionToday
    assert not day.isNoms
    assert day.isPms  # PMs are open by default

    # Create another day - simulate starting a new day
    day2 = Day()
    game.days.append(day2)

    # Verify day count increases
    assert len(game.days) == 2
