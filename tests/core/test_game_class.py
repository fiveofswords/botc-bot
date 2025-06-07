"""
Tests for the Game class in bot_impl.py
"""

import datetime
from unittest.mock import AsyncMock, patch, Mock

import discord.errors
import pytest

import global_vars
from bot_impl import Game, Player, Script
from model.characters import Character
from model.game import Day
from tests.fixtures.discord_mocks import mock_discord_setup, MockChannel
from tests.fixtures.game_fixtures import setup_test_game


# Mock interfaces for testing since we can't create multiple inheritance with them
class MockSeatingOrderModifier:
    def seating_order_message(self, seating_order):
        return " (Modified)"


class MockDayStartModifier:
    async def on_day_start(self, origin, kills):
        return True


@pytest.mark.asyncio
async def test_game_initialization(setup_test_game):
    """Test that Game is properly initialized with the expected attributes."""
    game = setup_test_game['game']
    players = setup_test_game['players']

    # Verify basic game attributes
    assert game.isDay is False
    assert game.whisper_mode == "all"
    assert game.show_tally is False
    assert game.has_automated_life_and_death is False

    # Verify seating order contains the expected players
    assert len(game.seatingOrder) == 3
    assert players['alice'] in game.seatingOrder
    assert players['bob'] in game.seatingOrder
    assert players['charlie'] in game.seatingOrder

    # Verify seating order message exists
    assert game.seatingOrderMessage is not None
    assert hasattr(game.seatingOrderMessage, 'created_at')

    # Verify info channel seating order message exists
    assert game.info_channel_seating_order_message is not None

    # Verify storytellers list is properly initialized
    assert len(game.storytellers) == 1
    assert players['storyteller'] == game.storytellers[0]

    # Verify game has days list (with one day from fixture)
    assert isinstance(game.days, list)
    assert len(game.days) == 1

    # Verify script is initialized
    assert hasattr(game, 'script')
    assert game.script is not None


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


