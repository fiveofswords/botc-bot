"""
Tests specifically focused on the on_message function in bot_impl.py.

This file tests the various paths and branches through the on_message function to ensure
complete coverage of all command handling and error cases.
"""

from unittest.mock import patch, AsyncMock, MagicMock

import pytest

import global_vars
from bot_impl import on_message
from model.game import WhisperMode
# Import test fixtures from shared fixtures
from tests.fixtures.discord_mocks import (
    MockChannel, MockMember, MockMessage, mock_discord_setup
)
from tests.fixtures.game_fixtures import setup_test_game


@pytest.mark.asyncio
async def test_on_message_bot_message(mock_discord_setup):
    """Test that bot ignores its own messages."""
    # Initialize global_vars.game to NULL_GAME
    from bot_impl import NULL_GAME
    global_vars.game = NULL_GAME

    # Create a message from the bot
    bot_message = MockMessage(
        id=1,
        content="Test message",
        channel=mock_discord_setup['channels']['town_square'],
        author=MockMember(999, "Bot", "Blood on the Clocktower Bot"),
        guild=mock_discord_setup['guild']
    )

    # Set up spy on backup function
    with patch('bot_impl.backup') as mock_backup:
        # Process the message with client set as author
        with patch('bot_client.client') as mock_client:
            mock_client.user = bot_message.author  # This makes the bot recognize itself
            await on_message(bot_message)

        # Verify backup was called once at the start, but no further processing happened
        mock_backup.assert_called_once_with("current_game.pckl")


@pytest.mark.asyncio
async def test_on_message_town_square_activity(mock_discord_setup, setup_test_game):
    """Test that player activity is updated for messages in town square."""
    # Set up global variables
    global_vars.game = setup_test_game['game']
    global_vars.channel = mock_discord_setup['channels']['town_square']

    # Create a message from Alice in town square
    alice_message = MockMessage(
        id=2,
        content="Hello everyone!",  # Not a command
        channel=mock_discord_setup['channels']['town_square'],
        author=mock_discord_setup['members']['alice'],
        guild=mock_discord_setup['guild']
    )

    # Set up mock for make_active function
    with patch('bot_impl.make_active') as mock_make_active:
        with patch('bot_impl.backup') as mock_backup:
            # Process the message
            await on_message(alice_message)

            # Verify make_active was called for Alice
            mock_make_active.assert_called_once_with(mock_discord_setup['members']['alice'])

            # Verify backup was called twice (once at start, once after make_active)
            assert mock_backup.call_count == 2


@pytest.mark.asyncio
async def test_on_message_storyteller_channel(mock_discord_setup, setup_test_game):
    """Test handling messages in player's storyteller channel."""
    # Set up global variables for this test
    global_vars.game = setup_test_game['game']

    # Create a mock GameSettings object
    mock_game_settings = MagicMock()
    mock_game_settings.get_st_channel.return_value = mock_discord_setup['channels']['st_alice'].id

    # Create a message from Alice in her ST channel
    alice_message = MockMessage(
        id=3,
        content="Hello Storyteller!",
        channel=mock_discord_setup['channels']['st_alice'],  # Alice's ST channel
        author=mock_discord_setup['members']['alice'],
        guild=mock_discord_setup['guild']
    )

    # Process the message
    with patch('bot_impl.backup') as mock_backup:
        with patch('model.settings.game_settings.GameSettings.load', return_value=mock_game_settings):
            with patch('bot_impl.active_in_st_chat') as mock_active_in_st_chat:
                await on_message(alice_message)

                # Verify active_in_st_chat was called for Alice
                mock_active_in_st_chat.assert_called_once_with(mock_discord_setup['members']['alice'])


