"""
Unit tests for player utility functions.
"""

from unittest import TestCase, IsolatedAsyncioTestCase, mock

import discord

from utils.player_utils import (
    is_player, find_player_by_nick, who_by_id, who_by_character, who, get_neighbors,
    check_and_print_if_one_or_zero_to_check_in
)


class TestIsPlayer(TestCase):
    """Test the is_player function."""

    @mock.patch('utils.player_utils.global_vars')
    def test_player_role(self, mock_global_vars):
        """Test function returns True when member has player role."""
        mock_member = mock.Mock(spec=discord.Member)
        mock_role = mock.Mock(spec=discord.Role)
        mock_global_vars.player_role = mock_role
        mock_member.roles = [mock_role]

        result = is_player(mock_member)

        self.assertTrue(result)

    @mock.patch('utils.player_utils.global_vars')
    def test_not_player_role(self, mock_global_vars):
        """Test function returns False when member doesn't have player role."""
        mock_member = mock.Mock(spec=discord.Member)
        mock_role = mock.Mock(spec=discord.Role)
        mock_other_role = mock.Mock(spec=discord.Role)
        mock_global_vars.player_role = mock_role
        mock_member.roles = [mock_other_role]

        result = is_player(mock_member)

        self.assertFalse(result)


class TestFindPlayerByNick(TestCase):
    """Test the find_player_by_nick function."""

    @mock.patch('utils.player_utils.global_vars')
    def test_exact_match(self, mock_global_vars):
        """Test finding player by exact display name match."""
        player1 = mock.Mock()
        player1.display_name = "Alice"
        player2 = mock.Mock()
        player2.display_name = "Bob"
        
        mock_game = mock.Mock()
        mock_game.seatingOrder = [player1, player2]
        mock_global_vars.game = mock_game

        result = find_player_by_nick("Alice")

        self.assertEqual(result, player1)

    @mock.patch('utils.player_utils.global_vars')
    def test_case_insensitive_match(self, mock_global_vars):
        """Test finding player by case-insensitive display name match."""
        player1 = mock.Mock()
        player1.display_name = "Alice"
        player2 = mock.Mock()
        player2.display_name = "Bob"
        
        mock_game = mock.Mock()
        mock_game.seatingOrder = [player1, player2]
        mock_global_vars.game = mock_game

        result = find_player_by_nick("alice")

        self.assertEqual(result, player1)

    @mock.patch('utils.player_utils.global_vars')
    def test_partial_match(self, mock_global_vars):
        """Test finding player by partial display name match."""
        player1 = mock.Mock()
        player1.display_name = "Alice Smith"
        player2 = mock.Mock()
        player2.display_name = "Bob Jones"
        
        mock_game = mock.Mock()
        mock_game.seatingOrder = [player1, player2]
        mock_global_vars.game = mock_game

        result = find_player_by_nick("smith")

        self.assertEqual(result, player1)

    @mock.patch('utils.player_utils.global_vars')
    def test_no_match(self, mock_global_vars):
        """Test finding no match returns None."""
        player1 = mock.Mock()
        player1.display_name = "Alice"
        player2 = mock.Mock()
        player2.display_name = "Bob"
        
        mock_game = mock.Mock()
        mock_game.seatingOrder = [player1, player2]
        mock_global_vars.game = mock_game

        result = find_player_by_nick("Charlie")

        self.assertIsNone(result)


class TestWhoById(TestCase):
    """Test the who_by_id function."""

    @mock.patch('utils.player_utils.global_vars')
    def test_find_by_id(self, mock_global_vars):
        """Test finding player by ID."""
        user1 = mock.Mock(spec=discord.User)
        user1.id = 12345
        player1 = mock.Mock()
        player1.user = user1
        
        user2 = mock.Mock(spec=discord.User)
        user2.id = 67890
        player2 = mock.Mock()
        player2.user = user2
        
        mock_game = mock.Mock()
        mock_game.seatingOrder = [player1, player2]
        mock_global_vars.game = mock_game

        result = who_by_id(12345)

        self.assertEqual(result, player1)

    @mock.patch('utils.player_utils.global_vars')
    def test_no_match_by_id(self, mock_global_vars):
        """Test finding no player by ID returns None."""
        user1 = mock.Mock(spec=discord.User)
        user1.id = 12345
        player1 = mock.Mock()
        player1.user = user1
        
        mock_game = mock.Mock()
        mock_game.seatingOrder = [player1]
        mock_global_vars.game = mock_game

        result = who_by_id(999)

        self.assertIsNone(result)


