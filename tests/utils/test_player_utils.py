"""
Tests for player utility functions used in the BOTC bot
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch, Mock, call

import discord
import pytest

from bot_impl import generate_possibilities, select_player, choices, yes_no, get_player
from utils.player_utils import (is_player, find_player_by_nick, who_by_id,
                                who_by_character, who, get_neighbors,
                                check_and_print_if_one_or_zero_to_check_in)


# Common test fixtures and setup

@pytest.fixture
def mock_players():
    """Create a set of mock players for testing."""
    player1 = MagicMock()
    player1.display_name = "Alice"
    player1.name = "alice123"

    player2 = MagicMock()
    player2.display_name = "Bob"
    player2.name = "bob456"

    player3 = MagicMock()
    player3.display_name = "Charlie"
    player3.name = "charlie789"

    return [player1, player2, player3]


@pytest.mark.asyncio
async def test_generate_possibilities(mock_players):
    """Test the generate_possibilities function."""
    # Test exact match with display_name
    result = await generate_possibilities("Alice", mock_players)
    assert result == [mock_players[0]]

    # Test partial match with display_name
    result = await generate_possibilities("Ali", mock_players)
    assert result == [mock_players[0]]

    # Test case-insensitive match
    result = await generate_possibilities("alice", mock_players)
    assert result == [mock_players[0]]

    # Test match with name (not display_name)
    result = await generate_possibilities("charlie", mock_players)
    assert result == [mock_players[2]]

    # Test multiple matches
    player4 = MagicMock()
    player4.display_name = "Alicia"
    player4.name = "alicia"
    mock_players.append(player4)

    result = await generate_possibilities("Ali", mock_players)
    assert len(result) == 2
    assert mock_players[0] in result
    assert player4 in result

    # Test no matches
    result = await generate_possibilities("nonexistent", mock_players)
    assert result == []

    # Test with person that has None display_name
    player5 = MagicMock()
    player5.display_name = None
    player5.name = "david"
    mock_players.append(player5)

    result = await generate_possibilities("david", mock_players)
    assert result == [player5]


@pytest.mark.asyncio
async def test_choices_with_number(mock_players):
    """Test the choices function when user selects by number."""
    # Setup
    user = MagicMock()
    possibilities = mock_players[:2]  # Alice and Bob

    # Create the mock reply
    mock_reply = MagicMock()

    # User selects option 1 (Alice)
    mock_choice = MagicMock()
    mock_choice.content = "1"  # Select first option
    mock_choice.author = user
    mock_choice.channel = mock_reply.channel

    # Patch the necessary functions
    with patch('utils.message_utils.safe_send', return_value=mock_reply) as mock_safe_send:
        with patch('bot_client.client') as mock_client:
            # Setup the wait_for mock
            mock_client.wait_for = AsyncMock(return_value=mock_choice)

            # Call choices
            result = await choices(user, possibilities, "Test")

            # Verify result is Alice
            assert result == mock_players[0]

            # Verify send called with options
            mock_safe_send.assert_called_once()
            # Message should include option numbers and names
            call_args = mock_safe_send.call_args[0][1]
            assert "Alice" in call_args
            assert "Bob" in call_args


@pytest.mark.asyncio
async def test_choices_with_cancel(mock_players):
    """Test the choices function when user cancels."""
    # Setup
    user = MagicMock()
    possibilities = mock_players[:2]  # Alice and Bob

    # Create the mock reply
    mock_reply = MagicMock()

    # User cancels
    mock_choice = MagicMock()
    mock_choice.content = "cancel"
    mock_choice.author = user
    mock_choice.channel = mock_reply.channel

    # Patch the necessary functions
    with patch('utils.message_utils.safe_send', return_value=mock_reply) as mock_safe_send:
        with patch('bot_client.client') as mock_client:
            # Setup the wait_for mock
            mock_client.wait_for = AsyncMock(return_value=mock_choice)

            # Call choices
            result = await choices(user, possibilities, "Test")

            # Verify result is None on cancel
            assert result is None


@pytest.mark.asyncio
@patch('utils.message_utils.safe_send')
@patch('bot_client.client.wait_for')
async def test_choices_with_timeout(mock_wait_for, mock_safe_send, mock_players):
    """Test the choices function when it times out."""
    # Setup
    user = MagicMock()
    possibilities = mock_players[:2]  # Alice and Bob

    # Create the mock reply
    mock_reply = MagicMock()
    mock_safe_send.return_value = mock_reply

    # Simulate timeout
    mock_wait_for.side_effect = asyncio.TimeoutError()

    # Call choices
    result = await choices(user, possibilities, "Test")

    # Verify result is None on timeout
    assert result is None


@pytest.mark.asyncio
async def test_select_player_exact_match(mock_players):
    """Test select_player with an exact match."""
    # Setup
    user = MagicMock()

    # Patch generate_possibilities to return a single player
    with patch('bot_impl.generate_possibilities', new_callable=AsyncMock) as mock_gen_poss:
        with patch('utils.message_utils.safe_send', new_callable=AsyncMock) as mock_safe_send:
            with patch('bot_impl.choices', new_callable=AsyncMock) as mock_choices:
                # Mock return value
                mock_gen_poss.return_value = [mock_players[0]]

                # Call select_player
                result = await select_player(user, "Alice", mock_players)

                # Verify result is the expected player
                assert result == mock_players[0]

                # Verify generate_possibilities was called
                mock_gen_poss.assert_awaited_once_with("Alice", mock_players)

                # Verify safe_send and choices were not called
                mock_safe_send.assert_not_awaited()
                mock_choices.assert_not_awaited()


@pytest.mark.asyncio
async def test_select_player_no_match():
    """Test select_player with no matches."""
    # Setup
    user = MagicMock()
    players = []

    # Patch generate_possibilities to return empty list
    with patch('bot_impl.generate_possibilities', new_callable=AsyncMock) as mock_gen_poss:
        with patch('utils.message_utils.safe_send', new_callable=AsyncMock) as mock_safe_send:
            # Mock return value
            mock_gen_poss.return_value = []

            # Call select_player
            result = await select_player(user, "nonexistent", players)

            # Verify result is None
            assert result is None

            # Verify safe_send was called with error message
            mock_safe_send.assert_awaited_once()
            # Error message should include the name
            assert "nonexistent" in mock_safe_send.call_args[0][1]


@pytest.mark.asyncio
async def test_select_player_multiple_matches(mock_players):
    """Test select_player with multiple matches."""
    # Setup
    user = MagicMock()

    # Patch generate_possibilities and choices
    with patch('bot_impl.generate_possibilities', new_callable=AsyncMock) as mock_gen_poss:
        with patch('bot_impl.choices', new_callable=AsyncMock) as mock_choices:
            # Mock generate_possibilities to return multiple players
            mock_gen_poss.return_value = mock_players[:2]  # Alice and Bob

            # Mock choices to return one player
            mock_choices.return_value = mock_players[0]  # Alice

            # Call select_player
            result = await select_player(user, "A", mock_players)

            # Verify result is the player returned by choices
            assert result == mock_players[0]

            # Verify generate_possibilities was called
            mock_gen_poss.assert_awaited_once_with("A", mock_players)

            # Verify choices was called with the matched players
            mock_choices.assert_awaited_once_with(user, mock_players[:2], "A")


@pytest.mark.asyncio
async def test_yes_no_with_yes():
    """Test yes_no function with 'yes' response."""
    # Setup
    user = MagicMock()

    # Create mock reply
    mock_reply = MagicMock()

    # User responds with 'yes'
    mock_choice = MagicMock()
    mock_choice.content = "yes"
    mock_choice.author = user
    mock_choice.channel = mock_reply.channel

    # Patch the necessary functions
    with patch('utils.message_utils.safe_send', return_value=mock_reply) as mock_safe_send:
        with patch('bot_client.client') as mock_client:
            # Setup the wait_for mock
            mock_client.wait_for = AsyncMock(return_value=mock_choice)

            # Call yes_no
            result = await yes_no(user, "Are you sure?")

            # Verify result is True
            assert result is True

            # Verify safe_send was called with the question
            mock_safe_send.assert_called_once()
            assert "Are you sure?" in mock_safe_send.call_args[0][1]


@pytest.mark.asyncio
@patch('utils.message_utils.safe_send')
@patch('bot_client.client.wait_for')
async def test_get_player_found(mock_wait_for, mock_safe_send):
    """Test get_player when player is found."""
    # Setup
    user = MagicMock()
    player = MagicMock()

    # Mock the global game object and seating order
    with patch('bot_impl.global_vars') as mock_global_vars:
        mock_global_vars.game.seatingOrder = [player]
        player.user = user

        # Call get_player
        result = await get_player(user)

        # Verify correct player was returned
        assert result == player


@pytest.mark.asyncio
@patch('utils.message_utils.safe_send')
@patch('bot_client.client.wait_for')
async def test_get_player_not_found(mock_wait_for, mock_safe_send):
    """Test get_player when player is not found."""
    # Setup
    user = MagicMock()
    other_user = MagicMock()
    player = MagicMock()

    # Mock the global game object and seating order
    with patch('bot_impl.global_vars') as mock_global_vars:
        mock_global_vars.game.seatingOrder = [player]
        player.user = other_user  # Different user

        # Call get_player
        result = await get_player(user)

        # Verify None was returned
        assert result is None


class TestIsPlayer:
    """Test the is_player function."""

    @patch('utils.player_utils.global_vars')
    def test_player_role(self, mock_global_vars):
        """Test function returns True when member has player role."""
        mock_member = Mock(spec=discord.Member)
        mock_role = Mock(spec=discord.Role)
        mock_global_vars.player_role = mock_role
        mock_member.roles = [mock_role]

        result = is_player(mock_member)

        assert result

    @patch('utils.player_utils.global_vars')
    def test_not_player_role(self, mock_global_vars):
        """Test function returns False when member doesn't have player role."""
        mock_member = Mock(spec=discord.Member)
        mock_role = Mock(spec=discord.Role)
        mock_other_role = Mock(spec=discord.Role)
        mock_global_vars.player_role = mock_role
        mock_member.roles = [mock_other_role]

        result = is_player(mock_member)

        assert not result