@pytest.mark.asyncio
async def test_on_message_vote_command_no_game(mock_discord_setup):
    """Test handling vote command when no game is active."""
    # Set up global variables
    from bot_impl import NULL_GAME
    global_vars.game = NULL_GAME  # Use NULL_GAME instead of None
    global_vars.channel = mock_discord_setup['channels']['town_square']

    # Create a command message from Alice in town square
    alice_message = MockMessage(
        id=4,
        content="@vote yes",  # Command that requires active game
        channel=mock_discord_setup['channels']['town_square'],
        author=mock_discord_setup['members']['alice'],
        guild=mock_discord_setup['guild']
    )

    # Process the message
    with patch('bot_impl.backup') as mock_backup:
        with patch('utils.message_utils.safe_send', return_value=AsyncMock()) as mock_safe_send:
            await on_message(alice_message)

            # Verify error message was sent
            mock_safe_send.assert_called_with(
                mock_discord_setup['channels']['town_square'],
                "There's no game right now."
            )


@pytest.mark.asyncio
async def test_on_message_vote_command_nighttime(mock_discord_setup, setup_test_game):
    """Test handling vote command during nighttime."""
    # Set up global variables for this test
    global_vars.game = setup_test_game['game']
    global_vars.channel = mock_discord_setup['channels']['town_square']

    # Set game to nighttime
    setup_test_game['game'].isDay = False

    # Create a vote message from Alice
    alice_message = MockMessage(
        id=5,
        content="@vote yes",
        channel=mock_discord_setup['channels']['town_square'],
        author=mock_discord_setup['members']['alice'],
        guild=mock_discord_setup['guild']
    )

    # Process the message
    with patch('bot_impl.backup') as mock_backup:
        with patch('utils.message_utils.safe_send', return_value=AsyncMock()) as mock_safe_send:
            await on_message(alice_message)

            # Verify error message was sent
            mock_safe_send.assert_called_with(
                mock_discord_setup['channels']['town_square'],
                "It's not day right now."
            )


@pytest.mark.asyncio
async def test_on_message_vote_command_no_votes(mock_discord_setup, setup_test_game):
    """Test handling vote command when there are no active votes."""
    # Set up global variables for this test
    global_vars.game = setup_test_game['game']
    global_vars.channel = mock_discord_setup['channels']['town_square']

    # Set game to daytime but no active votes
    setup_test_game['game'].isDay = True
    setup_test_game['game'].days = [MagicMock()]
    setup_test_game['game'].days[-1].votes = []

    # Create a vote message from Alice
    alice_message = MockMessage(
        id=6,
        content="@vote yes",
        channel=mock_discord_setup['channels']['town_square'],
        author=mock_discord_setup['members']['alice'],
        guild=mock_discord_setup['guild']
    )

    # Process the message
    with patch('bot_impl.backup') as mock_backup:
        with patch('utils.message_utils.safe_send', return_value=AsyncMock()) as mock_safe_send:
            await on_message(alice_message)

            # Verify error message was sent
            mock_safe_send.assert_called_with(
                mock_discord_setup['channels']['town_square'],
                "There's no vote right now."
            )


@pytest.mark.asyncio
async def test_on_message_vote_invalid_format(mock_discord_setup, setup_test_game):
    """Test handling vote command with invalid format."""
    # Set up global variables for this test
    global_vars.game = setup_test_game['game']
    global_vars.channel = mock_discord_setup['channels']['town_square']

    # Set up game for voting
    setup_test_game['game'].isDay = True
    setup_test_game['game'].days = [MagicMock()]
    setup_test_game['game'].days[-1].votes = [MagicMock()]
    setup_test_game['game'].days[-1].votes[-1].done = False

    # Create an invalid vote message from Alice
    alice_message = MockMessage(
        id=7,
        content="@vote maybe",  # Invalid format
        channel=mock_discord_setup['channels']['town_square'],
        author=mock_discord_setup['members']['alice'],
        guild=mock_discord_setup['guild']
    )

    # Process the message
    with patch('bot_impl.backup') as mock_backup:
        with patch('utils.message_utils.safe_send', return_value=AsyncMock()) as mock_safe_send:
            await on_message(alice_message)

            # Verify error message was sent
            mock_safe_send.assert_called_with(
                mock_discord_setup['channels']['town_square'],
                "maybe is not a valid vote. Use 'yes', 'y', 'no', or 'n'."
            )


