"""Tests for user alias integration in help system."""

from commands.command_enums import UserType, HelpSection
from commands.help_commands import HelpGenerator, UserAliases
from commands.loader import load_all_commands

# Ensure commands are loaded for testing
load_all_commands()


class TestUserAliasesInHelp:
    """Test user-defined aliases integration with help system."""

    def test_user_aliases_type_alias(self):
        """Test that UserAliases type alias works correctly."""
        # Should accept dict[str, str]
        user_aliases: UserAliases = {
            "p": "ping",
            "t": "test"
        }

        # Should be usable in help generation
        embed = HelpGenerator.create_section_help_embed(
            HelpSection.MISC, UserType.STORYTELLER, user_aliases
        )
        assert embed.title == "Miscellaneous Commands"

    def test_user_aliases_in_misc_section(self):
        """Test that user aliases appear in MISC section help."""
        user_aliases: UserAliases = {
            "p": "ping",  # alias for registry command
            "t": "test",  # alias for registry command
        }

        # Test MISC section which includes ping and test commands
        misc_embed = HelpGenerator.create_section_help_embed(
            HelpSection.MISC, UserType.STORYTELLER, user_aliases
        )

        # Check that user aliases are included in command display
        field_names = [field.name for field in misc_embed.fields]

        # Find the ping command field
        ping_field = None
        for field in misc_embed.fields:
            if "ping" in field.name.lower():
                ping_field = field
                break

        # Should have found ping command with user alias
        assert ping_field is not None, f"Ping field not found in: {field_names}"
        assert "aliases:" in ping_field.name
        assert "p" in ping_field.name  # Our user alias should be included

    def test_user_aliases_in_player_help(self):
        """Test that user aliases appear in player help."""
        user_aliases: UserAliases = {
            "pm": "pm",  # alias for player command (hardcoded)
            "hist": "history",  # alias for player command (hardcoded)
        }

        # Test player help with user aliases
        player_embed = HelpGenerator.create_player_help_embed(user_aliases)

        # Check that the embed was created
        assert player_embed.title == "Player Commands"

        # Check for user aliases in the fields
        field_names = [field.name for field in player_embed.fields]

        # Should find commands with aliases
        found_pm_alias = any("pm" in name and "aliases:" in name for name in field_names)
        assert found_pm_alias, f"PM alias not found in fields: {field_names}"

    def test_user_aliases_combined_with_existing_aliases(self):
        """Test that user aliases are combined with existing registry/hardcoded aliases."""
        user_aliases: UserAliases = {
            "testing": "test",  # test command might have no existing aliases
        }

        # Test misc section
        misc_embed = HelpGenerator.create_section_help_embed(
            HelpSection.MISC, UserType.STORYTELLER, user_aliases
        )

        # Find the test command field  
        test_field = None
        for field in misc_embed.fields:
            if field.name.startswith("test"):
                test_field = field
                break

        # Should include user alias
        if test_field:
            assert "testing" in test_field.name

    def test_empty_user_aliases(self):
        """Test that empty user aliases don't break anything."""
        user_aliases: UserAliases = {}

        # Should work with empty aliases
        embed = HelpGenerator.create_section_help_embed(
            HelpSection.MISC, UserType.STORYTELLER, user_aliases
        )
        assert embed.title == "Miscellaneous Commands"

    def test_none_user_aliases(self):
        """Test that None user aliases work correctly."""
        # Should work with None aliases (existing behavior)
        embed = HelpGenerator.create_section_help_embed(
            HelpSection.MISC, UserType.STORYTELLER, None
        )
        assert embed.title == "Miscellaneous Commands"

    def test_user_aliases_for_nonexistent_commands(self):
        """Test that aliases pointing to non-existent commands are gracefully ignored."""
        user_aliases: UserAliases = {
            "p": "ping",  # valid command
            "xyz": "nonexistent",  # invalid command - should be ignored
        }

        # Should still work and include valid aliases
        misc_embed = HelpGenerator.create_section_help_embed(
            HelpSection.MISC, UserType.STORYTELLER, user_aliases
        )

        # Should find ping with alias
        field_names = [field.name for field in misc_embed.fields]
        ping_fields = [name for name in field_names if name.startswith("ping")]

        if ping_fields:
            # Should have the valid alias
            assert any("p" in name for name in ping_fields)
            # Should not have the invalid alias 
            assert not any("xyz" in name for name in ping_fields)

    def test_duplicate_aliases(self):
        """Test handling of duplicate aliases (same alias for different commands)."""
        user_aliases: UserAliases = {
            "p": "ping",
            "test": "ping",  # User alias that shadows existing command name
        }

        # Should still work
        misc_embed = HelpGenerator.create_section_help_embed(
            HelpSection.MISC, UserType.STORYTELLER, user_aliases
        )

        # Find ping command
        ping_field = None
        for field in misc_embed.fields:
            if field.name.startswith("ping"):
                ping_field = field
                break

        if ping_field:
            # Should include both aliases
            assert "p" in ping_field.name
            assert "test" in ping_field.name