class TestFindPlayerByNick:
    """Test the find_player_by_nick function."""

    @patch('utils.player_utils.global_vars')
    def test_exact_match(self, mock_global_vars):
        """Test finding player by exact display name match."""
        player1 = Mock()
        player1.display_name = "Alice"
        player2 = Mock()
        player2.display_name = "Bob"

        mock_game = Mock()
        mock_game.seatingOrder = [player1, player2]
        mock_global_vars.game = mock_game

        result = find_player_by_nick("Alice")

        assert result == player1

    @patch('utils.player_utils.global_vars')
    def test_case_insensitive_match(self, mock_global_vars):
        """Test finding player by case-insensitive display name match."""
        player1 = Mock()
        player1.display_name = "Alice"
        player2 = Mock()
        player2.display_name = "Bob"

        mock_game = Mock()
        mock_game.seatingOrder = [player1, player2]
        mock_global_vars.game = mock_game

        result = find_player_by_nick("alice")

        assert result == player1

    @patch('utils.player_utils.global_vars')
    def test_partial_match(self, mock_global_vars):
        """Test finding player by partial display name match."""
        player1 = Mock()
        player1.display_name = "Alice Smith"
        player2 = Mock()
        player2.display_name = "Bob Jones"

        mock_game = Mock()
        mock_game.seatingOrder = [player1, player2]
        mock_global_vars.game = mock_game

        result = find_player_by_nick("smith")

        assert result == player1

    @patch('utils.player_utils.global_vars')
    def test_no_match(self, mock_global_vars):
        """Test finding no match returns None."""
        player1 = Mock()
        player1.display_name = "Alice"
        player2 = Mock()
        player2.display_name = "Bob"

        mock_game = Mock()
        mock_game.seatingOrder = [player1, player2]
        mock_global_vars.game = mock_game

        result = find_player_by_nick("Charlie")

        assert result is None