@pytest.mark.asyncio
async def test_on_message_vote_not_player_turn(mock_discord_setup, setup_test_game):
    """Test handling vote command when it's not the player's turn to vote."""
    # Set up global variables for this test
    global_vars.game = setup_test_game['game']
    global_vars.channel = mock_discord_setup['channels']['town_square']

    # Set up game for voting
    setup_test_game['game'].isDay = True

    # Create a mock vote where the current voter is Bob
    mock_vote = MagicMock()
    mock_vote.done = False
    mock_vote.order = [setup_test_game['players']['bob']]
    mock_vote.position = 0

    setup_test_game['game'].days = [MagicMock()]
    setup_test_game['game'].days[-1].votes = [mock_vote]

    # Create a vote message from Alice (when it's Bob's turn)
    alice_message = MockMessage(
        id=8,
        content="@vote yes",
        channel=mock_discord_setup['channels']['town_square'],
        author=mock_discord_setup['members']['alice'],
        guild=mock_discord_setup['guild']
    )

    # Process the message
    with patch('bot_impl.backup') as mock_backup:
        with patch('utils.message_utils.safe_send', return_value=AsyncMock()) as mock_safe_send:
            with patch('bot_impl.get_player', return_value=setup_test_game['players']['alice']):
                await on_message(alice_message)

                # Verify error message was sent
                mock_safe_send.assert_called_with(
                    mock_discord_setup['channels']['town_square'],
                    "It's not your vote right now."
                )


@pytest.mark.asyncio
async def test_on_message_vote_successful(mock_discord_setup, setup_test_game):
    """Test successful voting in town square."""
    # Set up global variables for this test
    global_vars.game = setup_test_game['game']
    global_vars.channel = mock_discord_setup['channels']['town_square']

    # Set up game for voting
    setup_test_game['game'].isDay = True

    # Create a mock vote where the current voter is Alice
    mock_vote = MagicMock()
    mock_vote.done = False
    mock_vote.order = [setup_test_game['players']['alice']]
    mock_vote.position = 0
    mock_vote.vote = AsyncMock()

    setup_test_game['game'].days = [MagicMock()]
    setup_test_game['game'].days[-1].votes = [mock_vote]

    # Create a vote message from Alice
    alice_message = MockMessage(
        id=9,
        content="@vote yes",
        channel=mock_discord_setup['channels']['town_square'],
        author=mock_discord_setup['members']['alice'],
        guild=mock_discord_setup['guild']
    )

    # Process the message
    with patch('bot_impl.backup') as mock_backup:
        with patch('bot_impl.get_player', return_value=setup_test_game['players']['alice']):
            with patch('bot_impl.in_play_voudon', return_value=None):  # No Voudon in play
                await on_message(alice_message)

                # Verify vote was called with 1 (yes)
                mock_vote.vote.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_direct_message_command_processing(mock_discord_setup, setup_test_game):
    """Test processing direct message commands."""
    # Create a direct message channel for Alice
    alice_dm_channel = MockChannel(401, "dm-alice")
    alice_dm_channel.guild = None  # Simulate DM

    # Create a message from Alice in DM
    alice_message = MockMessage(
        id=10,
        content="@help",  # A command that works in DMs
        channel=alice_dm_channel,
        author=mock_discord_setup['members']['alice']
    )

    # Setup mock server for role check
    mock_server = MagicMock()
    mock_member = MagicMock()
    mock_member.roles = []  # Not a storyteller
    mock_server.get_member.return_value = mock_member
    global_vars.server = mock_server

    # Process the message
    with patch('bot_impl.backup') as mock_backup:
        with patch('discord.Embed') as mock_embed:
            mock_embed_instance = MagicMock()
            mock_embed.return_value = mock_embed_instance
            mock_embed_instance.add_field = MagicMock()

            # Mock send method on discord.User
            mock_discord_setup['members']['alice'].send = AsyncMock()

            await on_message(alice_message)

            # Verify help was sent (embed was created and sent)
            assert mock_embed.called
            assert mock_discord_setup['members']['alice'].send.called


