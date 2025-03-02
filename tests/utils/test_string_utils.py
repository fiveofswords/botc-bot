"""
Tests for string utility functions used in the BOTC bot
"""

from unittest.mock import MagicMock, patch

import pytest

from bot_impl import str_cleanup, find_all, is_storyteller


def test_str_cleanup():
    """Test the str_cleanup function."""
    # Test with spaces
    assert str_cleanup("test string", [" "]) == "TestString"

    # Test with multiple characters
    assert str_cleanup("test-string,name", ["-", ","]) == "TestStringName"

    # Test with complex example (similar to role name cleanup)
    assert str_cleanup("virgin mary, mother-of-christ", [",", " ", "-", "'"]) == "VirginMaryMotherOfChrist"

    # Test with empty string
    assert str_cleanup("", [" "]) == ""

    # The actual implementation capitalizes the first letter of each segment
    # but doesn't preserve camelCase in the input
    assert str_cleanup("testString", ["-"]) == "Teststring"


def test_find_all():
    """Test the find_all function."""
    # Test finding multiple occurrences for 'a' in 'banana'
    result = list(find_all("a", "banana"))
    assert result == [1, 3, 5]

    # Test finding multiple occurrences in a longer string
    result = list(find_all("a", "abracadabra"))
    assert result == [0, 3, 5, 7, 10]

    # Test not finding any occurrences
    result = list(find_all("x", "banana"))
    assert result == []

    # Test with empty pattern string
    result = list(find_all("", "banana"))
    assert len(result) >= 6  # At minimum it should have indices 0-5

    # Test with empty search string
    result = list(find_all("a", ""))
    assert result == []


@pytest.mark.asyncio
@patch('bot_impl.generate_possibilities')
async def test_is_storyteller(mock_generate_possibilities):
    """Test the is_storyteller function."""
    # Test with direct storyteller references
    assert await is_storyteller("storytellers") is True
    assert await is_storyteller("the storytellers") is True
    assert await is_storyteller("storyteller") is True
    assert await is_storyteller("the storyteller") is True

    # Setup for testing with player names
    mock_server = MagicMock()
    mock_gamemaster_role = MagicMock()

    # Save original global values if needed to restore later
    import global_vars
    original_server = global_vars.server
    original_gamemaster_role = global_vars.gamemaster_role

    try:
        # Mock the global variables
        global_vars.server = mock_server
        global_vars.gamemaster_role = mock_gamemaster_role

        # Case 1: Player is a storyteller
        mock_member = MagicMock()
        mock_member.id = 12345
        mock_server.get_member.return_value = mock_member
        mock_member.roles = [mock_gamemaster_role]

        # Mock generate_possibilities to return a player
        mock_generate_possibilities.return_value = [mock_member]

        # Test with player name that matches a storyteller
        assert await is_storyteller("storyteller_name") is True

        # Case 2: Player is not a storyteller
        mock_member.roles = []
        assert await is_storyteller("player_name") is False

        # Case 3: Multiple matches
        mock_generate_possibilities.return_value = [mock_member, MagicMock()]
        assert await is_storyteller("ambiguous_name") is False

        # Case 4: No matches
        mock_generate_possibilities.return_value = []
        assert await is_storyteller("nonexistent_player") is False

    finally:
        # Restore global variables
        global_vars.server = original_server
        global_vars.gamemaster_role = original_gamemaster_role
