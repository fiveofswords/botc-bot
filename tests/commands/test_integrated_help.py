"""Tests for the integrated help command system."""

from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

import global_vars
from commands.command_enums import HelpSection, UserType
from commands.help_commands import help_command, HelpGenerator
from commands.loader import load_all_commands
from commands.registry import registry

# Ensure commands are loaded for testing
load_all_commands()


class TestIntegratedHelp:
    """Test the integrated help command functionality."""

    @pytest.fixture
    def setup_mock_environment(self):
        """Set up mock Discord environment."""
        # Mock global_vars
        global_vars.gamemaster_role = MagicMock()
        global_vars.server = MagicMock()

        # Mock user and member
        mock_user = MagicMock(spec=discord.User)
        mock_user.send = AsyncMock()

        mock_member = MagicMock()
        mock_member.roles = []

        global_vars.server.get_member.return_value = mock_member

        # Mock message
        mock_message = MagicMock(spec=discord.Message)
        mock_message.author = mock_user
        mock_message.author.id = 12345

        return {
            'message': mock_message,
            'user': mock_user,
            'member': mock_member
        }

    @pytest.mark.asyncio
    async def test_help_command_registered(self):
        """Test that help command is registered in the registry."""
        assert "help" in registry.commands
        help_cmd = registry.commands["help"]
        assert help_cmd.name == "help"
        assert help_cmd.description == "Display help information for bot commands"
        assert HelpSection.MISC in help_cmd.help_sections
        assert UserType.PUBLIC in help_cmd.user_types

    @pytest.mark.asyncio
    async def test_help_command_player_basic(self, setup_mock_environment):
        """Test basic player help command."""
        mock_env = setup_mock_environment

        # Player (not storyteller)
        mock_env['member'].roles = []

        with patch('commands.help_commands.global_vars', global_vars):
            await help_command(mock_env['message'], "")

        # Verify help was sent
        mock_env['user'].send.assert_called_once()
        call_args = mock_env['user'].send.call_args[1]
        embed = call_args['embed']

        assert "Player Commands" in embed.title

    @pytest.mark.asyncio
    async def test_help_command_storyteller_basic(self, setup_mock_environment):
        """Test basic storyteller help command."""
        mock_env = setup_mock_environment
        
        # Storyteller
        mock_env['member'].roles = [global_vars.gamemaster_role]

        with patch('commands.help_commands.global_vars', global_vars):
            await help_command(mock_env['message'], "")

        # Verify help was sent
        mock_env['user'].send.assert_called_once()
        call_args = mock_env['user'].send.call_args[1]
        embed = call_args['embed']

        assert "Storyteller Help" in embed.title

    @pytest.mark.asyncio
    async def test_help_command_storyteller_sections(self, setup_mock_environment):
        """Test storyteller help command sections."""
        mock_env = setup_mock_environment
        mock_env['member'].roles = [global_vars.gamemaster_role]

        sections = ["common", "progression", "day", "gamestate", "configure", "info", "misc"]

        for section in sections:
            mock_env['user'].send.reset_mock()

            with patch('commands.help_commands.global_vars', global_vars):
                await help_command(mock_env['message'], section)

            # Verify help was sent
            assert mock_env['user'].send.called
            call_args = mock_env['user'].send.call_args[1]
            embed = call_args['embed']

            # Should have some commands
            assert len(embed.fields) > 0

    @pytest.mark.asyncio
    async def test_help_command_includes_registry_commands(self, setup_mock_environment):
        """Test that help command includes commands from the registry."""
        mock_env = setup_mock_environment
        mock_env['member'].roles = [global_vars.gamemaster_role]

        # Test misc section which should include our test commands
        with patch('commands.help_commands.global_vars', global_vars):
            await help_command(mock_env['message'], "misc")

        call_args = mock_env['user'].send.call_args[1]
        embed = call_args['embed']

        # Should include ping command from registry
        field_names = [field.name for field in embed.fields]
        assert "ping" in field_names

    @pytest.mark.asyncio
    async def test_help_command_player_section(self, setup_mock_environment):
        """Test player help section for storytellers."""
        mock_env = setup_mock_environment
        mock_env['member'].roles = [global_vars.gamemaster_role]

        with patch('commands.help_commands.global_vars', global_vars):
            await help_command(mock_env['message'], "player")

        call_args = mock_env['user'].send.call_args[1]
        embed = call_args['embed']

        assert "Player Commands" in embed.title

    @pytest.mark.asyncio
    async def test_help_command_unknown_section(self, setup_mock_environment):
        """Test help command with unknown section."""
        mock_env = setup_mock_environment
        mock_env['member'].roles = [global_vars.gamemaster_role]

        with patch('commands.help_commands.global_vars', global_vars):
            await help_command(mock_env['message'], "unknown")

        # Should send error message
        mock_env['user'].send.assert_called_once()
        call_args = mock_env['user'].send.call_args[0]
        assert "Unknown help topic" in call_args[0]

    def test_create_player_help_includes_registry_commands(self):
        """Test that player help includes registry commands."""
        embed = HelpGenerator.create_player_help_embed()

        assert "Player Commands" in embed.title

        # Should have some fields
        assert len(embed.fields) > 0

        # Should include tutorial and formatting info
        field_names = [field.name.lower() for field in embed.fields]
        assert any("playing online" in name for name in field_names)
        assert any("formatting" in name for name in field_names)

    def test_create_storyteller_main_help(self):
        """Test storyteller main help creation."""
        embed = HelpGenerator.create_storyteller_help_embed()

        assert "Storyteller Help" in embed.title

        # Should have help sections listed
        field_names = [field.name.lower() for field in embed.fields]
        assert any("help common" in name for name in field_names)
        assert any("help progression" in name for name in field_names)
        assert any("help day" in name for name in field_names)

    @pytest.mark.asyncio
    async def test_help_command_dm_failure_fallback(self, setup_mock_environment):
        """Test help command behavior when DM fails."""
        mock_env = setup_mock_environment
        mock_env['member'].roles = []

        # Make DM sending fail
        mock_env['user'].send.side_effect = discord.Forbidden(MagicMock(), "Can't send DM")

        # Should not raise an exception - just log a warning
        with patch('commands.help_commands.global_vars', global_vars):
            with patch('bot_client.logging') as mock_logging:
                await help_command(mock_env['message'], "")

                # Should log a warning about DM failure
                mock_logging.warning.assert_called_once()
                warning_call = mock_logging.warning.call_args[0][0]
                assert "Failed to send help DM" in warning_call

        # Should only call send once (the failed attempt)
        assert mock_env['user'].send.call_count == 1

    def test_registry_commands_integration(self):
        """Test that registry commands are properly integrated."""
        # We should have both info commands and help command registered
        command_names = list(registry.commands.keys())

        assert "ping" in command_names
        assert "test" in command_names
        assert "help" in command_names

        # Help command should have proper metadata
        help_cmd = registry.commands["help"]
        assert help_cmd.description == "Display help information for bot commands"
        assert HelpSection.MISC in help_cmd.help_sections