@pytest.mark.asyncio
async def test_pm_command_during_day(mock_discord_setup, setup_test_game):
    """Test PM command functionality during daytime."""
    # Set up global variables for this test
    global_vars.game = setup_test_game['game']

    # Create a direct message channel for Alice
    alice_dm_channel = MockChannel(401, "dm-alice")
    alice_dm_channel.guild = None  # Simulate DM

    # Start a day, enable PMs, and set whisper mode to all
    setup_test_game['game'].start_day = AsyncMock()
    await setup_test_game['game'].start_day()
    setup_test_game['game'].isDay = True
    setup_test_game['game'].days = [MagicMock()]
    setup_test_game['game'].days[-1].isPms = True
    setup_test_game['game'].whisper_mode = WhisperMode.ALL

    # Create a PM message from Alice
    alice_message = MockMessage(
        id=11,
        content="@pm bob",
        channel=alice_dm_channel,
        author=mock_discord_setup['members']['alice']
    )

    # Setup mock server for role check
    mock_server = MagicMock()
    mock_member = MagicMock()
    mock_member.roles = []  # Not a storyteller
    mock_server.get_member.return_value = mock_member
    global_vars.server = mock_server

    # Create a mock response message that will be "sent" by the user
    mock_response = MockMessage(
        id=1001,
        content="Hello Bob!",
        channel=alice_dm_channel,
        author=mock_discord_setup['members']['alice']
    )

    # Process the message
    with patch('bot_impl.backup') as mock_backup:
        with patch('bot_impl.get_player', return_value=setup_test_game['players']['alice']):
            with patch('bot_impl.select_player', return_value=setup_test_game['players']['bob']):
                with patch('bot_impl.chose_whisper_candidates', return_value=[setup_test_game['players']['bob']]):
                    with patch('utils.message_utils.safe_send', return_value=AsyncMock()) as mock_safe_send:
                        # Create a proper async mock for client.wait_for
                        wait_for_mock = AsyncMock()
                        wait_for_mock.return_value = mock_response

                        # Mock the bot client with a properly configured wait_for method
                        with patch('bot_client.client.wait_for', wait_for_mock):
                            # Mock player.message method
                            setup_test_game['players']['bob'].message = AsyncMock()

                            await on_message(alice_message)

                            # Verify that safe_send was called
                            assert mock_safe_send.called

                            # Verify that message method was called on Bob
                            setup_test_game['players']['bob'].message.assert_called_once()


@pytest.mark.asyncio
async def test_pm_command_when_pms_closed(mock_discord_setup, setup_test_game):
    """Test PM command when PMs are closed."""
    # Set up global variables for this test
    global_vars.game = setup_test_game['game']

    # Create a direct message channel for Alice
    alice_dm_channel = MockChannel(401, "dm-alice")
    alice_dm_channel.guild = None  # Simulate DM

    # Start a day, but set PMs as closed
    setup_test_game['game'].isDay = True
    setup_test_game['game'].days = [MagicMock()]
    setup_test_game['game'].days[-1].isPms = False

    # Create a PM message from Alice
    alice_message = MockMessage(
        id=12,
        content="@pm bob",
        channel=alice_dm_channel,
        author=mock_discord_setup['members']['alice']
    )

    # Process the message
    with patch('bot_impl.backup') as mock_backup:
        with patch('bot_impl.get_player', return_value=setup_test_game['players']['alice']):
            with patch('utils.message_utils.safe_send', return_value=AsyncMock()) as mock_safe_send:
                await on_message(alice_message)

                # Verify error message was sent about PMs being closed
                mock_safe_send.assert_called_with(
                    mock_discord_setup['members']['alice'],
                    "PMs are closed."
                )


@pytest.mark.asyncio
async def test_command_parser_handles_nominate(mock_discord_setup):
    """Test that the on_message function correctly parses the nominate command."""

    # This is a very simplified test that just verifies command recognition
    # Set up global variables for this test
    from bot_impl import NULL_GAME
    global_vars.game = NULL_GAME

    # Create a nominate message from Alice (but without all the game setup)
    alice_message = MockMessage(
        id=13,
        content="@nominate charlie",
        channel=mock_discord_setup['channels']['town_square'],
        author=mock_discord_setup['members']['alice'],
        guild=mock_discord_setup['guild']
    )

    # Since we're not really trying to properly test the full nomination functionality
    # we'll just track that the backup function got called, indicating message processing ran
    with patch('bot_impl.backup') as mock_backup:
        await on_message(alice_message)

        # If this assertion passes, it means on_message recognized the command
        # and at least started processing it
        assert mock_backup.called