class TestWhoById:
    """Test the who_by_id function."""

    @patch('utils.player_utils.global_vars')
    def test_find_by_id(self, mock_global_vars):
        """Test finding player by ID."""
        user1 = Mock(spec=discord.User)
        user1.id = 12345
        player1 = Mock()
        player1.user = user1

        user2 = Mock(spec=discord.User)
        user2.id = 67890
        player2 = Mock()
        player2.user = user2

        mock_game = Mock()
        mock_game.seatingOrder = [player1, player2]
        mock_global_vars.game = mock_game

        result = who_by_id(12345)

        assert result == player1

    @patch('utils.player_utils.global_vars')
    def test_no_match_by_id(self, mock_global_vars):
        """Test finding no player by ID returns None."""
        user1 = Mock(spec=discord.User)
        user1.id = 12345
        player1 = Mock()
        player1.user = user1

        mock_game = Mock()
        mock_game.seatingOrder = [player1]
        mock_global_vars.game = mock_game

        result = who_by_id(999)

        assert result is None


class TestWhoByCharacter:
    """Test the who_by_character function."""

    @patch('utils.player_utils.global_vars')
    def test_find_by_character(self, mock_global_vars):
        """Test finding player by character name."""
        player1 = Mock()
        player1.character = Mock()
        player1.character.role_name = "Washerwoman"

        player2 = Mock()
        player2.character = Mock()
        player2.character.role_name = "Slayer"

        mock_game = Mock()
        mock_game.seatingOrder = [player1, player2]
        mock_global_vars.game = mock_game

        result = who_by_character("Washerwoman")

        assert result == player1

    @patch('utils.player_utils.global_vars')
    def test_case_insensitive_character(self, mock_global_vars):
        """Test finding player by case-insensitive character name."""
        player1 = Mock()
        player1.character = Mock()
        player1.character.role_name = "Washerwoman"

        mock_game = Mock()
        mock_game.seatingOrder = [player1]
        mock_global_vars.game = mock_game

        result = who_by_character("washerwoman")

        assert result == player1

    @patch('utils.player_utils.global_vars')
    def test_no_match_by_character(self, mock_global_vars):
        """Test finding no player by character returns None."""
        player1 = Mock()
        player1.character = Mock()
        player1.character.role_name = "Washerwoman"

        mock_game = Mock()
        mock_game.seatingOrder = [player1]
        mock_global_vars.game = mock_game

        result = who_by_character("Fortune Teller")

        assert result is None