class TestWhoByCharacter(TestCase):
    """Test the who_by_character function."""

    @mock.patch('utils.player_utils.global_vars')
    def test_find_by_character(self, mock_global_vars):
        """Test finding player by character name."""
        player1 = mock.Mock()
        player1.character = mock.Mock()
        player1.character.role_name = "Washerwoman"
        
        player2 = mock.Mock()
        player2.character = mock.Mock()
        player2.character.role_name = "Slayer"
        
        mock_game = mock.Mock()
        mock_game.seatingOrder = [player1, player2]
        mock_global_vars.game = mock_game

        result = who_by_character("Washerwoman")

        self.assertEqual(result, player1)

    @mock.patch('utils.player_utils.global_vars')
    def test_case_insensitive_character(self, mock_global_vars):
        """Test finding player by case-insensitive character name."""
        player1 = mock.Mock()
        player1.character = mock.Mock()
        player1.character.role_name = "Washerwoman"
        
        mock_game = mock.Mock()
        mock_game.seatingOrder = [player1]
        mock_global_vars.game = mock_game

        result = who_by_character("washerwoman")

        self.assertEqual(result, player1)

    @mock.patch('utils.player_utils.global_vars')
    def test_no_match_by_character(self, mock_global_vars):
        """Test finding no player by character returns None."""
        player1 = mock.Mock()
        player1.character = mock.Mock()
        player1.character.role_name = "Washerwoman"
        
        mock_game = mock.Mock()
        mock_game.seatingOrder = [player1]
        mock_global_vars.game = mock_game

        result = who_by_character("Fortune Teller")

        self.assertIsNone(result)


class TestWho(TestCase):
    """Test the who function."""

    @mock.patch('utils.player_utils.who_by_id')
    def test_who_with_int(self, mock_who_by_id):
        """Test who with integer ID."""
        mock_who_by_id.return_value = "player1"
        
        result = who(12345)
        
        mock_who_by_id.assert_called_once_with(12345)
        self.assertEqual(result, "player1")

    @mock.patch('utils.player_utils.who_by_id')
    def test_who_with_digit_string(self, mock_who_by_id):
        """Test who with string containing digits."""
        mock_who_by_id.return_value = "player1"
        
        result = who("12345")
        
        mock_who_by_id.assert_called_once_with(12345)
        self.assertEqual(result, "player1")

    @mock.patch('utils.player_utils.who_by_name')
    @mock.patch('utils.player_utils.who_by_id')
    def test_who_with_name_string(self, mock_who_by_id, mock_who_by_name):
        """Test who with name string."""
        mock_who_by_id.return_value = None
        mock_who_by_name.return_value = "player1"
        
        result = who("Alice")
        
        mock_who_by_name.assert_called_once_with("Alice")
        self.assertEqual(result, "player1")

    @mock.patch('utils.player_utils.who_by_character')
    @mock.patch('utils.player_utils.who_by_name')
    @mock.patch('utils.player_utils.who_by_id')
    def test_who_with_character_string(self, mock_who_by_id, mock_who_by_name, mock_who_by_character):
        """Test who with character string."""
        mock_who_by_id.return_value = None
        mock_who_by_name.return_value = None
        mock_who_by_character.return_value = "player1"
        
        result = who("Slayer")
        
        mock_who_by_character.assert_called_once_with("Slayer")
        self.assertEqual(result, "player1")

    @mock.patch('utils.player_utils.who_by_id')
    def test_who_with_member(self, mock_who_by_id):
        """Test who with Discord member."""
        mock_member = mock.Mock(spec=discord.Member)
        mock_member.id = 12345
        mock_who_by_id.return_value = "player1"
        
        result = who(mock_member)
        
        mock_who_by_id.assert_called_once_with(12345)
        self.assertEqual(result, "player1")

    @mock.patch('utils.player_utils.who_by_character')
    @mock.patch('utils.player_utils.who_by_name')
    @mock.patch('utils.player_utils.who_by_id')
    def test_who_with_no_match(self, mock_who_by_id, mock_who_by_name, mock_who_by_character):
        """Test who with no match returns None."""
        mock_who_by_id.return_value = None
        mock_who_by_name.return_value = None
        mock_who_by_character.return_value = None
        
        result = who("Unknown")
        
        self.assertIsNone(result)