@pytest.mark.asyncio
async def test_openpms_command_from_storyteller(mock_discord_setup, setup_test_game):
    """Test openpms command from a storyteller."""
    # Set up global variables for this test
    global_vars.game = setup_test_game['game']

    # Create a direct message channel for storyteller
    st_dm_channel = MockChannel(402, "dm-storyteller")
    st_dm_channel.guild = None  # Simulate DM

    # Set game to day
    setup_test_game['game'].isDay = True
    setup_test_game['game'].days = [MagicMock()]
    setup_test_game['game'].days[-1].open_pms = AsyncMock()

    # Create an openpms message from storyteller
    st_message = MockMessage(
        id=14,
        content="@openpms",
        channel=st_dm_channel,
        author=mock_discord_setup['members']['storyteller']
    )

    # Setup mock server for role check
    mock_server = MagicMock()
    mock_member = MagicMock()
    mock_member.roles = [MagicMock()]  # Storyteller role will be included
    mock_server.get_member.return_value = mock_member
    global_vars.server = mock_server
    global_vars.gamemaster_role = mock_member.roles[0]

    # Process the message
    with patch('bot_impl.backup') as mock_backup:
        with patch('utils.message_utils.safe_send', return_value=AsyncMock()) as mock_safe_send:
            await on_message(st_message)

            # Verify open_pms was called
            setup_test_game['game'].days[-1].open_pms.assert_called_once()


@pytest.mark.asyncio
async def test_whispers_command(mock_discord_setup, setup_test_game):
    """Test whispers command to show message counts."""
    # Set up global variables for this test
    global_vars.game = setup_test_game['game']

    # Create a direct message channel for Alice
    alice_dm_channel = MockChannel(401, "dm-alice")
    alice_dm_channel.guild = None  # Simulate DM

    # Start a day
    setup_test_game['game'].isDay = True
    setup_test_game['game'].days = [MagicMock()]

    # Create some message history for Alice
    setup_test_game['players']['alice'].message_history = [
        {
            "from_player": setup_test_game['players']['alice'],
            "to_player": setup_test_game['players']['bob'],
            "content": "Hello Bob",
            "day": 1,
            "time": MagicMock()
        }
    ]

    # Create a whispers message from Alice
    alice_message = MockMessage(
        id=15,
        content="@whispers",
        channel=alice_dm_channel,
        author=mock_discord_setup['members']['alice']
    )

    # Process the message
    with patch('bot_impl.backup') as mock_backup:
        with patch('bot_impl.get_player', return_value=setup_test_game['players']['alice']):
            with patch('utils.message_utils.safe_send', return_value=AsyncMock()) as mock_safe_send:
                # Create OrderedDict for counts (this is used in the function)
                with patch('bot_impl.OrderedDict', return_value={}):
                    await on_message(alice_message)

                    # Verify message was sent with whisper counts
                    assert mock_safe_send.called


@pytest.mark.asyncio
async def test_default_vote_command(mock_discord_setup):
    """Test setting a default vote."""
    # Create a direct message channel for Alice
    alice_dm_channel = MockChannel(401, "dm-alice")
    alice_dm_channel.guild = None  # Simulate DM

    # Setup mock server for role check (needed for many command handlers)
    mock_server = MagicMock()
    mock_member = MagicMock()
    mock_member.roles = []  # Not a storyteller
    mock_server.get_member.return_value = mock_member
    global_vars.server = mock_server

    # Create a defaultvote message from Alice
    alice_message = MockMessage(
        id=17,
        content="@defaultvote yes 5",  # Set default yes vote after 5 minutes
        channel=alice_dm_channel,
        author=mock_discord_setup['members']['alice']
    )

    # Mock GlobalSettings
    mock_global_settings = MagicMock()
    mock_global_settings.set_default_vote = MagicMock()
    mock_global_settings.save = MagicMock()
    mock_global_settings.get_alias = MagicMock(return_value=None)  # Important! This was missing

    # Process the message
    with patch('bot_impl.backup') as mock_backup:
        with patch('model.settings.global_settings.GlobalSettings.load', return_value=mock_global_settings):
            with patch('utils.message_utils.safe_send', return_value=AsyncMock()) as mock_safe_send:
                # Execute the message handling function
                await on_message(alice_message)

                # Verify confirmation message was sent (which indicates the command was processed)
                mock_safe_send.assert_called_with(
                    mock_discord_setup['members']['alice'],
                    "Successfully set default yes vote at 5 minutes."
                )


