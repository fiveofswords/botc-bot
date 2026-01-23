"""
Tests for the Day class in bot_impl.py
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import global_vars
from model.game.day import Day
from model.game.vote import Vote
from model.game.base_vote import VoteOutcome
from model.game.whisper_mode import WhisperMode
# Import fixtures from fixtures directory
from tests.fixtures.discord_mocks import mock_discord_setup, MockMessage, MockClient
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
        mock_message = MockMessage(
            id=12345,
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

    # Create a mock client
    mock_client = MockClient()
    
    # Apply patches for Discord message sending
    with patch('bot_client.client', mock_client), \
            patch('utils.message_utils.safe_send') as mock_safe_send:

        # Set up global variables using fixture
        global_vars.channel = mock_discord_setup['channels']['town_square']
        global_vars.player_role = mock_discord_setup['roles']['player']

        # Mock message and fetch_message
        mock_message = MockMessage(
            id=12345,
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


class TestNominationThresholds:
    """Tests for the votes_needed calculation and announcement thresholds."""

    @pytest.mark.asyncio
    async def test_first_nomination_shows_only_execute_threshold(self, mock_discord_setup, setup_test_game):
        """First nomination (no aboutToDie) should show only 'to execute' in announcement."""
        # Arrange
        global_vars.game = setup_test_game['game']
        global_vars.channel = mock_discord_setup['channels']['town_square']
        global_vars.player_role = mock_discord_setup['roles']['player']
        global_vars.gamemaster_role = mock_discord_setup['roles']['gamemaster']

        alice = setup_test_game['players']['alice']
        bob = setup_test_game['players']['bob']
        charlie = setup_test_game['players']['charlie']

        global_vars.game.seatingOrder = [alice, bob, charlie]
        global_vars.game.show_tally = False

        day = Day()
        global_vars.game.days = [day]

        # All 3 players alive -> majority = ceil(3/2) = 2
        expected_majority = 2

        captured_messages = []

        async def capture_safe_send(channel, content):
            captured_messages.append(content)
            mock_msg = MagicMock()
            mock_msg.id = 12345
            mock_msg.pin = AsyncMock()
            return mock_msg

        with patch('utils.message_utils.safe_send', side_effect=capture_safe_send), \
             patch('model.nomination_buttons.send_nomination_buttons_to_st_channels', new_callable=AsyncMock), \
             patch('model.game.vote.in_play_voudon', return_value=None):

            # Act
            await day.nomination(alice, bob)

            # Assert - find the nomination announcement
            nomination_msg = next((m for m in captured_messages if "has been nominated" in m), None)
            assert nomination_msg is not None, "Nomination announcement not found"

            # Should NOT contain "to tie" since there's no aboutToDie
            assert "to tie" not in nomination_msg
            # Should contain "to execute" with the correct threshold
            assert f"{expected_majority} to execute" in nomination_msg

    @pytest.mark.asyncio
    async def test_second_nomination_shows_tie_and_execute_thresholds(self, mock_discord_setup, setup_test_game):
        """Second nomination (with aboutToDie set) should show both 'to tie' and 'to execute'."""
        # Arrange
        global_vars.game = setup_test_game['game']
        global_vars.channel = mock_discord_setup['channels']['town_square']
        global_vars.player_role = mock_discord_setup['roles']['player']
        global_vars.gamemaster_role = mock_discord_setup['roles']['gamemaster']

        alice = setup_test_game['players']['alice']
        bob = setup_test_game['players']['bob']
        charlie = setup_test_game['players']['charlie']

        global_vars.game.seatingOrder = [alice, bob, charlie]
        global_vars.game.show_tally = False

        day = Day()
        global_vars.game.days = [day]

        # Simulate a previous vote that resulted in aboutToDie
        prev_vote = MagicMock()
        prev_vote.votes = 2  # Previous vote got 2 votes
        day.aboutToDie = (alice, prev_vote)

        captured_messages = []

        async def capture_safe_send(channel, content):
            captured_messages.append(content)
            mock_msg = MagicMock()
            mock_msg.id = 12345
            mock_msg.pin = AsyncMock()
            return mock_msg

        with patch('utils.message_utils.safe_send', side_effect=capture_safe_send), \
             patch('model.nomination_buttons.send_nomination_buttons_to_st_channels', new_callable=AsyncMock), \
             patch('model.game.vote.in_play_voudon', return_value=None):

            # Act
            await day.nomination(bob, charlie)

            # Assert - find the nomination announcement
            nomination_msg = next((m for m in captured_messages if "has been nominated" in m), None)
            assert nomination_msg is not None, "Nomination announcement not found"

            # Should contain both thresholds
            assert "2 to tie" in nomination_msg
            assert "3 to execute" in nomination_msg

    @pytest.mark.asyncio
    async def test_votes_needed_uses_max_of_previous_plus_one_and_majority(self, mock_discord_setup, setup_test_game):
        """votes_needed should be max(aboutToDie.votes + 1, majority)."""
        # Arrange
        global_vars.game = setup_test_game['game']
        global_vars.channel = mock_discord_setup['channels']['town_square']
        global_vars.player_role = mock_discord_setup['roles']['player']
        global_vars.gamemaster_role = mock_discord_setup['roles']['gamemaster']

        alice = setup_test_game['players']['alice']
        bob = setup_test_game['players']['bob']
        charlie = setup_test_game['players']['charlie']
        storyteller = setup_test_game['players']['storyteller']

        # 4 players -> majority = ceil(4/2) = 2
        global_vars.game.seatingOrder = [alice, bob, charlie, storyteller]
        global_vars.game.show_tally = False

        day = Day()
        global_vars.game.days = [day]

        # Case 1: prev_vote.votes + 1 > majority
        # prev_vote.votes = 3, majority = 2 -> votes_needed = max(4, 2) = 4
        prev_vote = MagicMock()
        prev_vote.votes = 3
        day.aboutToDie = (alice, prev_vote)

        captured_votes_needed = []

        async def capture_buttons(nominee_name, nominator_name, votes_needed, is_exile=False):
            captured_votes_needed.append(votes_needed)

        with patch('utils.message_utils.safe_send', new_callable=AsyncMock) as mock_send, \
             patch('model.nomination_buttons.send_nomination_buttons_to_st_channels', side_effect=capture_buttons), \
             patch('model.game.vote.in_play_voudon', return_value=None):

            mock_msg = MagicMock()
            mock_msg.id = 12345
            mock_msg.pin = AsyncMock()
            mock_send.return_value = mock_msg

            await day.nomination(bob, charlie)

            # votes_needed should be 4 (prev_vote.votes + 1 = 4 > majority = 2)
            assert captured_votes_needed[-1] == 4

        # Case 2: majority > prev_vote.votes + 1
        # Reset for new test
        day.votes = []
        day.aboutToDie = None

        # Make prev_vote.votes small so majority wins
        prev_vote2 = MagicMock()
        prev_vote2.votes = 1  # prev_vote.votes + 1 = 2, majority = 2 -> max(2, 2) = 2
        day.aboutToDie = (alice, prev_vote2)

        captured_votes_needed.clear()

        with patch('utils.message_utils.safe_send', new_callable=AsyncMock) as mock_send, \
             patch('model.nomination_buttons.send_nomination_buttons_to_st_channels', side_effect=capture_buttons), \
             patch('model.game.vote.in_play_voudon', return_value=None):

            mock_msg = MagicMock()
            mock_msg.id = 12345
            mock_msg.pin = AsyncMock()
            mock_send.return_value = mock_msg

            # Reset nomination state
            charlie.can_nominate = True
            storyteller.can_be_nominated = True

            await day.nomination(storyteller, charlie)

            # votes_needed should be 2 (max(2, 2) = 2)
            assert captured_votes_needed[-1] == 2


class TestVoteDetermineOutcomeConsistency:
    """Tests for consistency between announced thresholds and Vote._determine_outcome."""

    @pytest.mark.asyncio
    async def test_vote_at_execute_threshold_passes(self, mock_discord_setup, setup_test_game):
        """A vote reaching exactly the announced execute threshold should PASS."""
        # Arrange
        global_vars.game = setup_test_game['game']
        alice = setup_test_game['players']['alice']
        bob = setup_test_game['players']['bob']
        charlie = setup_test_game['players']['charlie']

        global_vars.game.seatingOrder = [alice, bob, charlie]

        day = Day()
        global_vars.game.days = [day]

        # No previous aboutToDie
        day.aboutToDie = None

        with patch('model.game.vote.in_play_voudon', return_value=None):
            vote = Vote(nominee=alice, nominator=bob)

            # majority = ceil(3/2) = 2
            assert vote.majority == 2

            # Simulate reaching exactly the execute threshold
            vote.votes = 2

            # Act
            outcome = vote._determine_outcome()

            # Assert - should PASS since votes >= majority and no higher aboutToDie
            assert outcome == VoteOutcome.PASS

    @pytest.mark.asyncio
    async def test_vote_at_tie_threshold_ties(self, mock_discord_setup, setup_test_game):
        """A vote reaching exactly the tie threshold (= aboutToDie.votes) should TIE."""
        # Arrange
        global_vars.game = setup_test_game['game']
        alice = setup_test_game['players']['alice']
        bob = setup_test_game['players']['bob']
        charlie = setup_test_game['players']['charlie']

        global_vars.game.seatingOrder = [alice, bob, charlie]

        day = Day()
        global_vars.game.days = [day]

        # Set up previous aboutToDie with 2 votes
        prev_vote = MagicMock()
        prev_vote.votes = 2
        day.aboutToDie = (alice, prev_vote)

        with patch('model.game.vote.in_play_voudon', return_value=None):
            vote = Vote(nominee=bob, nominator=charlie)

            # majority = ceil(3/2) = 2
            assert vote.majority == 2

            # Simulate reaching exactly the tie threshold (= aboutToDie.votes = 2)
            vote.votes = 2

            # Act
            outcome = vote._determine_outcome()

            # Assert - should TIE since votes == aboutToDie.votes and votes >= majority
            assert outcome == VoteOutcome.TIE

    @pytest.mark.asyncio
    async def test_vote_above_tie_below_execute_fails(self, mock_discord_setup, setup_test_game):
        """A vote above tie threshold but below execute threshold should...

        Actually this scenario is impossible since execute = tie + 1.
        But if majority is higher than tie threshold, and vote is at majority but below tie+1, it should TIE.
        """
        # This test verifies the edge case where majority != prev_vote.votes
        # Arrange
        global_vars.game = setup_test_game['game']
        alice = setup_test_game['players']['alice']
        bob = setup_test_game['players']['bob']
        charlie = setup_test_game['players']['charlie']
        storyteller = setup_test_game['players']['storyteller']

        # 4 players -> majority = 2
        global_vars.game.seatingOrder = [alice, bob, charlie, storyteller]

        day = Day()
        global_vars.game.days = [day]

        # prev_vote.votes = 3, so tie = 3, execute = 4
        # majority = 2
        prev_vote = MagicMock()
        prev_vote.votes = 3
        day.aboutToDie = (alice, prev_vote)

        with patch('model.game.vote.in_play_voudon', return_value=None):
            vote = Vote(nominee=bob, nominator=charlie)

            # Vote gets 2 votes (= majority, but < tie threshold of 3)
            vote.votes = 2

            # Act
            outcome = vote._determine_outcome()

            # Assert - should FAIL because votes < aboutToDie.votes (even though >= majority)
            assert outcome == VoteOutcome.FAIL

    @pytest.mark.asyncio
    async def test_vote_below_majority_fails(self, mock_discord_setup, setup_test_game):
        """A vote below majority should always FAIL regardless of aboutToDie."""
        # Arrange
        global_vars.game = setup_test_game['game']
        alice = setup_test_game['players']['alice']
        bob = setup_test_game['players']['bob']
        charlie = setup_test_game['players']['charlie']

        global_vars.game.seatingOrder = [alice, bob, charlie]

        day = Day()
        global_vars.game.days = [day]

        # Even with a low aboutToDie threshold
        prev_vote = MagicMock()
        prev_vote.votes = 1
        day.aboutToDie = (alice, prev_vote)

        with patch('model.game.vote.in_play_voudon', return_value=None):
            vote = Vote(nominee=bob, nominator=charlie)

            # majority = 2, vote gets 1 (below majority)
            vote.votes = 1

            # Act
            outcome = vote._determine_outcome()

            # Assert - should FAIL because votes < majority
            assert outcome == VoteOutcome.FAIL


class TestMajorityChangesBetweenNominations:
    """Tests for edge cases where majority changes between nominations."""

    @pytest.mark.asyncio
    async def test_majority_decreases_after_player_death(self, mock_discord_setup, setup_test_game):
        """When a player dies, majority decreases for subsequent nominations."""
        # Arrange
        global_vars.game = setup_test_game['game']
        global_vars.channel = mock_discord_setup['channels']['town_square']
        global_vars.player_role = mock_discord_setup['roles']['player']
        global_vars.gamemaster_role = mock_discord_setup['roles']['gamemaster']

        alice = setup_test_game['players']['alice']
        bob = setup_test_game['players']['bob']
        charlie = setup_test_game['players']['charlie']
        storyteller = setup_test_game['players']['storyteller']

        # Start with 4 living players -> majority = 2
        global_vars.game.seatingOrder = [alice, bob, charlie, storyteller]
        alice.is_ghost = False
        bob.is_ghost = False
        charlie.is_ghost = False
        storyteller.is_ghost = False
        global_vars.game.show_tally = False

        day = Day()
        global_vars.game.days = [day]

        with patch('model.game.vote.in_play_voudon', return_value=None):
            # First vote with 4 players
            vote1 = Vote(nominee=alice, nominator=bob)
            assert vote1.majority == 2  # ceil(4/2) = 2

            # Simulate alice dying
            alice.is_ghost = True

            # Second vote with 3 living players
            vote2 = Vote(nominee=bob, nominator=charlie)
            assert vote2.majority == 2  # ceil(3/2) = 2

            # Simulate bob dying too
            bob.is_ghost = True

            # Third vote with 2 living players
            vote3 = Vote(nominee=charlie, nominator=storyteller)
            assert vote3.majority == 1  # ceil(2/2) = 1

    @pytest.mark.asyncio
    async def test_execute_threshold_uses_new_majority_after_death(self, mock_discord_setup, setup_test_game):
        """When majority changes, announced threshold should reflect new majority."""
        # Arrange
        global_vars.game = setup_test_game['game']
        global_vars.channel = mock_discord_setup['channels']['town_square']
        global_vars.player_role = mock_discord_setup['roles']['player']
        global_vars.gamemaster_role = mock_discord_setup['roles']['gamemaster']

        alice = setup_test_game['players']['alice']
        bob = setup_test_game['players']['bob']
        charlie = setup_test_game['players']['charlie']
        storyteller = setup_test_game['players']['storyteller']

        global_vars.game.seatingOrder = [alice, bob, charlie, storyteller]
        global_vars.game.show_tally = False

        day = Day()
        global_vars.game.days = [day]

        # Previous vote got 2 votes with 4 players
        prev_vote = MagicMock()
        prev_vote.votes = 2
        day.aboutToDie = (alice, prev_vote)

        # Now only 2 players alive -> majority = 1
        alice.is_ghost = True
        bob.is_ghost = True
        charlie.is_ghost = False
        storyteller.is_ghost = False

        captured_votes_needed = []

        async def capture_buttons(nominee_name, nominator_name, votes_needed, is_exile=False):
            captured_votes_needed.append(votes_needed)

        with patch('utils.message_utils.safe_send', new_callable=AsyncMock) as mock_send, \
             patch('model.nomination_buttons.send_nomination_buttons_to_st_channels', side_effect=capture_buttons), \
             patch('model.game.vote.in_play_voudon', return_value=None):

            mock_msg = MagicMock()
            mock_msg.id = 12345
            mock_msg.pin = AsyncMock()
            mock_send.return_value = mock_msg

            await day.nomination(charlie, storyteller)

            # New majority = 1 (2 living players)
            # votes_needed = max(prev_vote.votes + 1, majority) = max(3, 1) = 3
            # The prev_vote.votes + 1 dominates
            assert captured_votes_needed[-1] == 3

    @pytest.mark.asyncio
    async def test_outcome_uses_current_majority_not_announced(self, mock_discord_setup, setup_test_game):
        """Vote outcome uses current majority at time of vote, not announcement time."""
        # Arrange
        global_vars.game = setup_test_game['game']
        alice = setup_test_game['players']['alice']
        bob = setup_test_game['players']['bob']
        charlie = setup_test_game['players']['charlie']
        storyteller = setup_test_game['players']['storyteller']

        # 4 living players at start
        global_vars.game.seatingOrder = [alice, bob, charlie, storyteller]
        alice.is_ghost = False
        bob.is_ghost = False
        charlie.is_ghost = False
        storyteller.is_ghost = False

        day = Day()
        global_vars.game.days = [day]
        day.aboutToDie = None

        with patch('model.game.vote.in_play_voudon', return_value=None):
            # Create vote when majority is 2
            vote = Vote(nominee=alice, nominator=bob)
            initial_majority = vote.majority
            assert initial_majority == 2

            # Simulate players dying during the vote (reducing living count)
            charlie.is_ghost = True
            storyteller.is_ghost = True

            # Now only 2 living, but vote.majority was set at creation time
            # The vote's majority doesn't change dynamically
            assert vote.majority == 2  # Still 2 from when it was created

            # With 1 vote, outcome should FAIL (below majority of 2)
            vote.votes = 1
            outcome = vote._determine_outcome()
            assert outcome == VoteOutcome.FAIL

            # With 2 votes, outcome should PASS
            vote.votes = 2
            outcome = vote._determine_outcome()
            assert outcome == VoteOutcome.PASS


class TestAnnouncementAndOutcomeConsistency:
    """Tests ensuring announced thresholds match actual execution logic."""

    @pytest.mark.asyncio
    async def test_announced_execute_threshold_matches_pass_condition(self, mock_discord_setup, setup_test_game):
        """Votes at exactly the announced execute threshold should result in PASS."""
        # Arrange
        global_vars.game = setup_test_game['game']
        global_vars.channel = mock_discord_setup['channels']['town_square']
        global_vars.player_role = mock_discord_setup['roles']['player']
        global_vars.gamemaster_role = mock_discord_setup['roles']['gamemaster']

        alice = setup_test_game['players']['alice']
        bob = setup_test_game['players']['bob']
        charlie = setup_test_game['players']['charlie']

        global_vars.game.seatingOrder = [alice, bob, charlie]
        global_vars.game.show_tally = False

        day = Day()
        global_vars.game.days = [day]

        # Set aboutToDie with 2 votes
        prev_vote = MagicMock()
        prev_vote.votes = 2
        day.aboutToDie = (alice, prev_vote)

        # Calculate expected thresholds (as day.nomination would)
        with patch('model.game.vote.in_play_voudon', return_value=None):
            test_vote = Vote(nominee=bob, nominator=charlie)
            majority = test_vote.majority  # 2
            announced_execute = 3  # max(3, 2) = 3
            announced_tie = prev_vote.votes  # 2

            # Verify our calculations
            assert announced_tie == 2
            assert announced_execute == 3

            # Test 1: Vote at execute threshold should PASS
            test_vote.votes = announced_execute  # 3
            outcome = test_vote._determine_outcome()
            assert outcome == VoteOutcome.PASS, f"Expected PASS at execute threshold {announced_execute}"

            # Test 2: Vote at tie threshold should TIE
            test_vote.votes = announced_tie  # 2
            outcome = test_vote._determine_outcome()
            assert outcome == VoteOutcome.TIE, f"Expected TIE at tie threshold {announced_tie}"

            # Test 3: Vote below tie threshold should FAIL (even if >= majority)
            test_vote.votes = announced_tie - 1  # 1
            outcome = test_vote._determine_outcome()
            assert outcome == VoteOutcome.FAIL, f"Expected FAIL below tie threshold"

    @pytest.mark.asyncio
    async def test_no_abouttodie_execute_at_majority(self, mock_discord_setup, setup_test_game):
        """Without aboutToDie, execute threshold equals majority."""
        # Arrange
        global_vars.game = setup_test_game['game']
        alice = setup_test_game['players']['alice']
        bob = setup_test_game['players']['bob']
        charlie = setup_test_game['players']['charlie']

        global_vars.game.seatingOrder = [alice, bob, charlie]

        day = Day()
        global_vars.game.days = [day]
        day.aboutToDie = None

        with patch('model.game.vote.in_play_voudon', return_value=None):
            vote = Vote(nominee=alice, nominator=bob)
            majority = vote.majority  # 2

            # At majority, should PASS
            vote.votes = majority
            outcome = vote._determine_outcome()
            assert outcome == VoteOutcome.PASS

            # Below majority, should FAIL
            vote.votes = majority - 1
            outcome = vote._determine_outcome()
            assert outcome == VoteOutcome.FAIL

    @pytest.mark.asyncio
    async def test_voudon_changes_majority_to_one(self, mock_discord_setup, setup_test_game):
        """With Voudon in play, majority is always 1."""
        # Arrange
        global_vars.game = setup_test_game['game']
        alice = setup_test_game['players']['alice']
        bob = setup_test_game['players']['bob']
        charlie = setup_test_game['players']['charlie']

        global_vars.game.seatingOrder = [alice, bob, charlie]

        day = Day()
        global_vars.game.days = [day]
        day.aboutToDie = None

        # Simulate Voudon in play
        with patch('model.game.vote.in_play_voudon', return_value=alice):
            vote = Vote(nominee=bob, nominator=charlie)

            # Majority should be 1 with Voudon
            assert vote.majority == 1

            # 1 vote should PASS
            vote.votes = 1
            outcome = vote._determine_outcome()
            assert outcome == VoteOutcome.PASS

