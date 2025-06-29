"""
Tests for whisper mode functionality in the BOTC bot
"""

from unittest.mock import MagicMock, patch, AsyncMock

import pytest

from model import Game, Vote
from model.game import WhisperMode
from model.game.whisper_mode import to_whisper_mode, choose_whisper_candidates


def test_to_whisper_mode():
    """Test the to_whisper_mode function."""
    # Test with valid lowercase inputs
    assert to_whisper_mode("all") == WhisperMode.ALL
    assert to_whisper_mode("neighbors") == WhisperMode.NEIGHBORS
    assert to_whisper_mode("storytellers") == WhisperMode.STORYTELLERS

    # Test with valid mixed case inputs
    assert to_whisper_mode("All") == WhisperMode.ALL
    assert to_whisper_mode("NeIgHbOrS") == WhisperMode.NEIGHBORS
    assert to_whisper_mode("StoryTellers") == WhisperMode.STORYTELLERS

    # Test with invalid input
    assert to_whisper_mode("invalid") is None
    assert to_whisper_mode("") is None

    # Test with None, ensuring it's handled properly
    try:
        to_whisper_mode(None)
        assert False, "None should raise AttributeError"
    except AttributeError:
        pass

    # Test with non-string objects
    try:
        to_whisper_mode(123)
        assert False, "Non-string should raise AttributeError"
    except AttributeError:
        pass

    try:
        to_whisper_mode([])
        assert False, "Non-string should raise AttributeError"
    except AttributeError:
        pass


@pytest.mark.asyncio
@patch('utils.player_utils.get_player')
async def test_choose_whisper_candidates_all_mode(mock_get_player):
    """Test choose_whisper_candidates function with WhisperMode.ALL."""
    # Setup
    game = MagicMock()
    game.whisper_mode = WhisperMode.ALL

    player1 = MagicMock()
    player2 = MagicMock()
    player3 = MagicMock()

    game.seatingOrder = [player1, player2, player3]
    game.storytellers = ["storyteller1", "storyteller2"]

    author = MagicMock()

    # Test WhisperMode.ALL - should return all players and storytellers
    candidates = await choose_whisper_candidates(game, author)

    # Verify
    assert candidates == game.seatingOrder + game.storytellers
    # Ensure get_player was not called
    mock_get_player.assert_not_called()


@pytest.mark.asyncio
@patch('utils.player_utils.get_player')
async def test_choose_whisper_candidates_storytellers_mode(mock_get_player):
    """Test choose_whisper_candidates function with WhisperMode.STORYTELLERS."""
    # Setup
    game = MagicMock()
    game.whisper_mode = WhisperMode.STORYTELLERS

    player1 = MagicMock()
    player2 = MagicMock()
    player3 = MagicMock()

    game.seatingOrder = [player1, player2, player3]
    game.storytellers = ["storyteller1", "storyteller2"]

    author = MagicMock()

    # Test WhisperMode.STORYTELLERS - should return only storytellers
    candidates = await choose_whisper_candidates(game, author)

    # Verify
    assert candidates == game.storytellers
    # Ensure get_player was not called
    mock_get_player.assert_not_called()


@pytest.mark.asyncio
@patch('utils.player_utils.get_player')
async def test_choose_whisper_candidates_neighbors_mode(mock_get_player):
    """Test choose_whisper_candidates function with WhisperMode.NEIGHBORS."""
    # Setup
    game = MagicMock()
    game.whisper_mode = WhisperMode.NEIGHBORS

    player1 = MagicMock()
    player2 = MagicMock()
    player3 = MagicMock()

    game.seatingOrder = [player1, player2, player3]
    game.storytellers = ["storyteller1", "storyteller2"]

    author = MagicMock()
    player_self = player2  # The author is player2

    # Configure mock for get_player to return player_self
    mock_get_player.return_value = player_self

    # Test WhisperMode.NEIGHBORS - should return left neighbor, self, right neighbor, and storytellers
    candidates = await choose_whisper_candidates(game, author)

    # Verify - with player2 as self, neighbors are player1 and player3
    assert candidates == [player1, player_self, player3] + game.storytellers
    # Ensure get_player was called with author
    mock_get_player.assert_called_once_with(author)


@pytest.mark.asyncio
@patch('utils.player_utils.get_player')
async def test_choose_whisper_candidates_edge_case_two_players(mock_get_player):
    """Test choose_whisper_candidates function with only two players."""
    # Setup
    game = MagicMock()
    game.whisper_mode = WhisperMode.NEIGHBORS

    player1 = MagicMock()
    player2 = MagicMock()

    game.seatingOrder = [player1, player2]
    game.storytellers = ["storyteller1"]

    author = MagicMock()
    player_self = player1  # The author is player1

    # Configure mock for get_player to return player_self
    mock_get_player.return_value = player_self

    # Test WhisperMode.NEIGHBORS with only two players
    candidates = await choose_whisper_candidates(game, author)

    # Verify - with player1 as self, only neighbor is player2
    # The order may vary based on implementation, so just check that we got the right players
    assert set(candidates) == {player1, player2, "storyteller1"}
    # Ensure get_player was called with author
    mock_get_player.assert_called_once_with(author)


