"""Tests for the enhanced help system."""

import discord

from commands.command_enums import HelpSection, UserType
from commands.help_commands import HelpGenerator
from commands.loader import load_all_commands
from commands.registry import registry

# Ensure commands are loaded for testing
load_all_commands()


class TestHelpSystem:
    """Test the enhanced help system functionality."""

    def test_help_types_enum_values(self):
        """Test that help enums have expected values."""
        assert HelpSection.COMMON.value == "common"
        assert HelpSection.PLAYER.value == "player"
        assert UserType.STORYTELLER.value == "storyteller"
        assert UserType.PLAYER.value == "player"
        assert UserType.NONE.value == "none"

    def test_registry_get_commands_by_section(self):
        """Test getting commands by help section."""
        # Test commands should be registered from debug_commands.py
        misc_commands = registry.get_commands_by_section(HelpSection.MISC)

        # Should find ping command which is in MISC section
        command_names = [cmd.name for cmd in misc_commands]
        assert "ping" in command_names

    def test_registry_get_commands_by_user_type(self):
        """Test getting commands by user type."""
        all_commands = registry.get_commands_by_user_type(UserType.NONE)
        storyteller_commands = registry.get_commands_by_user_type(UserType.STORYTELLER)

        # Should have some commands for each type
        assert len(all_commands) > 0
        assert len(storyteller_commands) > 0

        # ping command should be available to ALL users
        all_command_names = [cmd.name for cmd in all_commands]
        assert "ping" in all_command_names

    def test_help_generator_creates_embeds(self):
        """Test that help generator creates proper embeds."""
        # Test storyteller help embed
        st_embed = HelpGenerator.create_storyteller_help_embed()
        assert isinstance(st_embed, discord.Embed)
        assert "Storyteller Help" in st_embed.title

        # Test player help embed
        player_embed = HelpGenerator.create_player_help_embed()
        assert isinstance(player_embed, discord.Embed)
        assert "Player Commands" in player_embed.title

    def test_help_generator_section_embed(self):
        """Test section-specific help embeds."""
        misc_embed = HelpGenerator.create_section_help_embed(HelpSection.MISC, UserType.NONE)
        assert isinstance(misc_embed, discord.Embed)
        assert "Miscellaneous Commands" in misc_embed.title

        # Should have some fields for commands
        assert len(misc_embed.fields) > 0

    def test_help_generator_player_embed(self):
        """Test player help embed."""
        player_embed = HelpGenerator.create_player_help_embed()
        assert isinstance(player_embed, discord.Embed)
        assert "Player Commands" in player_embed.title

        # Should have tutorial and formatting fields
        field_names = [field.name for field in player_embed.fields]
        assert any("playing online" in name.lower() for name in field_names)
        assert any("formatting" in name.lower() for name in field_names)

    def test_registry_enhanced_command_decorator(self):
        """Test that the enhanced command decorator works."""

        # This test verifies that we can register a command with help info

        @registry.command(
            name="test_help_cmd",
            description="Test command for help system",
            help_sections=[HelpSection.MISC],
            user_types=[UserType.NONE],
            aliases=["thc"]
        )
        async def test_help_command(message, argument):
            pass

        # Verify command was registered
        assert "test_help_cmd" in registry.commands
        cmd_info = registry.commands["test_help_cmd"]
        assert cmd_info.description == "Test command for help system"
        assert HelpSection.MISC in cmd_info.help_sections
        assert UserType.NONE in cmd_info.user_types
        assert "thc" in cmd_info.aliases

        # Verify alias was registered
        assert registry.aliases["thc"] == "test_help_cmd"

    def test_enhanced_command_decorator_defaults(self):
        """Test command decorator with default values."""

        @registry.command(name="test_defaults")
        async def test_defaults_command(message, argument):
            pass

        cmd_info = registry.commands["test_defaults"]
        assert cmd_info.description == ""
        assert cmd_info.help_sections == ()
        assert cmd_info.user_types == ()
        assert cmd_info.aliases == ()