class TestWho:
    """Test the who function."""

    @patch('utils.player_utils.who_by_id')
    def test_who_with_int(self, mock_who_by_id):
        """Test who with integer ID."""
        mock_who_by_id.return_value = "player1"

        result = who(12345)

        mock_who_by_id.assert_called_once_with(12345)
        assert result == "player1"

    @patch('utils.player_utils.who_by_id')
    def test_who_with_digit_string(self, mock_who_by_id):
        """Test who with string containing digits."""
        mock_who_by_id.return_value = "player1"

        result = who("12345")

        mock_who_by_id.assert_called_once_with(12345)
        assert result == "player1"

    @patch('utils.player_utils.who_by_name')
    @patch('utils.player_utils.who_by_id')
    def test_who_with_name_string(self, mock_who_by_id, mock_who_by_name):
        """Test who with name string."""
        mock_who_by_id.return_value = None
        mock_who_by_name.return_value = "player1"

        result = who("Alice")

        mock_who_by_name.assert_called_once_with("Alice")
        assert result == "player1"

    @patch('utils.player_utils.who_by_character')
    @patch('utils.player_utils.who_by_name')
    @patch('utils.player_utils.who_by_id')
    def test_who_with_character_string(self, mock_who_by_id, mock_who_by_name, mock_who_by_character):
        """Test who with character string."""
        mock_who_by_id.return_value = None
        mock_who_by_name.return_value = None
        mock_who_by_character.return_value = "player1"

        result = who("Slayer")

        mock_who_by_character.assert_called_once_with("Slayer")
        assert result == "player1"

    @patch('utils.player_utils.who_by_id')
    def test_who_with_member(self, mock_who_by_id):
        """Test who with Discord member."""
        mock_member = Mock(spec=discord.Member)
        mock_member.id = 12345
        mock_who_by_id.return_value = "player1"

        result = who(mock_member)

        mock_who_by_id.assert_called_once_with(12345)
        assert result == "player1"

    @patch('utils.player_utils.who_by_character')
    @patch('utils.player_utils.who_by_name')
    @patch('utils.player_utils.who_by_id')
    def test_who_with_no_match(self, mock_who_by_id, mock_who_by_name, mock_who_by_character):
        """Test who with no match returns None."""
        mock_who_by_id.return_value = None
        mock_who_by_name.return_value = None
        mock_who_by_character.return_value = None

        result = who("Unknown")

        assert result is None