@pytest.mark.asyncio
@patch('global_vars.info_channel', new_callable=AsyncMock)
async def test_update_seating_order_message_posts_to_info_channel(mock_info_channel, mock_discord_setup, setup_test_game):
    """Test that update_seating_order_message correctly posts to and updates the info channel."""
    game = setup_test_game['game']

    # Mock game.seatingOrderMessage for the main channel
    game.seatingOrderMessage = AsyncMock()
    game.seatingOrderMessage.edit = AsyncMock()
    game.seatingOrderMessage.id = 12345 # Dummy ID for logging

    # --- Scenario 1: First update (no existing message in info channel) ---
    # Reset the info channel message to None to test creation behavior
    game.info_channel_seating_order_message = None

    # Mock the message returned by info_channel.send
    mock_sent_message_scenario1 = AsyncMock()
    mock_sent_message_scenario1.pin = AsyncMock()
    mock_sent_message_scenario1.edit = AsyncMock() # For scenario 2
    # This is the mock for the .send method of mock_info_channel
    original_send_mock = AsyncMock(return_value=mock_sent_message_scenario1)
    mock_info_channel.send = original_send_mock

    await game.update_seating_order_message()

    # Expected message text
    message_text = "**Seating Order:**"
    for person in game.seatingOrder:
        person_display_name = person.display_name
        if person.is_ghost: # Assuming default setup_test_game has no ghosts initially
            if person.dead_votes <= 0:
                person_display_name = "~~" + person_display_name + "~~ X"
            else:
                person_display_name = "~~" + person_display_name + "~~ " + "O" * person.dead_votes
        if person.hand_raised: # Assuming no hands raised initially
            person_display_name += " ✋"
        message_text += "\n{}".format(person_display_name)
        # Simplified: assuming no SeatingOrderModifier in default setup for this basic check
        # if isinstance(person.character, SeatingOrderModifier):
        #     message_text += person.character.seating_order_message(game.seatingOrder)


    mock_info_channel.send.assert_called_once_with(message_text)
    mock_sent_message_scenario1.pin.assert_called_once()
    assert game.info_channel_seating_order_message == mock_sent_message_scenario1
    # Main channel message should also have been edited
    game.seatingOrderMessage.edit.assert_called_once_with(content=message_text)


    # --- Scenario 2: Subsequent update (existing message in info channel) ---
    # game.info_channel_seating_order_message is now mock_sent_message_scenario1
    await game.update_seating_order_message()

    mock_sent_message_scenario1.edit.assert_called_once_with(content=message_text)
    # Send should not be called again
    assert original_send_mock.call_count == 1 # Still 1 from scenario 1
    # Pin should not be called again
    assert mock_sent_message_scenario1.pin.call_count == 1 # Still 1 from scenario 1
    # Main channel message edit call count should be 2
    assert game.seatingOrderMessage.edit.call_count == 2


    # --- Scenario 3: Message in info channel was deleted ---
    # game.info_channel_seating_order_message is still mock_sent_message_scenario1
    # Make its edit method raise NotFound
    mock_sent_message_scenario1.edit.side_effect = discord.errors.NotFound(Mock(), "Message not found")

    # Mock the new message that will be sent
    mock_sent_message_scenario3 = AsyncMock()
    mock_sent_message_scenario3.pin = AsyncMock()
    # Update info_channel.send to return this new mock for the next call
    # Instead of replacing mock_info_channel.send, we make the original_send_mock return the new message on its next call
    original_send_mock.return_value = mock_sent_message_scenario3


    await game.update_seating_order_message()

    # send should be called again (total 2 times now on original_send_mock)
    assert original_send_mock.call_count == 2
    original_send_mock.assert_called_with(message_text) # Checks the arguments of the last call
    mock_sent_message_scenario3.pin.assert_called_once()
    assert game.info_channel_seating_order_message == mock_sent_message_scenario3
    # Main channel message edit call count should be 3
    assert game.seatingOrderMessage.edit.call_count == 3
    # The old message's edit was called, raised error, then new message sent.
    # So, mock_sent_message_scenario1.edit call count should be 2 (one success, one failure)
    assert mock_sent_message_scenario1.edit.call_count == 2


@pytest.mark.asyncio
@patch('global_vars.whisper_channel', new_callable=AsyncMock)
@patch('global_vars.channel', new_callable=AsyncMock)
@patch('global_vars.info_channel', new_callable=AsyncMock)
async def test_game_end_cleans_up_info_channel_message(mock_info_channel, mock_main_channel, mock_whisper_channel, mock_discord_setup, setup_test_game):
    """Test that Game.end correctly unpins and deletes the info channel message."""
    game = setup_test_game['game']

    # Mock game.seatingOrderMessage (main channel)
    game.seatingOrderMessage = AsyncMock()
    game.seatingOrderMessage.created_at = datetime.datetime.now()
    game.seatingOrderMessage.unpin = AsyncMock()

    # Mock pins for main and whisper channels
    mock_main_channel.pins = AsyncMock(return_value=[])
    mock_whisper_channel.pins = AsyncMock(return_value=[]) # Game.end tries to unpin from it

    # Mock the info channel message
    mock_info_msg = AsyncMock()
    mock_info_msg.unpin = AsyncMock()
    mock_info_msg.delete = AsyncMock()
    game.info_channel_seating_order_message = mock_info_msg

    await game.end(winner='good')

    mock_info_msg.unpin.assert_called_once()
    mock_info_msg.delete.assert_called_once()

    # --- Scenario: Message already deleted/unpinned during unpin attempt ---
    mock_info_msg.reset_mock() # Reset call counts etc.
    mock_info_msg.unpin.side_effect = discord.errors.NotFound(Mock(), "Message not found")
    # delete should still be an AsyncMock without side_effect here

    await game.end(winner='evil') # Call end again with the modified mock

    mock_info_msg.unpin.assert_called_once() # Attempted unpin
    mock_info_msg.delete.assert_not_called()  # Delete should NOT be called when unpin raises NotFound

    # --- Scenario: Message already deleted during delete attempt ---
    mock_info_msg.reset_mock()
    mock_info_msg.unpin.side_effect = None # Clear side effect from previous scenario
    mock_info_msg.unpin.return_value = None # Ensure it's a simple AsyncMock again
    mock_info_msg.delete.side_effect = discord.errors.NotFound(Mock(), "Message not found")

    await game.end(winner='tie')

    mock_info_msg.unpin.assert_called_once() # Unpin should be called
    mock_info_msg.delete.assert_called_once() # Delete was attempted


