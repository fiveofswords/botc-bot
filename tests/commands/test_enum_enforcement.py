"""Tests for command enum enforcement (user types and game phases)."""

from unittest.mock import AsyncMock

import pytest

import global_vars
from commands.command_enums import UserType, GamePhase
from commands.registry import registry, ValidationError, validate_game_phase
from model.game import NULL_GAME
from tests.fixtures.discord_mocks import mock_discord_setup
from tests.fixtures.game_fixtures import setup_test_game


class TestEnumEnforcement:
    """Test command enum enforcement for user types and game phases."""

    @pytest.fixture(autouse=True)
    def setup_test_command(self):
        """Set up test commands for validation testing."""
        # Save registry state
        self.original_state = registry.save_state()

        # Create test commands with different restrictions
        @registry.command(
            name="test_storyteller_only",
            description="Test storyteller-only command",
            user_types=[UserType.STORYTELLER],
            implemented=True
        )
        async def test_st_command(message, argument):
            await message.channel.send("ST command worked!")

        @registry.command(
            name="test_player_only",
            description="Test player-only command",
            user_types=[UserType.PLAYER],
            implemented=True
        )
        async def test_player_command(message, argument):
            await message.channel.send("Player command worked!")

        @registry.command(
            name="test_day_only",
            description="Test day-only command",
            user_types=[UserType.STORYTELLER],
            required_phases=[GamePhase.DAY],
            implemented=True
        )
        async def test_day_command(message, argument):
            await message.channel.send("Day command worked!")

        @registry.command(
            name="test_night_only",
            description="Test night-only command",
            user_types=[UserType.STORYTELLER],
            required_phases=[GamePhase.NIGHT],
            implemented=True
        )
        async def test_night_command(message, argument):
            await message.channel.send("Night command worked!")

        @registry.command(
            name="test_game_required",
            description="Test command requiring active game",
            user_types=[UserType.STORYTELLER],
            required_phases=[GamePhase.DAY, GamePhase.NIGHT],
            implemented=True
        )
        async def test_game_command(message, argument):
            await message.channel.send("Game command worked!")

        @registry.command(
            name="test_none_only",
            description="Test command for regular members only",
            user_types=[UserType.PUBLIC],
            implemented=True
        )
        async def test_none_command(message, argument):
            await message.channel.send("None command worked!")

        yield

        # Restore registry state
        registry.restore_state(self.original_state)

    @pytest.mark.asyncio
    async def test_storyteller_permission_validation(self, mock_discord_setup, setup_test_game):
        """Test that storyteller-only commands are properly restricted."""
        # Use alice (regular player) first - should be blocked
        alice = mock_discord_setup['members']['alice']
        mock_message = AsyncMock()
        mock_message.author = alice
        mock_message.channel.send = AsyncMock()

        # Should block non-storyteller
        result = await registry.handle_command("test_storyteller_only", mock_message, "")
        assert result is True  # Command was handled (with error)
        mock_message.channel.send.assert_called_once_with(
            "You do not have permission to use the test_storyteller_only command. Allowed role(s): Storyteller.")

        # Try with storyteller - should work
        storyteller = mock_discord_setup['members']['storyteller']
        mock_message.author = storyteller
        mock_message.channel.send.reset_mock()

        result = await registry.handle_command("test_storyteller_only", mock_message, "")
        assert result is True
        mock_message.channel.send.assert_called_once_with("ST command worked!")

    @pytest.mark.asyncio
    async def test_player_permission_validation(self, mock_discord_setup, setup_test_game):
        """Test that player-only commands are properly restricted."""
        # Set up game state so players are in seating order
        global_vars.game = setup_test_game['game']

        # Test with storyteller (not a player in game) - should be blocked
        storyteller = mock_discord_setup['members']['storyteller']
        mock_message = AsyncMock()
        mock_message.author = storyteller
        mock_message.channel.send = AsyncMock()

        # Should block non-player
        result = await registry.handle_command("test_player_only", mock_message, "")
        assert result is True  # Command was handled (with error)
        mock_message.channel.send.assert_called_once_with(
            "You do not have permission to use the test_player_only command. Allowed role(s): Player.")

        # Try with alice (a player in the game) - should work
        alice = mock_discord_setup['members']['alice']
        mock_message.author = alice
        mock_message.channel.send.reset_mock()

        result = await registry.handle_command("test_player_only", mock_message, "")
        assert result is True
        mock_message.channel.send.assert_called_once_with("Player command worked!")

    @pytest.mark.asyncio
    async def test_game_phase_validation(self, mock_discord_setup, setup_test_game):
        """Test that game phase restrictions work correctly."""
        # Use storyteller for these tests (has permission)
        storyteller = mock_discord_setup['members']['storyteller']
        mock_message = AsyncMock()
        mock_message.author = storyteller
        mock_message.channel.send = AsyncMock()

        # Test no active game
        global_vars.game = NULL_GAME

        result = await registry.handle_command("test_game_required", mock_message, "")
        assert result is True  # Command was handled (with error)
        mock_message.channel.send.assert_called_once_with("There's no game right now.")

        # Set up active game for phase testing
        game = setup_test_game['game']
        global_vars.game = game

        # Test day-only command during night
        game.isDay = False  # Night time
        mock_message.channel.send.reset_mock()

        result = await registry.handle_command("test_day_only", mock_message, "")
        assert result is True
        mock_message.channel.send.assert_called_once_with("It's not day right now.")

        # Test night-only command during day
        game.isDay = True  # Day time
        mock_message.channel.send.reset_mock()

        result = await registry.handle_command("test_night_only", mock_message, "")
        assert result is True
        mock_message.channel.send.assert_called_once_with("It's not night right now.")

        # Test day command during day (should work)
        mock_message.channel.send.reset_mock()

        result = await registry.handle_command("test_day_only", mock_message, "")
        assert result is True
        mock_message.channel.send.assert_called_once_with("Day command worked!")

    @pytest.mark.asyncio
    async def test_public_user_type_partition(self, mock_discord_setup, setup_test_game):
        """Test that UserType.PUBLIC truly partitions users correctly."""
        # Set up game state
        global_vars.game = setup_test_game['game']

        # Create a truly public user (no special roles, not in game)
        from tests.fixtures.discord_mocks import MockMember
        public_user = MockMember(999, "PublicUser", roles=[], guild=mock_discord_setup['guild'])
        mock_discord_setup['guild'].members.append(public_user)

        mock_message = AsyncMock()
        mock_message.author = public_user
        mock_message.channel.send = AsyncMock()

        # PUBLIC user should be able to use PUBLIC commands
        result = await registry.handle_command("test_none_only", mock_message, "")
        assert result is True
        mock_message.channel.send.assert_called_once_with("None command worked!")

        # Test that storyteller CANNOT use PUBLIC-only commands
        storyteller = mock_discord_setup['members']['storyteller']
        mock_message.author = storyteller
        mock_message.channel.send.reset_mock()

        result = await registry.handle_command("test_none_only", mock_message, "")
        assert result is True  # Command was handled (with error)
        mock_message.channel.send.assert_called_once_with(
            "You do not have permission to use the test_none_only command. Allowed role(s): Public.")

        # Test that player CANNOT use PUBLIC-only commands
        alice = mock_discord_setup['members']['alice']  # Alice is a player in the game
        mock_message.author = alice
        mock_message.channel.send.reset_mock()

        result = await registry.handle_command("test_none_only", mock_message, "")
        assert result is True  # Command was handled (with error)
        mock_message.channel.send.assert_called_once_with(
            "You do not have permission to use the test_none_only command. Allowed role(s): Public.")

    @pytest.mark.asyncio
    async def test_game_phase_validation_directly(self, mock_discord_setup, setup_test_game):
        """Test the game phase validation function directly."""
        # Test game phase validation
        global_vars.game = NULL_GAME

        # Should raise ValidationError for game requirement
        with pytest.raises(ValidationError, match="There's no game right now"):
            validate_game_phase((GamePhase.DAY,))

        # Should pass with no requirements
        validate_game_phase(())

        # Test phase-specific validation
        game = setup_test_game['game']
        game.isDay = False  # Night
        global_vars.game = game

        with pytest.raises(ValidationError, match="It's not day right now"):
            validate_game_phase((GamePhase.DAY,))

        # Should pass for night requirement
        validate_game_phase((GamePhase.NIGHT,))
