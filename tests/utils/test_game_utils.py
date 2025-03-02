"""Tests for the game_utils module which provides utility functions for game management."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from utils.game_utils import update_presence, remove_backup


class TestUpdatePresence:
    """Tests for the update_presence function which updates Discord bot status based on game state."""

    @pytest.mark.asyncio
    async def test_no_game(self):
        """Test that update_presence sets appropriate status when no game is running."""
        # Set up mock Discord client
        mock_client = AsyncMock()
        mock_client.change_presence = AsyncMock()

        # Set up mock Discord status types
        mock_discord_game = MagicMock()
        mock_discord_status = MagicMock()
        mock_discord_status.dnd = "dnd_status"  # Do Not Disturb status

        # When no game is active
        with patch('utils.game_utils.global_vars') as mock_global_vars, \
                patch('utils.game_utils.discord') as mock_discord:
            mock_discord.Status = mock_discord_status
            mock_discord.Game = mock_discord_game
            mock_global_vars.game = None

            # When updating presence
            await update_presence(mock_client)

            # Then the bot should show "No ongoing game!" status
            mock_client.change_presence.assert_called_once()
            mock_discord.Game.assert_called_once_with(name="No ongoing game!")

    @pytest.mark.asyncio
    async def test_night_phase(self):
        """Test that update_presence shows nighttime status during night phase."""
        # Set up mock Discord client
        mock_client = AsyncMock()
        mock_client.change_presence = AsyncMock()

        # Set up mock Discord status types
        mock_discord_game = MagicMock()
        mock_discord_status = MagicMock()
        mock_discord_status.idle = "idle_status"  # Idle status for night

        # When a game is in night phase
        with patch('utils.game_utils.global_vars') as mock_global_vars, \
                patch('utils.game_utils.discord') as mock_discord:
            mock_discord.Status = mock_discord_status
            mock_discord.Game = mock_discord_game

            mock_game = MagicMock()
            mock_game.seatingOrder = [MagicMock()]  # Has at least one player
            mock_game.isDay = False  # Night phase
            mock_global_vars.game = mock_game

            # When updating presence
            await update_presence(mock_client)

            # Then the bot should show nighttime status
            mock_client.change_presence.assert_called_once()
            mock_discord.Game.assert_called_once_with(name="It's nighttime!")

    @pytest.mark.asyncio
    async def test_day_phase_pms_closed_noms_closed(self):
        """Test that update_presence shows the correct status when PMs and nominations are closed."""
        # Set up mock Discord client
        mock_client = AsyncMock()
        mock_client.change_presence = AsyncMock()

        # Set up mock Discord status types
        mock_discord_game = MagicMock()
        mock_discord_status = MagicMock()
        mock_discord_status.online = "online_status"  # Online status for day

        # Mock WhisperMode enumeration
        mock_whisper_mode = MagicMock()
        mock_whisper_mode.ALL = "all"

        # When game is in day phase with closed PMs and nominations
        with patch('utils.game_utils.global_vars') as mock_global_vars, \
                patch('utils.game_utils.discord') as mock_discord, \
                patch('model.game.whisper_mode.WhisperMode', mock_whisper_mode):
            mock_discord.Status = mock_discord_status
            mock_discord.Game = mock_discord_game

            # Create a day with closed PMs and nominations
            mock_day = MagicMock()
            mock_day.isPms = False  # PMs are closed
            mock_day.isNoms = False  # Nominations are closed

            # Create a game in day phase
            mock_game = MagicMock()
            mock_game.seatingOrder = [MagicMock()]
            mock_game.isDay = True
            mock_game.days = [mock_day]
            mock_game.whisper_mode = "neighbors"  # Custom whisper mode

            mock_global_vars.game = mock_game

            # When updating presence
            await update_presence(mock_client)

            # Then the bot should show status with closed PMs and nominations
            mock_client.change_presence.assert_called_once()
            mock_discord.Game.assert_called_once_with(name="PMs Closed, Nominations Closed!")

    @pytest.mark.asyncio
    async def test_day_phase_pms_open_whisper_mode(self):
        """Test that update_presence shows whisper mode information when PMs are open."""
        # Set up mock Discord client
        mock_client = AsyncMock()
        mock_client.change_presence = AsyncMock()

        # Set up mock Discord status types
        mock_discord_game = MagicMock()
        mock_discord_status = MagicMock()
        mock_discord_status.online = "online_status"  # Online status for day

        # Mock WhisperMode enumeration
        mock_whisper_mode = MagicMock()
        mock_whisper_mode.ALL = "all"

        # When game is in day phase with open PMs and nominations
        with patch('utils.game_utils.global_vars') as mock_global_vars, \
                patch('utils.game_utils.discord') as mock_discord, \
                patch('model.game.whisper_mode.WhisperMode', mock_whisper_mode):
            mock_discord.Status = mock_discord_status
            mock_discord.Game = mock_discord_game

            # Create a day with open PMs and nominations
            mock_day = MagicMock()
            mock_day.isPms = True  # PMs are open
            mock_day.isNoms = True  # Nominations are open

            # Create a game in day phase with neighbors whisper mode
            mock_game = MagicMock()
            mock_game.seatingOrder = [MagicMock()]
            mock_game.isDay = True
            mock_game.days = [mock_day]
            mock_game.whisper_mode = "neighbors"  # Custom whisper mode

            mock_global_vars.game = mock_game

            # When updating presence
            await update_presence(mock_client)

            # Then the bot should show status with whisper mode and open nominations
            mock_client.change_presence.assert_called_once()
            mock_discord.Game.assert_called_once_with(name="PMs to neighbors, Nominations Open!")


class TestRemoveBackup:
    """Tests for the remove_backup function which cleans up game backup files."""

    @patch('os.path.exists')
    @patch('os.remove')
    @patch('utils.game_utils.global_vars')
    def test_backup_exists(self, mock_global_vars, mock_remove, mock_exists):
        """Test that remove_backup deletes both main and attribute backup files when they exist."""
        # Given backup files exist
        mock_exists.return_value = True

        # And the game has various attributes
        mock_game = MagicMock()
        mock_game.days = []
        mock_game.isDay = False
        mock_game.script = []
        mock_global_vars.game = mock_game

        # When removing backups
        with patch('utils.game_utils.dir') as mock_dir:
            # Return game attributes that should be backed up
            mock_dir.return_value = ['days', 'isDay', 'script', '__class__', '__call__']
            remove_backup("test.pckl")

            # Then all backup files (main + attributes) should be removed
            assert mock_remove.call_count == 4  # Main file + 3 attribute files
            mock_remove.assert_any_call("test.pckl")
            mock_remove.assert_any_call("days_test.pckl")
            mock_remove.assert_any_call("isDay_test.pckl")
            mock_remove.assert_any_call("script_test.pckl")

    @patch('os.path.exists')
    @patch('os.remove')
    @patch('utils.game_utils.global_vars')
    def test_backup_doesnt_exist(self, mock_global_vars, mock_remove, mock_exists):
        """Test that remove_backup does nothing when backup files don't exist."""
        # Given no backup files exist
        mock_exists.return_value = False

        # And there is a game
        mock_game = MagicMock()
        mock_global_vars.game = mock_game

        # When removing backups
        remove_backup("test.pckl")

        # Then no files should be removed
        mock_remove.assert_not_called()

    @patch('os.path.exists')
    @patch('os.remove')
    @patch('utils.game_utils.global_vars')
    def test_some_obj_files_exist(self, mock_global_vars, mock_remove, mock_exists):
        """Test that remove_backup only removes files that actually exist."""

        # Given only some backup files exist
        def exists_side_effect(path):
            if path == "test.pckl" or path == "days_test.pckl":
                return True
            return False

        mock_exists.side_effect = exists_side_effect

        # And the game has various attributes
        mock_game = MagicMock()
        mock_game.days = []
        mock_game.isDay = False
        mock_global_vars.game = mock_game

        # When removing backups
        with patch('utils.game_utils.dir') as mock_dir:
            # Return game attributes that should be backed up
            mock_dir.return_value = ['days', 'isDay', '__class__']
            remove_backup("test.pckl")

            # Then only existing files should be removed
            assert mock_remove.call_count == 2  # Main file + days obj file
            mock_remove.assert_any_call("test.pckl")
            mock_remove.assert_any_call("days_test.pckl")