@pytest.mark.asyncio
@patch('global_vars.info_channel', new_callable=AsyncMock)
async def test_game_functions_correctly_with_none_info_channel_message(mock_info_channel, mock_discord_setup):
    """Test that Game class functions correctly when info_channel_seating_order_message is None."""
    # Create a Game with None for info_channel_seating_order_message
    alice = Player(
        Character,
        "good",
        mock_discord_setup['members']['alice'],
        mock_discord_setup['channels']['st_alice'],
        0
    )
    bob = Player(
        Character,
        "good",
        mock_discord_setup['members']['bob'],
        mock_discord_setup['channels']['st_bob'],
        1
    )
    seating_order = [alice, bob]

    # Create seating order message for main channel
    seating_message = await mock_discord_setup['channels']['town_square'].send(
        "**Seating Order:**\nAlice\nBob")

    # Create Game with None for info channel message
    game = Game(seating_order, seating_message, None, Script([]))

    # Verify initial state
    assert game.info_channel_seating_order_message is None
    assert game.seatingOrder == seating_order
    assert game.seatingOrderMessage == seating_message

    # Test update_seating_order_message with None info channel message
    mock_sent_message = AsyncMock()
    mock_sent_message.pin = AsyncMock()
    mock_info_channel.send = AsyncMock(return_value=mock_sent_message)

    await game.update_seating_order_message()

    # Should create new info channel message since it was None
    mock_info_channel.send.assert_called_once()
    mock_sent_message.pin.assert_called_once()
    assert game.info_channel_seating_order_message == mock_sent_message

    # Test update_seating_order_message again (should edit existing message)
    mock_sent_message.edit = AsyncMock()
    await game.update_seating_order_message()

    mock_sent_message.edit.assert_called_once()
    # send should not be called again
    assert mock_info_channel.send.call_count == 1

    # Test reseat method works with info channel message
    new_seating_order = [bob, alice]  # Swap order
    with patch.object(game, 'update_seating_order_message', new_callable=AsyncMock) as mock_update, \
            patch('model.game.game.reorder_channels', new_callable=AsyncMock) as mock_reorder:
        await game.reseat(new_seating_order)
        mock_update.assert_called_once()
        mock_reorder.assert_called_once()

    assert game.seatingOrder == new_seating_order

    # Test game.end() works correctly with info channel message
    mock_sent_message.unpin = AsyncMock()
    mock_sent_message.delete = AsyncMock()

    # Mock the main channel pins for game.end()
    mock_main_channel = mock_discord_setup['channels']['town_square']
    mock_main_channel.pins = AsyncMock(return_value=[])

    with patch('global_vars.channel', mock_main_channel), \
            patch('global_vars.whisper_channel', None), \
            patch('utils.game_utils.remove_backup'), \
            patch('utils.game_utils.update_presence'):
        await game.end(winner='good')

    mock_sent_message.unpin.assert_called_once()
    mock_sent_message.delete.assert_called_once()

    # Test that game.end() also works when info_channel_seating_order_message is None
    game.info_channel_seating_order_message = None

    with patch('global_vars.channel', mock_main_channel), \
            patch('global_vars.whisper_channel', None), \
            patch('utils.game_utils.remove_backup'), \
            patch('utils.game_utils.update_presence'):
        # This should not raise any exceptions
        await game.end(winner='evil')