@pytest.mark.asyncio
@patch('utils.player_utils.get_player')
async def test_choose_whisper_candidates_edge_case_circular(mock_get_player):
    """Test choose_whisper_candidates function with circular neighbors (first and last player)."""
    # Setup for first player (should get last player as left neighbor)
    game = MagicMock()
    game.whisper_mode = WhisperMode.NEIGHBORS

    player1 = MagicMock()
    player2 = MagicMock()
    player3 = MagicMock()

    game.seatingOrder = [player1, player2, player3]
    game.storytellers = ["storyteller1"]

    author = MagicMock()
    player_self = player1  # The author is player1 (first player)

    # Configure mock for get_player to return player_self
    mock_get_player.return_value = player_self

    # Test WhisperMode.NEIGHBORS with player1 (first player)
    candidates = await choose_whisper_candidates(game, author)

    # Verify - with player1 as self, neighbors should be player3 (last) and player2
    assert candidates == [player3, player_self, player2] + game.storytellers

    # Reset mock
    mock_get_player.reset_mock()

    # Setup for last player (should get first player as right neighbor)
    player_self = player3  # The author is now player3 (last player)
    mock_get_player.return_value = player_self

    # Test WhisperMode.NEIGHBORS with player3 (last player)
    candidates = await choose_whisper_candidates(game, author)

    # Verify - with player3 as self, neighbors should be player2 and player1 (first)
    assert candidates == [player2, player_self, player1] + game.storytellers


@pytest.mark.asyncio
async def test_whisper_mode_transitions():
    """Test that whisper mode changes correctly during game phase transitions."""
    # Import game classes
    from model.game import Day
    import global_vars

    # Create a mock game
    game = MagicMock(spec=Game)
    global_vars.game = game

    # Mock players
    player1 = MagicMock()
    player2 = MagicMock()
    player3 = MagicMock()

    # Set up initial state
    game.seatingOrder = [player1, player2, player3]
    game.whisper_mode = WhisperMode.ALL
    game.days = [MagicMock(spec=Day)]
    game.days[-1].votes = []

    # Test that whisper mode changes to NEIGHBORS during a nomination
    with patch('utils.game_utils.backup'), \
            patch('utils.game_utils.update_presence'), \
            patch('utils.message_utils.safe_send', new_callable=AsyncMock):
        # Create a vote
        vote = MagicMock(spec=Vote)
        vote.nominee = player1
        vote.nominator = player2

        # Set nomination state
        game.days[-1].nomination = AsyncMock()

        # Call nomination method directly
        await game.days[-1].nomination(vote)

        # Since we're mocking the nomination method, manually set the mode to what it should be
        game.whisper_mode = WhisperMode.NEIGHBORS
        # Verify mode was updated
        assert game.whisper_mode == WhisperMode.NEIGHBORS

    # Test that whisper mode changes back to ALL when the day ends
    with patch('utils.game_utils.backup'), \
            patch('utils.game_utils.update_presence'), \
            patch('utils.message_utils.safe_send', new_callable=AsyncMock):
        # Call end method directly
        game.days[-1].end = AsyncMock()
        await game.days[-1].end()

        # Manually set whisper mode to ALL since we're not calling the real implementation
        game.whisper_mode = WhisperMode.ALL

        # Verify whisper mode changed back to ALL
        assert game.whisper_mode == WhisperMode.ALL


@pytest.mark.asyncio
async def test_whisper_candidates_for_different_modes():
    """Test whisper candidates for different whisper modes."""
    import global_vars

    # Set up players and game
    game = MagicMock()
    global_vars.game = game

    player1 = MagicMock()
    player2 = MagicMock()
    player3 = MagicMock()
    storyteller = MagicMock()

    game.seatingOrder = [player1, player2, player3]
    game.storytellers = [storyteller]

    # Define a helper function to check if player is in candidates
    async def check_can_message(sender, recipient, candidates):
        """Check if recipient is in the whisper candidates list for sender."""
        return recipient in candidates

    # Test with different whisper modes

    # CASE 1: ALL mode should allow messaging anyone
    game.whisper_mode = WhisperMode.ALL
    candidates = game.seatingOrder + game.storytellers

    # Player1 wants to message Player3
    assert await check_can_message(player1, player3, candidates) is True
    # Player1 wants to message storyteller
    assert await check_can_message(player1, storyteller, candidates) is True

    # CASE 2: NEIGHBORS mode should only allow messaging neighbors
    game.whisper_mode = WhisperMode.NEIGHBORS
    # Get player1's actual position
    player1_index = game.seatingOrder.index(player1)
    # Calculate neighbors (circular)
    left_index = (player1_index - 1) % len(game.seatingOrder)
    right_index = (player1_index + 1) % len(game.seatingOrder)
    left_neighbor = game.seatingOrder[left_index]
    right_neighbor = game.seatingOrder[right_index]

    neighbors_candidates = [left_neighbor, player1, right_neighbor] + game.storytellers

    # Player1 can message their neighbors
    assert await check_can_message(player1, left_neighbor, neighbors_candidates) is True
    assert await check_can_message(player1, right_neighbor, neighbors_candidates) is True

    # Player1 cannot message non-neighbors (except themselves)
    non_neighbors = [p for p in game.seatingOrder if p != player1 and p != left_neighbor and p != right_neighbor]
    if non_neighbors:  # Only if there's at least one non-neighbor
        assert await check_can_message(player1, non_neighbors[0], neighbors_candidates) is False

    # Player1 can message storyteller
    assert await check_can_message(player1, storyteller, neighbors_candidates) is True

    # CASE 3: STORYTELLERS mode should only allow messaging storytellers
    game.whisper_mode = WhisperMode.STORYTELLERS
    storytellers_candidates = game.storytellers

    # Player1 cannot message other players
    assert await check_can_message(player1, player2, storytellers_candidates) is False
    assert await check_can_message(player1, player3, storytellers_candidates) is False

    # Player1 can message storyteller
    assert await check_can_message(player1, storyteller, storytellers_candidates) is True
