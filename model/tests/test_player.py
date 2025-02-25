"""
Unit tests for the Player class.
"""

import asyncio
from datetime import datetime
from unittest import IsolatedAsyncioTestCase, mock

import discord

from model.player import Player


class TestPlayer(IsolatedAsyncioTestCase):
    """Test the Player class."""

    async def asyncSetUp(self):
        """Set up test fixtures for each test."""
        # Create mock objects for testing
        self._setup_mocks()

        # Create test player
        self._create_test_player()

        # Patch global variables
        self._patch_global_vars()

        # Add cleanup
        self.addCleanup(self.global_vars_patcher.stop)

    def _setup_mocks(self):
        """Set up all mock objects needed for testing."""
        # Stub character
        self.mock_character_class = mock.MagicMock()
        self.mock_character = mock.MagicMock()
        self.mock_character_class.return_value = self.mock_character

        # Stub user
        self.mock_user = mock.MagicMock(spec=discord.Member)
        self.mock_user.name = "TestUser"
        self.mock_user.display_name = "TestDisplayName"
        self.mock_user.add_roles = mock.MagicMock(spec=discord.Member.add_roles)

        # Stub roles
        self.player_roles = []
        self.mock_inactive_role = mock.MagicMock(spec=discord.Role, id=12345)
        type(self.mock_user).roles = mock.PropertyMock(return_value=self.player_roles)

        # Mock channel
        self.mock_st_channel = mock.MagicMock(spec=discord.TextChannel)

    def _create_test_player(self):
        """Create test player instance."""
        self.player = Player(
            character_class=self.mock_character_class,
            alignment="good",
            user=self.mock_user,
            st_channel=self.mock_st_channel,
            position=1
        )

    def _patch_global_vars(self):
        """Patch global variables used by the Player class."""
        self.global_vars_patcher = mock.patch('model.player.global_vars')
        self.mock_global_vars = self.global_vars_patcher.start()
        self.mock_global_vars.inactive_role = self.mock_inactive_role
        self.mock_global_vars.game = mock.MagicMock()
        self.mock_global_vars.game.seatingOrder = [self.player]
        self.mock_global_vars.game.has_automated_life_and_death = False

    def test_init(self):
        """Test player initialization."""
        # Check player properties match expected values
        self.assertEqual(self.player.character, self.mock_character)
        self.assertEqual(self.player.alignment, "good")
        self.assertEqual(self.player.user, self.mock_user)
        self.assertEqual(self.player.st_channel, self.mock_st_channel)
        self.assertEqual(self.player.name, "TestUser")
        self.assertEqual(self.player.display_name, "TestDisplayName")
        self.assertEqual(self.player.position, 1)

        # Check default state flags
        self.assertFalse(self.player.is_ghost)
        self.assertEqual(self.player.dead_votes, 0)
        self.assertFalse(self.player.is_active)
        self.assertTrue(self.player.can_nominate)
        self.assertTrue(self.player.can_be_nominated)
        self.assertFalse(self.player.has_skipped)
        self.assertFalse(self.player.has_checked_in)
        self.assertEqual(len(self.player.message_history), 0)
        self.assertFalse(self.player.riot_nominee)
        self.assertIsInstance(self.player.last_active, float)
        self.assertFalse(self.player.is_inactive)

    def test_getstate(self):
        """Test serialization for pickling."""
        # Set IDs for mocks
        self.mock_user.id = 12345
        self.mock_st_channel.id = 67890

        # Get serialized state
        state = self.player.__getstate__()

        # Verify IDs are used for Discord objects
        self.assertEqual(state["user"], 12345)
        self.assertEqual(state["st_channel"], 67890)

    def test_setstate(self):
        """Test deserialization for unpickling."""
        # Create a state dictionary
        state = {
            "user": 12345,
            "st_channel": 67890,
            "alignment": "good",
            "name": "TestUser",
            "display_name": "TestDisplayName",
            "position": 1,
            "is_ghost": False,
            "dead_votes": 0,
            "is_active": False,
        }

        # Mock Discord objects that would be retrieved
        mock_member = mock.MagicMock(spec=discord.Member)
        mock_channel = mock.MagicMock(spec=discord.TextChannel)
        self.mock_global_vars.server.get_member.return_value = mock_member
        self.mock_global_vars.server.get_channel.return_value = mock_channel

        # Create and restore player
        player = Player(
            character_class=self.mock_character_class,
            alignment="good",
            user=self.mock_user,
            st_channel=self.mock_st_channel,
            position=1
        )
        player.__setstate__(state)

        # Verify Discord objects were retrieved by ID
        self.mock_global_vars.server.get_member.assert_called_once_with(12345)
        self.mock_global_vars.server.get_channel.assert_called_once_with(67890)
        self.assertEqual(player.user, mock_member)
        self.assertEqual(player.st_channel, mock_channel)

    async def test_morning(self):
        """Test morning state reset."""
        # Setup player state before morning
        self._set_player_state(
            is_ghost=True,
            can_nominate=False,
            can_be_nominated=False,
            is_active=True,
            has_skipped=True,
            has_checked_in=True,
            riot_nominee=True
        )

        # Call method under test
        await self.player.morning()

        # Verify state was reset correctly
        self.assertFalse(self.player.is_inactive)
        self.assertFalse(self.player.can_nominate)  # False because is_ghost is True
        self.assertTrue(self.player.can_be_nominated)
        self.assertFalse(self.player.is_active)
        self.assertFalse(self.player.has_skipped)
        self.assertFalse(self.player.has_checked_in)
        self.assertFalse(self.player.riot_nominee)

    async def test_morning_with_inactive_role(self):
        """Test morning state reset with inactive role."""
        # Add inactive role
        self.player_roles.append(self.mock_inactive_role)

        # Call method under test
        await self.player.morning()

        # Check state was reset with inactive flags
        self.assertTrue(self.player.is_inactive)
        self.assertTrue(self.player.is_active)
        self.assertTrue(self.player.has_skipped)
        self.assertTrue(self.player.has_checked_in)

    @mock.patch('model.player.ChannelManager')
    @mock.patch('utils.message_utils.safe_send')
    async def test_kill(self, mock_safe_send, mock_channel_manager):
        """Test player kill."""
        # Set up mocks
        self._setup_message_mocks(mock_safe_send, mock_channel_manager)

        # Call kill method
        result = await self.player.kill()

        # Verify player state changed
        self.assertTrue(self.player.is_ghost)
        self.assertEqual(self.player.dead_votes, 1)

        # Verify roles and permissions updated
        self._verify_kill_role_changes()

        # Verify messages sent
        mock_safe_send.assert_called_once()
        mock_safe_send.return_value.pin.assert_called_once()

        # Verify channel permissions updated
        mock_channel_manager.return_value.set_ghost.assert_called_once_with(self.mock_st_channel.id)

        # Verify game state updated
        self.mock_global_vars.game.reseat.assert_called_once()

        # Verify result
        self.assertTrue(result)

    @mock.patch('utils.message_utils.safe_send')
    async def test_kill_with_on_death_prevention(self, mock_safe_send):
        """Test player kill prevention via on_death handlers."""
        # Set up a player with on_death handler that prevents death
        self.mock_global_vars.game.has_automated_life_and_death = True

        # Create a fake character with on_death that prevents death
        fake_character = mock.MagicMock()
        fake_character.on_death.return_value = False
        fake_character.on_death_priority.return_value = 0

        # Create a fake player with that character
        fake_player = mock.MagicMock()
        fake_player.character = fake_character

        # Add that player to the game
        self.mock_global_vars.game.seatingOrder = [fake_player]

        # Call kill method
        result = await self.player.kill()

        # Verify character's on_death was called
        fake_character.on_death.assert_called_once_with(self.player, True)

        # Verify player did not die
        self.assertFalse(self.player.is_ghost)
        self.assertEqual(self.player.dead_votes, 0)

        # Verify no other methods were called
        mock_safe_send.assert_not_called()
        self.mock_user.add_roles.assert_not_called()

        # Verify result
        self.assertFalse(result)

    @mock.patch('model.player.client')
    @mock.patch('utils.message_utils.safe_send')
    async def test_execute_die_and_end(self, mock_safe_send, mock_client):
        """Test player execution with die and end day."""
        # Configure execute test
        self._setup_execute_test_environment(
            mock_safe_send, mock_client,
            die_choice="yes", end_choice="yes"
        )

        # Call execute method
        mock_user = mock.AsyncMock(spec=discord.Member)
        await self.player.execute(mock_user)

        # Verify kill was called
        # noinspection PyUnresolvedReferences
        self.player.kill.assert_called_once_with(suppress=True, force=False)

        # Verify day end was called
        self.mock_global_vars.game.days[0].end.assert_called_once()

        # Verify execution flag was set
        self.assertTrue(self.mock_global_vars.game.days[0].isExecutionToday)

    @mock.patch('model.player.client')
    @mock.patch('utils.message_utils.safe_send')
    async def test_execute_no_die(self, mock_safe_send, mock_client):
        """Test player execution with no die."""
        # Configure execute test
        self._setup_execute_test_environment(
            mock_safe_send, mock_client,
            die_choice="no", end_choice="no"
        )

        # Call execute method
        mock_user = mock.AsyncMock(spec=discord.Member)
        await self.player.execute(mock_user)

        # Verify execution flag was set but no other actions
        self.assertTrue(self.mock_global_vars.game.days[0].isExecutionToday)
        self.assertEqual(mock_safe_send.call_count, 3)

    @mock.patch('model.player.client')
    @mock.patch('utils.message_utils.safe_send')
    async def test_execute_timeout(self, mock_safe_send, mock_client):
        """Test player execution with timeout."""
        # Configure safe_send
        mock_message = mock.AsyncMock(spec=discord.Message)
        mock_safe_send.side_effect = [mock_message, mock.AsyncMock()]

        # Configure wait_for to time out
        mock_client.wait_for = mock.AsyncMock()
        mock_client.wait_for.side_effect = asyncio.TimeoutError()

        # Call execute method
        mock_user = mock.AsyncMock(spec=discord.Member)
        await self.player.execute(mock_user)

        # Verify timeout message sent
        mock_safe_send.assert_has_calls([
            mock.call(mock_user, "Do they die? yes or no"),
            mock.call(mock_user, "Message timed out!")
        ])

    @mock.patch('model.player.client')
    @mock.patch('utils.message_utils.safe_send')
    async def test_execute_cancel(self, mock_safe_send, mock_client):
        """Test player execution with cancel."""
        # Configure safe_send
        mock_message = mock.AsyncMock(spec=discord.Message)
        mock_safe_send.side_effect = [mock_message, mock.AsyncMock()]

        # Configure wait_for to return cancel
        mock_response = mock.AsyncMock(spec=discord.Message)
        mock_response.content = "cancel"
        mock_client.wait_for = mock.AsyncMock()
        mock_client.wait_for.return_value = mock_response

        # Call execute method
        mock_user = mock.AsyncMock(spec=discord.Member)
        await self.player.execute(mock_user)

        # Verify cancel message sent
        mock_safe_send.assert_has_calls([
            mock.call(mock_user, "Do they die? yes or no"),
            mock.call(mock_user, "Action cancelled!")
        ])

    @mock.patch('model.player.ChannelManager')
    @mock.patch('utils.message_utils.safe_send')
    async def test_revive(self, mock_safe_send, mock_channel_manager):
        """Test player revive."""
        # Set up player as dead
        self._set_player_state(is_ghost=True, dead_votes=2)

        # Set up mocks
        self._setup_message_mocks(mock_safe_send, mock_channel_manager)

        # Call revive method
        await self.player.revive()

        # Verify player state changed
        self.assertFalse(self.player.is_ghost)
        self.assertEqual(self.player.dead_votes, 0)

        # Verify character was refreshed
        self.mock_character.refresh.assert_called_once()

        # Verify roles were removed
        self.mock_user.remove_roles.assert_called_once_with(
            self.mock_global_vars.ghost_role,
            self.mock_global_vars.dead_vote_role
        )

        # Verify channel permissions updated
        mock_channel_manager.return_value.remove_ghost.assert_called_once_with(self.mock_st_channel.id)

        # Verify announcement sent
        mock_safe_send.assert_called_once()
        mock_safe_send.return_value.pin.assert_called_once()

        # Verify game state updated
        self.mock_global_vars.game.reseat.assert_called_once()

    @mock.patch('model.player.global_vars')
    async def test_change_character(self, mock_global_vars):
        """Test character change."""
        # Set up mocks
        mock_global_vars.game.reseat = mock.AsyncMock()

        # Create new character
        new_character_class = mock.MagicMock()
        new_character = mock.MagicMock()
        new_character_class.return_value = new_character

        # Call change_character method
        await self.player.change_character(new_character_class)

        # Verify character was changed
        self.assertEqual(self.player.character, new_character)
        new_character_class.assert_called_once_with(self.player)

        # Verify seating was updated
        mock_global_vars.game.reseat.assert_called_once()

    async def test_change_alignment(self):
        """Test alignment change."""
        # Call change_alignment method
        await self.player.change_alignment("evil")

        # Verify alignment was changed
        self.assertEqual(self.player.alignment, "evil")

    @mock.patch('utils.message_utils.safe_send')
    async def test_message(self, mock_safe_send):
        """Test sending a message to a player."""
        # Set up common message test environment
        mock_sender, mock_message = self._setup_message_test(mock_safe_send)

        # Call message method
        await self.player.message(
            from_player=mock_sender,
            content="Test message content",
            jump="https://discord.com/original_url"
        )

        # Verify messages were sent
        self._verify_message_sent(mock_safe_send, mock_sender)

        # Verify message history was updated
        self._verify_message_history(mock_sender)

    @mock.patch('utils.message_utils.safe_send')
    async def test_message_whisper_channel(self, mock_safe_send):
        """Test sending a message with whisper channel."""
        # Set up whisper channel
        mock_whisper_channel = mock.AsyncMock(spec=discord.TextChannel)
        self.mock_global_vars.whisper_channel = mock_whisper_channel

        # Set up common message test environment
        mock_sender, _ = self._setup_message_test(mock_safe_send)

        # Call message method
        await self.player.message(
            from_player=mock_sender,
            content="Test message content",
            jump="https://discord.com/original_url"
        )

        # Verify message was sent to whisper channel
        mock_safe_send.assert_any_call(
            mock_whisper_channel,
            "Message from SenderName to TestDisplayName: **Test message content**"
        )

    @mock.patch('utils.message_utils.safe_send')
    async def test_message_http_exception(self, mock_safe_send):
        """Test sending a message with HTTP exception."""
        # Set up mocks
        mock_sender = mock.MagicMock()
        mock_sender.display_name = "SenderName"
        mock_sender.message_history = []

        # Configure safe_send to raise exception
        mock_safe_send.side_effect = [
            discord.errors.HTTPException(mock.MagicMock(), "Error"),
            mock.AsyncMock()  # For the error message to sender
        ]

        # Set up logger
        mock_logger = mock.MagicMock()
        mock_player = mock.patch('model.player.logger', mock_logger)
        mock_player.start()
        self.addCleanup(mock_player.stop)

        # Call message method
        await self.player.message(
            from_player=mock_sender,
            content="Test message content",
            jump="https://discord.com/original_url"
        )

        # Verify error message sent to sender
        mock_safe_send.assert_called_with(
            mock_sender.user,
            f"Something went wrong with your message to {self.player.display_name}! Please try again"
        )

        # Verify logger was called
        mock_logger.info.assert_called_once()

        # Verify message history was not updated
        self.assertEqual(len(self.player.message_history), 0)
        self.assertEqual(len(mock_sender.message_history), 0)

    @mock.patch('utils.message_utils.safe_send')
    async def test_make_inactive(self, mock_safe_send):
        """Test making a player inactive."""
        # Set up game in day phase
        self.mock_global_vars.game.isDay = True

        # Set up test players
        self._setup_inactive_test_players()

        # Call make_inactive method
        await self.player.make_inactive()

        # Verify player state changed
        self._verify_inactive_state()

        # Verify notification messages sent
        self._verify_inactive_notifications(mock_safe_send)

    @mock.patch('utils.player_utils.check_and_print_if_one_or_zero_to_check_in')
    async def test_make_inactive_night(self, mock_check_checkin):
        """Test making a player inactive during night phase."""
        # Set up game in night phase
        self.mock_global_vars.game.isDay = False

        # Call make_inactive method
        await self.player.make_inactive()

        # Verify check_and_print_if_one_or_zero_to_check_in was called
        mock_check_checkin.assert_called_once()

    async def test_undo_inactive(self):
        """Test making a player no longer inactive."""
        # Set up player as inactive
        self._set_player_state(
            is_inactive=True,
            has_skipped=True,
            has_checked_in=True
        )

        # Call undo_inactive method
        await self.player.undo_inactive()

        # Verify player state changed
        self.assertFalse(self.player.is_inactive)
        self.assertFalse(self.player.has_skipped)
        self.assertFalse(self.player.has_checked_in)

        # Verify roles were removed
        self.mock_user.remove_roles.assert_called_once_with(self.mock_global_vars.inactive_role)

    def test_update_last_active(self):
        """Test updating last active timestamp."""
        old_timestamp = self.player.last_active

        # Wait a small amount of time
        import time
        time.sleep(0.01)

        # Call update_last_active method
        self.player.update_last_active()

        # Verify timestamp was updated
        self.assertGreater(self.player.last_active, old_timestamp)

    async def test_add_dead_vote(self):
        """Test adding a dead vote."""
        # Configure mock game.reseat to be an AsyncMock
        self.mock_global_vars.game.reseat = mock.AsyncMock()

        # Call add_dead_vote method
        await self.player.add_dead_vote()

        # Verify dead_votes was incremented
        self.assertEqual(self.player.dead_votes, 1)

        # Verify roles were added
        self.mock_user.add_roles.assert_called_once_with(self.mock_global_vars.dead_vote_role)

        # Verify reseat was called
        self.mock_global_vars.game.reseat.assert_called_once()

    async def test_add_dead_vote_already_has_vote(self):
        """Test adding a dead vote when player already has one."""
        # Set up player with existing dead vote
        self._set_player_state(dead_votes=1)

        # Configure mock game.reseat to be an AsyncMock
        self.mock_global_vars.game.reseat = mock.AsyncMock()

        # Call add_dead_vote method
        await self.player.add_dead_vote()

        # Verify dead_votes was incremented
        self.assertEqual(self.player.dead_votes, 2)

        # Verify roles were not added again
        self.mock_user.add_roles.assert_not_called()

    async def test_remove_dead_vote(self):
        """Test removing a dead vote."""
        # Set up player with dead votes
        self._set_player_state(dead_votes=2)

        # Configure mock game.reseat to be an AsyncMock
        self.mock_global_vars.game.reseat = mock.AsyncMock()

        # Call remove_dead_vote method
        await self.player.remove_dead_vote()

        # Verify dead_votes was decremented
        self.assertEqual(self.player.dead_votes, 1)

        # Verify roles were not removed
        self.mock_user.remove_roles.assert_not_called()

        # Verify reseat was called
        self.mock_global_vars.game.reseat.assert_called_once()

    async def test_remove_last_dead_vote(self):
        """Test removing the last dead vote."""
        # Set up player with one dead vote
        self._set_player_state(dead_votes=1)

        # Configure mock game.reseat to be an AsyncMock
        self.mock_global_vars.game.reseat = mock.AsyncMock()

        # Call remove_dead_vote method
        await self.player.remove_dead_vote()

        # Verify dead_votes was decremented
        self.assertEqual(self.player.dead_votes, 0)

        # Verify roles were removed
        self.mock_user.remove_roles.assert_called_once_with(self.mock_global_vars.dead_vote_role)

    @mock.patch('model.player.global_vars')
    async def test_wipe_roles(self, mock_global_vars):
        """Test wiping all roles from a player."""
        # Call wipe_roles method
        await self.player.wipe_roles()

        # Verify roles were removed
        self.mock_user.remove_roles.assert_called_once_with(
            mock_global_vars.traveler_role,
            mock_global_vars.ghost_role,
            mock_global_vars.dead_vote_role
        )

    @mock.patch('model.player.logger')
    async def test_wipe_roles_http_exception(self, mock_logger):
        """Test wiping roles with HTTP exception."""
        # Configure remove_roles to raise exception
        self.player.user.remove_roles.side_effect = discord.HTTPException(mock.MagicMock(), "Error")

        # Call wipe_roles method
        await self.player.wipe_roles()

        # Verify logger was called
        mock_logger.info.assert_called_once()

    # Helper methods for tests
    def _set_player_state(self, **kwargs):
        """Helper to set player state."""
        for attr, value in kwargs.items():
            setattr(self.player, attr, value)

    def _setup_message_mocks(self, mock_safe_send, mock_channel_manager):
        """Set up mocks for messaging tests."""
        # Configure global vars
        self.mock_global_vars.channel = mock.AsyncMock(spec=discord.TextChannel)
        self.mock_global_vars.ghost_role = mock.MagicMock(spec=discord.Role)
        self.mock_global_vars.dead_vote_role = mock.MagicMock(spec=discord.Role)
        self.mock_global_vars.game.reseat = mock.AsyncMock()

        # Configure message
        mock_message = mock.AsyncMock(spec=discord.Message)
        mock_safe_send.return_value = mock_message

        # Configure channel manager
        mock_channel_manager_instance = mock.AsyncMock()
        mock_channel_manager.return_value = mock_channel_manager_instance

    def _verify_kill_role_changes(self):
        """Verify role changes after kill."""
        self.mock_user.add_roles.assert_called_once_with(
            self.mock_global_vars.ghost_role,
            self.mock_global_vars.dead_vote_role
        )

    def _setup_execute_test_environment(self, mock_safe_send, mock_client, die_choice, end_choice):
        """Configure test environment for execute method tests."""
        # Set up player
        self.player.kill = mock.AsyncMock(return_value=True)

        # Set up game
        mock_day = mock.AsyncMock()
        mock_game = mock.MagicMock()
        mock_game.days = [mock_day]
        mock_game.isDay = True
        self.mock_global_vars.game = mock_game
        self.mock_global_vars.channel = mock.AsyncMock(spec=discord.TextChannel)

        # Set up messages
        mock_message1 = mock.AsyncMock(spec=discord.Message)
        mock_message2 = mock.AsyncMock(spec=discord.Message)

        # Set up user responses
        mock_response1 = mock.AsyncMock(spec=discord.Message)
        mock_response1.content = die_choice
        mock_response2 = mock.AsyncMock(spec=discord.Message)
        mock_response2.content = end_choice

        # Configure wait_for
        mock_client.wait_for = mock.AsyncMock()
        mock_client.wait_for.side_effect = [mock_response1, mock_response2]

        # Configure safe_send
        mock_safe_send.side_effect = [mock_message1, mock_message2, mock.AsyncMock()]

    @staticmethod
    def _setup_message_test(mock_safe_send):
        """Set up common environment for message tests."""
        # Create sender
        mock_sender = mock.MagicMock()
        mock_sender.display_name = "SenderName"
        mock_sender.message_history = []

        # Create message response
        mock_message = mock.AsyncMock(spec=discord.Message)
        mock_message.created_at = datetime.now()
        mock_message.jump_url = "https://discord.com/message_url"
        mock_safe_send.return_value = mock_message

        return mock_sender, mock_message

    def _verify_message_sent(self, mock_safe_send, mock_sender):
        """Verify messages sent during message method."""
        # Verify message to player
        mock_safe_send.assert_any_call(
            self.player.user,
            "Message from SenderName: **Test message content**"
        )

        # Verify confirmation to sender
        mock_safe_send.assert_any_call(mock_sender.user, "Message sent!")

    def _verify_message_history(self, mock_sender):
        """Verify message history updated correctly."""
        # Check lengths
        self.assertEqual(len(self.player.message_history), 1)
        self.assertEqual(len(mock_sender.message_history), 1)

        # Check content in player's history
        self.assertEqual(self.player.message_history[0]["content"], "Test message content")
        self.assertEqual(self.player.message_history[0]["from_player"], mock_sender)
        self.assertEqual(self.player.message_history[0]["to_player"], self.player)

        # Check content in sender's history
        self.assertEqual(mock_sender.message_history[0]["content"], "Test message content")
        self.assertEqual(mock_sender.message_history[0]["from_player"], mock_sender)
        self.assertEqual(mock_sender.message_history[0]["to_player"], self.player)
        self.assertEqual(mock_sender.message_history[0]["jump"], "https://discord.com/original_url")

    def _setup_inactive_test_players(self):
        """Configure test players for inactive tests."""
        # Create an inactive player
        other_player = mock.MagicMock()
        other_player.is_active = False
        other_player.alignment = "good"
        other_player.display_name = "OtherPlayer"

        # Create a player that can nominate but has skipped
        can_nominate_player = mock.MagicMock()
        can_nominate_player.can_nominate = True
        can_nominate_player.has_skipped = True
        can_nominate_player.alignment = "good"
        can_nominate_player.is_ghost = False

        # Add players to seating order
        self.mock_global_vars.game.seatingOrder = [self.player, other_player, can_nominate_player]

        # Set up GM role members
        gm_member = mock.MagicMock(spec=discord.Member)
        self.mock_global_vars.gamemaster_role.members = [gm_member]

    def _verify_inactive_state(self):
        """Verify player state after becoming inactive."""
        self.assertTrue(self.player.is_inactive)
        self.assertTrue(self.player.has_skipped)
        self.assertTrue(self.player.is_active)
        self.assertTrue(self.player.has_checked_in)
        self.mock_user.add_roles.assert_called_once_with(self.mock_global_vars.inactive_role)

    def _verify_inactive_notifications(self, mock_safe_send):
        """Verify notifications sent when a player becomes inactive."""
        # Get GM member
        gm_member = self.mock_global_vars.gamemaster_role.members[0]

        # Verify notification about active players
        mock_safe_send.assert_any_call(
            gm_member,
            "Just waiting on OtherPlayer to speak."
        )

        # Verify notification about nominations
        mock_safe_send.assert_any_call(
            gm_member,
            "Everyone has nominated or skipped!"
        )


if __name__ == '__main__':
    import unittest

    unittest.main()