class TestGetNeighbors(TestCase):
    """Test the get_neighbors function."""

    @mock.patch('utils.player_utils.global_vars')
    def test_get_neighbors_normal(self, mock_global_vars):
        """Test getting neighbors for a player in the middle."""
        player1 = mock.Mock()
        player1.is_ghost = False
        
        player2 = mock.Mock()
        player2.is_ghost = False
        
        player3 = mock.Mock()
        player3.is_ghost = False
        
        mock_game = mock.Mock()
        mock_game.seatingOrder = [player1, player2, player3]
        mock_global_vars.game = mock_game

        result = get_neighbors(player2)

        self.assertEqual(result, [player1, player3])

    @mock.patch('utils.player_utils.global_vars')
    def test_get_neighbors_wraparound(self, mock_global_vars):
        """Test getting neighbors for a player at the end."""
        player1 = mock.Mock()
        player1.is_ghost = False
        
        player2 = mock.Mock()
        player2.is_ghost = False
        
        player3 = mock.Mock()
        player3.is_ghost = False
        
        mock_game = mock.Mock()
        mock_game.seatingOrder = [player1, player2, player3]
        mock_global_vars.game = mock_game

        result = get_neighbors(player3)

        self.assertEqual(result, [player2, player1])

    @mock.patch('utils.player_utils.global_vars')
    def test_get_neighbors_skip_ghost(self, mock_global_vars):
        """Test neighbors skips ghost players."""
        player1 = mock.Mock()
        player1.is_ghost = False
        
        player2 = mock.Mock()
        player2.is_ghost = True  # Ghost player should be skipped
        
        player3 = mock.Mock()
        player3.is_ghost = False
        
        player4 = mock.Mock()
        player4.is_ghost = False
        
        mock_game = mock.Mock()
        mock_game.seatingOrder = [player1, player2, player3, player4]
        mock_global_vars.game = mock_game

        result = get_neighbors(player1)

        self.assertEqual(result, [player4, player3])  # Should skip player2

    @mock.patch('utils.player_utils.global_vars')
    def test_player_not_in_seating_order(self, mock_global_vars):
        """Test empty list returned when player not in seating order."""
        player1 = mock.Mock()
        player2 = mock.Mock()  # This player is not in seating order
        
        mock_game = mock.Mock()
        mock_game.seatingOrder = [player1]
        mock_global_vars.game = mock_game

        result = get_neighbors(player2)

        self.assertEqual(result, [])


class TestCheckAndPrintIfOneOrZeroToCheckIn(IsolatedAsyncioTestCase):
    """Test the check_and_print_if_one_or_zero_to_check_in function."""

    @mock.patch('utils.player_utils.safe_send')
    @mock.patch('utils.player_utils.global_vars')
    async def test_one_player_left(self, mock_global_vars, mock_safe_send):
        """Test message when one player left to check in."""
        player1 = mock.Mock()
        player1.has_checked_in = True
        player1.alignment = "good"
        
        player2 = mock.Mock()
        player2.has_checked_in = False
        player2.alignment = "evil"
        player2.display_name = "Bob"
        
        player3 = mock.Mock()  # Storyteller (neutral) should be ignored
        player3.has_checked_in = False
        player3.alignment = "neutral"
        
        mock_game = mock.Mock()
        mock_game.seatingOrder = [player1, player2, player3]
        
        member1 = mock.Mock(spec=discord.Member)
        member2 = mock.Mock(spec=discord.Member)
        role = mock.Mock(spec=discord.Role)
        role.members = [member1, member2]
        
        mock_global_vars.game = mock_game
        mock_global_vars.gamemaster_role = role

        await check_and_print_if_one_or_zero_to_check_in()

        self.assertEqual(mock_safe_send.call_count, 2)
        mock_safe_send.assert_has_calls([
            mock.call(member1, "Just waiting on Bob to check in."),
            mock.call(member2, "Just waiting on Bob to check in.")
        ])

    @mock.patch('utils.player_utils.safe_send')
    @mock.patch('utils.player_utils.global_vars')
    async def test_zero_players_left(self, mock_global_vars, mock_safe_send):
        """Test message when zero players left to check in."""
        player1 = mock.Mock()
        player1.has_checked_in = True
        player1.alignment = "good"
        
        player2 = mock.Mock()
        player2.has_checked_in = True
        player2.alignment = "evil"
        
        mock_game = mock.Mock()
        mock_game.seatingOrder = [player1, player2]
        
        member1 = mock.Mock(spec=discord.Member)
        role = mock.Mock(spec=discord.Role)
        role.members = [member1]
        
        mock_global_vars.game = mock_game
        mock_global_vars.gamemaster_role = role

        await check_and_print_if_one_or_zero_to_check_in()

        mock_safe_send.assert_called_once_with(member1, "Everyone has checked in!")

    @mock.patch('utils.player_utils.safe_send')
    @mock.patch('utils.player_utils.global_vars')
    async def test_multiple_players_left(self, mock_global_vars, mock_safe_send):
        """Test no message when multiple players left to check in."""
        player1 = mock.Mock()
        player1.has_checked_in = False
        player1.alignment = "good"
        
        player2 = mock.Mock()
        player2.has_checked_in = False
        player2.alignment = "evil"
        
        mock_game = mock.Mock()
        mock_game.seatingOrder = [player1, player2]
        
        member1 = mock.Mock(spec=discord.Member)
        role = mock.Mock(spec=discord.Role)
        role.members = [member1]
        
        mock_global_vars.game = mock_game
        mock_global_vars.gamemaster_role = role

        await check_and_print_if_one_or_zero_to_check_in()

        mock_safe_send.assert_not_called()


if __name__ == '__main__':
    import unittest
    unittest.main()