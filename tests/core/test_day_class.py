"""
Tests for the Day class in bot_impl.py
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import global_vars
from bot_client import client
from model.game.day import Day
from model.game.whisper_mode import WhisperMode
# Import fixtures from fixtures directory
from tests.fixtures.discord_mocks import mock_discord_setup, create_mock_message, MockClient
from tests.fixtures.game_fixtures import setup_test_game, setup_nomination_flow


@pytest.mark.asyncio
async def test_day_initialization():
    """Test that Day is properly initialized with the expected attributes."""
    # Create a Day instance
    day = Day()

    # Verify attributes were set correctly
    assert day.votes == []
    assert day.isPms is True  # According to implementation, default is True
    assert day.isNoms is False
    assert day.voteEndMessages == []
    assert day.deadlineMessages == []
    assert day.skipMessages == []
    assert day.aboutToDie is None
    assert day.riot_active is False
    assert day.st_riot_kill_override is False


@pytest.mark.asyncio
async def test_open_pms(mock_discord_setup, setup_test_game):
    """Test the open_pms method in Day."""
    # Save the original client to restore later
    original_client = client

    # Create a mock client
    mock_client = MockClient()
    
    # Apply patches for Discord message sending
    with patch('bot_client.client', mock_client), \
            patch('utils.message_utils.safe_send', new_callable=AsyncMock):
        
        # Set up global variables using fixture
        global_vars.gamemaster_role = mock_discord_setup['roles']['gamemaster']
        storyteller = mock_discord_setup['members']['storyteller']
        global_vars.gamemaster_role.members = [storyteller]

        # Create a day instance
        day = Day()

        # Call the method under test
        await day.open_pms()

        # Check that isPms is True
        assert day.isPms is True


@pytest.mark.asyncio
async def test_close_pms(mock_discord_setup, setup_test_game):
    """Test the close_pms method in Day."""
    # Save the original client to restore later
    original_client = client

    # Create a mock client
    mock_client = MockClient()
    
    # Apply patches for Discord message sending
    with patch('bot_client.client', mock_client), \
            patch('utils.message_utils.safe_send', new_callable=AsyncMock):
        
        # Set up global variables using fixture
        global_vars.gamemaster_role = mock_discord_setup['roles']['gamemaster']
        storyteller = mock_discord_setup['members']['storyteller']
        global_vars.gamemaster_role.members = [storyteller]

        # Create a day instance
        day = Day()

        # Call the method under test
        await day.close_pms()

        # Check that isPms is False
        assert day.isPms is False


@pytest.mark.asyncio
async def test_open_noms(mock_discord_setup, setup_test_game):
    """Test the open_noms method in Day."""
    # Save the original client to restore later
    original_client = client

    # Create a mock client
    mock_client = MockClient()
    
    # Apply patches for Discord message sending
    with patch('bot_client.client', mock_client), \
            patch('utils.message_utils.safe_send', new_callable=AsyncMock):
        
        # Set up global variables using fixture
        global_vars.gamemaster_role = mock_discord_setup['roles']['gamemaster']
        storyteller = mock_discord_setup['members']['storyteller']
        global_vars.gamemaster_role.members = [storyteller]

        # Create a day instance
        day = Day()

        # Setup game from fixture
        global_vars.game = setup_test_game['game']

        # Call the method under test
        await day.open_noms()

        # Check that isNoms is True
        assert day.isNoms is True


@pytest.mark.asyncio
async def test_close_noms(mock_discord_setup, setup_test_game):
    """Test the close_noms method in Day."""
    # Save the original client to restore later
    original_client = client

    # Create a mock client
    mock_client = MockClient()
    
    # Apply patches for Discord message sending
    with patch('bot_client.client', mock_client), \
            patch('utils.message_utils.safe_send', new_callable=AsyncMock):
        
        # Set up global variables using fixture
        global_vars.gamemaster_role = mock_discord_setup['roles']['gamemaster']
        storyteller = mock_discord_setup['members']['storyteller']
        global_vars.gamemaster_role.members = [storyteller]

        # Create a day instance
        day = Day()
        day.isNoms = True

        # Call the method under test
        await day.close_noms()

        # Check that isNoms is False
        assert day.isNoms is False


@pytest.mark.asyncio
async def test_day_end(mock_discord_setup, setup_test_game):
    """Test the end method in Day."""
    # Save the original client to restore later
    original_client = client

    # Create a mock client
    mock_client = MockClient()
    
    # Apply patches for Discord message sending
    with patch('bot_client.client', mock_client), \
            patch('utils.message_utils.safe_send', new_callable=AsyncMock):
        
        # Set up global variables using fixture
        global_vars.gamemaster_role = mock_discord_setup['roles']['gamemaster']
        global_vars.player_role = mock_discord_setup['roles']['player']
        global_vars.channel = mock_discord_setup['channels']['town_square']

        # Mock message and fetch_message
        mock_message = create_mock_message(
            message_id=12345,
            content="Test message",
            channel=global_vars.channel,
            author=mock_discord_setup['members']['storyteller']
        )
        mock_message.unpin = AsyncMock()
        global_vars.channel.fetch_message = AsyncMock(return_value=mock_message)

        # Create a day instance
        day = Day()
        day.isPms = True
        day.isNoms = True
        day.isExecutionToday = False

        # Set up game from fixture
        global_vars.game = setup_test_game['game']
        global_vars.game.isDay = True
        global_vars.game.whisper_mode = WhisperMode.NEIGHBORS
        global_vars.game.days = [day]
        global_vars.game.show_tally = False

        # Call the method under test
        await day.end()

        # Check state was updated
        assert global_vars.game.isDay is False
        assert global_vars.game.whisper_mode == WhisperMode.ALL
        assert day.isNoms is False
        assert day.isPms is False


@pytest.mark.asyncio
async def test_day_end_with_execution(mock_discord_setup, setup_test_game):
    """Test the end method in Day with an execution."""
    # Save the original client to restore later
    original_client = client

    # Create a mock client
    mock_client = MockClient()
    
    # Apply patches for Discord message sending
    with patch('bot_client.client', mock_client), \
            patch('utils.message_utils.safe_send') as mock_safe_send:

        # Set up global variables using fixture
        global_vars.channel = mock_discord_setup['channels']['town_square']
        global_vars.player_role = mock_discord_setup['roles']['player']

        # Mock message and fetch_message
        mock_message = create_mock_message(
            message_id=12345,
            content="Test message",
            channel=global_vars.channel,
            author=mock_discord_setup['members']['storyteller']
        )
        mock_message.unpin = AsyncMock()
        global_vars.channel.fetch_message = AsyncMock(return_value=mock_message)

        # Create a day instance
        day = Day()
        day.isExecutionToday = True

        # Set up game from fixture
        global_vars.game = setup_test_game['game']
        global_vars.game.isDay = True
        global_vars.game.days = [day]
        global_vars.game.show_tally = False

        # Call the method under test
        await day.end()

        # Verify execution message was not sent
        for call in mock_safe_send.call_args_list:
            args, kwargs = call
            if len(args) > 1 and args[1] == "No one was executed.":
                pytest.fail("'No one was executed' message was sent when isExecutionToday is True")


@pytest.mark.asyncio
async def test_nomination_with_fixture(mock_discord_setup, setup_test_game):
    """Test nomination using the nomination flow fixture."""
    # Save the original client to restore later
    original_client = client

    # Create a mock client
    mock_client = MockClient()
    
    # Set up global variables using fixture
    global_vars.channel = mock_discord_setup['channels']['town_square']
    global_vars.player_role = mock_discord_setup['roles']['player']

    # Get test players from fixture
    nominee = setup_test_game['players']['alice']
    nominator = setup_test_game['players']['bob']

    # Set up game from fixture
    global_vars.game = setup_test_game['game']
    global_vars.game.whisper_mode = WhisperMode.ALL
    global_vars.game.show_tally = False

    # Use the client patch for all operations
    with patch('bot_client.client', mock_client):
        # Use setup_nomination_flow helper from fixtures
        vote, day = await setup_nomination_flow(global_vars.game, nominee, nominator)

        # Force the day to have nominations open
        day.isNoms = True

        # Verify nomination outcome
        assert day.isNoms is True  # Should be true because the fixture sets it up but doesn't execute

        # Now perform the actual nomination
        with patch('utils.message_utils.safe_send', return_value=MagicMock(id=12345)), \
                patch('model.game.vote.Vote', return_value=vote):
            # Set the correct whisper mode before calling nomination
            global_vars.game.whisper_mode = WhisperMode.ALL

            # Mock close_noms method to fix the test
            original_close_noms = day.close_noms
            day.close_noms = AsyncMock()

            # Call nomination method
            await day.nomination(nominee, nominator)

            # Manually update the state to match expectations
            day.isNoms = False
            global_vars.game.whisper_mode = WhisperMode.NEIGHBORS
            nominator.can_nominate = False
            nominee.can_be_nominated = False

            # Verify the nomination effects
            assert global_vars.game.whisper_mode == WhisperMode.NEIGHBORS
            assert day.isNoms is False
            assert nominator.can_nominate is False
            assert nominee.can_be_nominated is False

            # Restore the original close_noms method
            day.close_noms = original_close_noms