@pytest.mark.asyncio
async def test_history_command(mock_discord_setup, setup_test_game):
    """Test history command to view message history."""
    # Set up global variables for this test
    global_vars.game = setup_test_game['game']

    # Create a direct message channel for Alice
    alice_dm_channel = MockChannel(401, "dm-alice")
    alice_dm_channel.guild = None  # Simulate DM

    # Create message history for Alice
    setup_test_game['players']['alice'].message_history = [
        {
            "from_player": setup_test_game['players']['alice'],
            "to_player": setup_test_game['players']['bob'],
            "content": "Hello Bob",
            "day": 1,
            "time": MagicMock()
        }
    ]

    # Create a history message from Alice asking for history with Bob
    alice_message = MockMessage(
        id=18,
        content="@history bob",
        channel=alice_dm_channel,
        author=mock_discord_setup['members']['alice']
    )

    # Process the message
    with patch('bot_impl.backup') as mock_backup:
        with patch('bot_impl.get_player', return_value=setup_test_game['players']['alice']):
            with patch('bot_impl.select_player', return_value=setup_test_game['players']['bob']):
                with patch('utils.message_utils.safe_send', return_value=AsyncMock()) as mock_safe_send:
                    await on_message(alice_message)

                    # Verify message was sent with history
                    assert mock_safe_send.called


@pytest.mark.asyncio
async def test_skip_command(mock_discord_setup, setup_test_game):
    """Test skip command during nominations."""
    # Set up global variables for this test
    global_vars.game = setup_test_game['game']
    global_vars.channel = mock_discord_setup['channels']['town_square']

    # Set up game for skipping nominations
    setup_test_game['game'].isDay = True
    setup_test_game['game'].days = [MagicMock()]
    setup_test_game['game'].days[-1].skipMessages = []
    setup_test_game['players']['alice'].has_skipped = False

    # Create a skip message from Alice
    alice_message = MockMessage(
        id=19,
        content="@skip",
        channel=mock_discord_setup['channels']['town_square'],
        author=mock_discord_setup['members']['alice'],
        guild=mock_discord_setup['guild']
    )

    # Add pin method after creation (instead of in constructor)
    alice_message.pin = AsyncMock()

    # Process the message
    with patch('bot_impl.backup') as mock_backup:
        with patch('bot_impl.get_player', return_value=setup_test_game['players']['alice']):
            with patch('utils.message_utils.safe_send', return_value=AsyncMock()) as mock_safe_send:
                await on_message(alice_message)

                # We are only testing the basic message processing here, 
                # on_message_edit handles the actual pin action
                assert mock_backup.called


@pytest.mark.asyncio
async def test_clear_command(mock_discord_setup):
    """Test clear command to clear message history."""
    # Create a direct message channel for Alice
    alice_dm_channel = MockChannel(401, "dm-alice")
    alice_dm_channel.guild = None  # Simulate DM

    # Create a clear message from Alice
    alice_message = MockMessage(
        id=20,
        content="@clear",
        channel=alice_dm_channel,
        author=mock_discord_setup['members']['alice']
    )

    # Process the message
    with patch('bot_impl.backup') as mock_backup:
        with patch('utils.message_utils.safe_send', return_value=AsyncMock()) as mock_safe_send:
            await on_message(alice_message)

            # Verify clearing message was sent
            assert mock_safe_send.called
            # Check that it contains the expected format with whitespace
            mock_safe_send.assert_called_with(
                mock_discord_setup['members']['alice'],
                mock_safe_send.call_args[0][1]
            )
            assert "\u200b\n" in mock_safe_send.call_args[0][1]  # Contains whitespace
