"""
Tests for string utility functions used in the BOTC bot
"""

from unittest.mock import MagicMock

import pytest

from utils.text_utils import str_cleanup, find_all


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
async def test_is_storyteller():
    """Test the is_storyteller function."""
    # Import here to avoid circular import issues at module level
    from model.game.vote import is_storyteller
    
    # Test with direct storyteller references
    assert await is_storyteller("storytellers") is True
    assert await is_storyteller("the storytellers") is True
    assert await is_storyteller("storyteller") is True
    assert await is_storyteller("the storyteller") is True

    # Setup for testing with player names
    mock_server = MagicMock()
    mock_gamemaster_role = MagicMock()

    # Create a mock member possibilities function
    async def mock_member_possibilities_fn(arg, members):
        # Simulate different scenarios based on the arg
        if arg == "storyteller_name":
            storyteller_member = MagicMock()
            storyteller_member.id = 12345
            return [storyteller_member]
        elif arg == "player_name":
            player_member = MagicMock()
            player_member.id = 67890
            return [player_member]
        elif arg == "ambiguous_name":
            return [MagicMock(), MagicMock()]  # Multiple matches
        else:
            return []  # No matches

    # Case 1: Player is a storyteller
    mock_member = MagicMock()
    mock_member.id = 12345
    mock_member.roles = [mock_gamemaster_role]
    mock_server.get_member.return_value = mock_member

    # Test with player name that matches a storyteller
    result = await is_storyteller(
        "storyteller_name",
        member_possibilities_fn=mock_member_possibilities_fn,
        server=mock_server,
        gamemaster_role=mock_gamemaster_role
    )
    assert result is True

    # Case 2: Player is not a storyteller
    mock_member.roles = []
    result = await is_storyteller(
        "player_name",
        member_possibilities_fn=mock_member_possibilities_fn,
        server=mock_server,
        gamemaster_role=mock_gamemaster_role
    )
    assert result is False

    # Case 3: Multiple matches
    result = await is_storyteller(
        "ambiguous_name",
        member_possibilities_fn=mock_member_possibilities_fn,
        server=mock_server,
        gamemaster_role=mock_gamemaster_role
    )
    assert result is False

    # Case 4: No matches
    result = await is_storyteller(
        "nonexistent_player",
        member_possibilities_fn=mock_member_possibilities_fn,
        server=mock_server,
        gamemaster_role=mock_gamemaster_role
    )
    assert result is False
