"""Tests for the enhanced help system."""

from types import MappingProxyType

import discord

from commands.command_enums import HelpSection, UserType
from commands.help_commands import HelpGenerator
from commands.loader import load_all_commands
from commands.registry import registry, CommandArgument, CommandInfo

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
        assert UserType.PUBLIC.value == "public"

    def test_registry_get_commands_by_section(self):
        """Test getting commands by help section."""
        # Test commands should be registered from debug_commands.py
        misc_commands = registry.get_commands_by_section(HelpSection.MISC)

        # Should find ping command which is in MISC section
        command_names = [cmd.name for cmd in misc_commands]
        assert "ping" in command_names

    def test_registry_get_commands_by_user_type(self):
        """Test getting commands by user type."""
        all_commands = registry.get_commands_by_user_type(UserType.PUBLIC)
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
        misc_embed = HelpGenerator.create_section_help_embed(HelpSection.MISC, UserType.PUBLIC)
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
            user_types=[UserType.PUBLIC],
            aliases=["thc"]
        )
        async def test_help_command(message, argument):
            pass

        # Verify command was registered
        assert "test_help_cmd" in registry.commands
        cmd_info = registry.commands["test_help_cmd"]
        assert cmd_info.description == "Test command for help system"
        assert HelpSection.MISC in cmd_info.help_sections
        assert UserType.PUBLIC in cmd_info.user_types
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

    def test_command_argument_formatting_logic(self):
        """Test the argument formatting logic produces correct help display formats."""

        @registry.command(
            name="format_test_cmd",
            description="Test argument formatting",
            help_sections=[HelpSection.MISC],
            user_types=[UserType.STORYTELLER],
            arguments=[
                CommandArgument("player"),  # Required name
                CommandArgument(("yes", "no")),  # Required choices
                CommandArgument("reason", optional=True),  # Optional name
                CommandArgument(("high", "medium", "low"), optional=True)  # Optional choices
            ]
        )
        async def format_test_command(message, argument):
            pass

        cmd = registry.commands["format_test_cmd"]
        formatted = cmd.get_formatted_name_for_user(UserType.STORYTELLER)

        # Test the actual formatting logic produces consistent format with hardcoded commands
        expected = "format_test_cmd <player> <yes|no> [reason] [high|medium|low]"
        assert formatted == expected

        # Test that the formatting logic correctly distinguishes required vs optional
        assert "<player>" in formatted  # Required argument
        assert "[reason]" in formatted  # Optional argument
        assert "<yes|no>" in formatted  # Required choices
        assert "[high|medium|low]" in formatted  # Optional choices

    def test_role_specific_argument_resolution_logic(self):
        """Test that the user type resolution logic works for arguments."""

        @registry.command(
            name="role_args_cmd",
            description="Command with role-specific arguments",
            help_sections=[HelpSection.INFO],
            user_types=[UserType.STORYTELLER, UserType.PLAYER],
            arguments={
                UserType.STORYTELLER: [
                    CommandArgument("player1"),
                    CommandArgument("player2", optional=True)
                ],
                UserType.PLAYER: [
                    CommandArgument("player")
                ]
            }
        )
        async def role_args_command(message, argument):
            pass

        cmd = registry.commands["role_args_cmd"]

        # Test the resolution logic produces different outputs for different user types
        st_formatted = cmd.get_formatted_name_for_user(UserType.STORYTELLER)
        player_formatted = cmd.get_formatted_name_for_user(UserType.PLAYER)

        # Verify the logic produces different formats for different roles
        assert st_formatted != player_formatted
        assert "player1" in st_formatted and "player1" not in player_formatted
        assert "player2" in st_formatted and "player2" not in player_formatted

    def test_arguments_integrate_with_help_section_retrieval(self):
        """Test that argument formatting works with help system section retrieval logic."""

        @registry.command(
            name="help_integration_cmd",
            description="Test help integration",
            help_sections=[HelpSection.MISC],
            user_types=[UserType.STORYTELLER],
            arguments=[CommandArgument("target"), CommandArgument(("option1", "option2"))]
        )
        async def help_integration_command(message, argument):
            pass

        # Test that get_commands_by_section preserves argument functionality
        misc_commands = registry.get_commands_by_section(HelpSection.MISC)
        test_commands = [cmd for cmd in misc_commands if cmd.name == "help_integration_cmd"]

        assert len(test_commands) == 1
        cmd = test_commands[0]

        # Test that commands retrieved by section still have working argument formatting
        formatted = cmd.get_formatted_name_for_user(UserType.STORYTELLER)
        assert "<target>" in formatted
        assert "<option1|option2>" in formatted

        # Test that undefined user type falls back to UserType.PUBLIC arguments (which uses the list format)
        undefined_formatted = cmd.get_formatted_name_for_user(UserType.OBSERVER)  # Not defined, falls back to NONE
        assert "<target>" in undefined_formatted  # Should use the list arguments since no dict is used
        assert "<option1|option2>" in undefined_formatted

    def test_dictionary_arguments_must_match_user_types(self):
        """Test that dictionary arguments contain exactly the same user types as user_types field."""

        # Test valid case - arguments dict matches user_types exactly
        @registry.command(
            name="valid_dict_args",
            description="Test valid dictionary arguments",
            help_sections=[HelpSection.MISC],
            user_types=[UserType.STORYTELLER, UserType.PLAYER],
            arguments={
                UserType.STORYTELLER: [CommandArgument("player1"), CommandArgument("player2")],
                UserType.PLAYER: [CommandArgument("target")]
            }
        )
        async def valid_dict_args_command(message, argument):
            pass

        # This should work fine
        cmd = registry.commands["valid_dict_args"]
        assert cmd.get_arguments_for_user(UserType.STORYTELLER) == (
            CommandArgument("player1"), CommandArgument("player2"))
        assert cmd.get_arguments_for_user(UserType.PLAYER) == (CommandArgument("target"),)

        # Test validation logic manually (what the validation test should check)
        if isinstance(cmd.arguments, MappingProxyType):
            argument_user_types = set(cmd.arguments.keys())
            command_user_types = set(cmd.user_types)

            # Allow UserType.PUBLIC as a fallback in arguments dict even if not in user_types
            argument_user_types_without_fallback = argument_user_types - {UserType.PUBLIC}

            # Check that all non-fallback argument user types are in command user types
            extra_in_args = argument_user_types_without_fallback - command_user_types
            missing_from_args = command_user_types - argument_user_types_without_fallback

            # For this valid case, should have no mismatches
            assert not extra_in_args, f"Arguments dict has extra user types not in user_types: {extra_in_args}"
            assert not missing_from_args, f"Arguments dict missing user types from user_types: {missing_from_args}"

    def test_dictionary_descriptions_must_match_user_types(self):
        """Test that dictionary descriptions contain exactly the same user types as user_types field."""

        # Test valid case - description dict matches user_types exactly
        @registry.command(
            name="valid_dict_desc",
            description={
                UserType.STORYTELLER: "Storyteller description",
                UserType.PLAYER: "Player description"
            },
            help_sections=[HelpSection.MISC],
            user_types=[UserType.STORYTELLER, UserType.PLAYER]
        )
        async def valid_dict_desc_command(message, argument):
            pass

        # This should work fine
        cmd = registry.commands["valid_dict_desc"]
        assert cmd.get_description_for_user(UserType.STORYTELLER) == "Storyteller description"
        assert cmd.get_description_for_user(UserType.PLAYER) == "Player description"

        # Test validation logic manually (what the validation test should check)
        if isinstance(cmd.description, MappingProxyType):
            description_user_types = set(cmd.description.keys())
            command_user_types = set(cmd.user_types)

            # Allow UserType.PUBLIC as a fallback in description dict even if not in user_types
            description_user_types_without_fallback = description_user_types - {UserType.PUBLIC}

            # Check that all non-fallback description user types are in command user types
            extra_in_desc = description_user_types_without_fallback - command_user_types
            missing_from_desc = command_user_types - description_user_types_without_fallback

            # For this valid case, should have no mismatches
            assert not extra_in_desc, f"Description dict has extra user types not in user_types: {extra_in_desc}"
            assert not missing_from_desc, f"Description dict missing user types from user_types: {missing_from_desc}"

    def test_registry_validation_for_all_commands(self):
        """Test that all commands in the registry follow the dictionary user type rules."""

        def validate_command_consistency(cmd_info: CommandInfo):
            """Helper to validate a single command's consistency with strict user type matching."""
            from collections.abc import Mapping
            command_user_types = set(cmd_info.user_types)

            # Validate arguments dictionary if present - must match user_types exactly
            if isinstance(cmd_info.arguments, Mapping):
                argument_user_types = set(cmd_info.arguments.keys())
                assert argument_user_types == command_user_types, (
                    f"Command '{cmd_info.name}' arguments dict keys {argument_user_types} "
                    f"must exactly match user_types {command_user_types}"
                )

            # Validate description dictionary if present - must match user_types exactly
            if isinstance(cmd_info.description, Mapping):
                description_user_types = set(cmd_info.description.keys())
                assert description_user_types == command_user_types, (
                    f"Command '{cmd_info.name}' description dict keys {description_user_types} "
                    f"must exactly match user_types {command_user_types}"
                )

        # Validate all commands in the registry
        for command_name, command_info in registry.get_all_commands().items():
            validate_command_consistency(command_info)