class TestGetNeighbors:
    """Test the get_neighbors function."""

    @patch('utils.player_utils.global_vars')
    def test_get_neighbors_normal(self, mock_global_vars):
        """Test getting neighbors for a player in the middle."""
        player1 = Mock()
        player1.is_ghost = False

        player2 = Mock()
        player2.is_ghost = False

        player3 = Mock()
        player3.is_ghost = False

        mock_game = Mock()
        mock_game.seatingOrder = [player1, player2, player3]
        mock_global_vars.game = mock_game

        result = get_neighbors(player2)

        assert result == [player1, player3]

    @patch('utils.player_utils.global_vars')
    def test_get_neighbors_wraparound(self, mock_global_vars):
        """Test getting neighbors for a player at the end."""
        player1 = Mock()
        player1.is_ghost = False

        player2 = Mock()
        player2.is_ghost = False

        player3 = Mock()
        player3.is_ghost = False

        mock_game = Mock()
        mock_game.seatingOrder = [player1, player2, player3]
        mock_global_vars.game = mock_game

        result = get_neighbors(player3)

        assert result == [player2, player1]

    @patch('utils.player_utils.global_vars')
    def test_get_neighbors_skip_ghost(self, mock_global_vars):
        """Test neighbors skips ghost players."""
        player1 = Mock()
        player1.is_ghost = False

        player2 = Mock()
        player2.is_ghost = True  # Ghost player should be skipped

        player3 = Mock()
        player3.is_ghost = False

        player4 = Mock()
        player4.is_ghost = False

        mock_game = Mock()
        mock_game.seatingOrder = [player1, player2, player3, player4]
        mock_global_vars.game = mock_game

        result = get_neighbors(player1)

        assert result == [player4, player3]  # Should skip player2

    @patch('utils.player_utils.global_vars')
    def test_player_not_in_seating_order(self, mock_global_vars):
        """Test empty list returned when player not in seating order."""
        player1 = Mock()
        player2 = Mock()  # This player is not in seating order

        mock_game = Mock()
        mock_game.seatingOrder = [player1]
        mock_global_vars.game = mock_game

        result = get_neighbors(player2)

        assert result == []


class TestCheckAndPrintIfOneOrZeroToCheckIn:
    """Test the check_and_print_if_one_or_zero_to_check_in function."""

    @patch('utils.message_utils.safe_send')
    @patch('utils.player_utils.global_vars')
    @pytest.mark.asyncio
    async def test_one_player_left(self, mock_global_vars, mock_safe_send):
        """Test message when one player left to check in."""
        player1 = Mock()
        player1.has_checked_in = True
        player1.alignment = "good"

        player2 = Mock()
        player2.has_checked_in = False
        player2.alignment = "evil"
        player2.display_name = "Bob"

        player3 = Mock()  # Storyteller (neutral) should be ignored
        player3.has_checked_in = False
        player3.alignment = "neutral"

        mock_game = Mock()
        mock_game.seatingOrder = [player1, player2, player3]

        member1 = Mock(spec=discord.Member)
        member2 = Mock(spec=discord.Member)
        role = Mock(spec=discord.Role)
        role.members = [member1, member2]

        mock_global_vars.game = mock_game
        mock_global_vars.gamemaster_role = role

        await check_and_print_if_one_or_zero_to_check_in()

        assert mock_safe_send.call_count == 2
        mock_safe_send.assert_has_calls([
            call(member1, "Just waiting on Bob to check in."),
            call(member2, "Just waiting on Bob to check in.")
        ])

    @patch('utils.message_utils.safe_send')
    @patch('utils.player_utils.global_vars')
    @pytest.mark.asyncio
    async def test_zero_players_left(self, mock_global_vars, mock_safe_send):
        """Test message when zero players left to check in."""
        player1 = Mock()
        player1.has_checked_in = True
        player1.alignment = "good"

        player2 = Mock()
        player2.has_checked_in = True
        player2.alignment = "evil"

        mock_game = Mock()
        mock_game.seatingOrder = [player1, player2]

        member1 = Mock(spec=discord.Member)
        role = Mock(spec=discord.Role)
        role.members = [member1]

        mock_global_vars.game = mock_game
        mock_global_vars.gamemaster_role = role

        await check_and_print_if_one_or_zero_to_check_in()

        mock_safe_send.assert_called_once_with(member1, "Everyone has checked in!")

    @patch('utils.message_utils.safe_send')
    @patch('utils.player_utils.global_vars')
    @pytest.mark.asyncio
    async def test_multiple_players_left(self, mock_global_vars, mock_safe_send):
        """Test no message when multiple players left to check in."""
        player1 = Mock()
        player1.has_checked_in = False
        player1.alignment = "good"

        player2 = Mock()
        player2.has_checked_in = False
        player2.alignment = "evil"

        mock_game = Mock()
        mock_game.seatingOrder = [player1, player2]

        member1 = Mock(spec=discord.Member)
        role = Mock(spec=discord.Role)
        role.members = [member1]

        mock_global_vars.game = mock_game
        mock_global_vars.gamemaster_role = role

        await check_and_print_if_one_or_zero_to_check_in()

        mock_safe_send.assert_not_called()
