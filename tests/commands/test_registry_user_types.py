"""
Tests for command registry user-type-specific help descriptions.

This module tests the enhanced registry functionality that supports
different help descriptions for different user types (player vs storyteller).
"""

from commands.command_enums import HelpSection, UserType
from commands.registry import CommandRegistry, CommandInfo


class TestRegistryUserTypeDescriptions:
    """Test user-type-specific descriptions in the command registry."""

    def setup_method(self):
        """Set up a fresh registry for each test."""
        self.registry = CommandRegistry()

    def test_single_string_description(self):
        """Test traditional single string descriptions work unchanged."""

        @self.registry.command(
            name="simple",
            description="Simple command for everyone",
            help_sections=[HelpSection.COMMON],
            user_types=[UserType.NONE]
        )
        async def simple_command(message, argument):
            pass

        command_info = self.registry.commands["simple"]

        # Should return same description for all user types
        assert command_info.get_description_for_user(UserType.PLAYER) == "Simple command for everyone"
        assert command_info.get_description_for_user(UserType.STORYTELLER) == "Simple command for everyone"
        assert command_info.get_description_for_user(UserType.NONE) == "Simple command for everyone"

    def test_user_type_specific_descriptions(self):
        """Test user-type-specific descriptions work correctly."""

        @self.registry.command(
            name="vote",
            description={
                UserType.PLAYER: "votes yes/no on ongoing nomination (only during your turn)",
                UserType.STORYTELLER: "votes for the current player (prompts for player selection)"
            },
            help_sections=[HelpSection.DAY],
            user_types=[UserType.NONE]
        )
        async def vote_command(message, argument):
            pass

        command_info = self.registry.commands["vote"]

        # Should return different descriptions for different user types
        assert command_info.get_description_for_user(
            UserType.PLAYER) == "votes yes/no on ongoing nomination (only during your turn)"
        assert command_info.get_description_for_user(
            UserType.STORYTELLER) == "votes for the current player (prompts for player selection)"

    def test_fallback_to_all_user_type(self):
        """Test fallback to UserType.NONE when specific type not found."""

        @self.registry.command(
            name="complex",
            description={
                UserType.STORYTELLER: "Storyteller-specific functionality",
                UserType.NONE: "General fallback description"
            },
            help_sections=[HelpSection.CONFIGURE],
            user_types=[UserType.NONE]
        )
        async def complex_command(message, argument):
            pass

        command_info = self.registry.commands["complex"]

        # STORYTELLER should get specific description
        assert command_info.get_description_for_user(UserType.STORYTELLER) == "Storyteller-specific functionality"

        # PLAYER should fall back to ALL description
        assert command_info.get_description_for_user(UserType.PLAYER) == "General fallback description"

        # ALL should get its own description
        assert command_info.get_description_for_user(UserType.NONE) == "General fallback description"

    def test_missing_description_returns_empty_string(self):
        """Test that missing descriptions return empty string."""

        @self.registry.command(
            name="partial",
            description={
                UserType.STORYTELLER: "Only storytellers see this"
            },
            help_sections=[HelpSection.CONFIGURE],
            user_types=[UserType.NONE]
        )
        async def partial_command(message, argument):
            pass

        command_info = self.registry.commands["partial"]

        # STORYTELLER should get specific description
        assert command_info.get_description_for_user(UserType.STORYTELLER) == "Only storytellers see this"

        # PLAYER should get empty string (no fallback available)
        assert command_info.get_description_for_user(UserType.PLAYER) == ""

        # ALL should get empty string (no fallback available)
        assert command_info.get_description_for_user(UserType.NONE) == ""

    def test_empty_description_dict(self):
        """Test behavior with empty description dictionary."""

        @self.registry.command(
            name="empty",
            description={},
            help_sections=[HelpSection.MISC],
            user_types=[UserType.NONE]
        )
        async def empty_command(message, argument):
            pass

        command_info = self.registry.commands["empty"]

        # All user types should get empty string
        assert command_info.get_description_for_user(UserType.PLAYER) == ""
        assert command_info.get_description_for_user(UserType.STORYTELLER) == ""
        assert command_info.get_description_for_user(UserType.NONE) == ""

    def test_get_commands_by_user_type_with_specific_descriptions(self):
        """Test that get_commands_by_user_type works with user-specific descriptions."""

        @self.registry.command(
            name="player_cmd",
            description={
                UserType.PLAYER: "Player-specific description",
                UserType.NONE: "Fallback description"
            },
            help_sections=[HelpSection.PLAYER],
            user_types=[UserType.PLAYER]
        )
        async def player_command(message, argument):
            pass

        @self.registry.command(
            name="storyteller_cmd",
            description={
                UserType.STORYTELLER: "Storyteller-specific description"
            },
            help_sections=[HelpSection.CONFIGURE],
            user_types=[UserType.STORYTELLER]
        )
        async def storyteller_command(message, argument):
            pass

        @self.registry.command(
            name="all_cmd",
            description={
                UserType.PLAYER: "Player view",
                UserType.STORYTELLER: "Storyteller view"
            },
            help_sections=[HelpSection.COMMON],
            user_types=[UserType.NONE]
        )
        async def all_command(message, argument):
            pass

        # Test player commands
        player_commands = self.registry.get_commands_by_user_type(UserType.PLAYER)
        player_names = [cmd.name for cmd in player_commands]

        assert "player_cmd" in player_names
        assert "all_cmd" in player_names
        assert "storyteller_cmd" not in player_names

        # Test storyteller commands
        storyteller_commands = self.registry.get_commands_by_user_type(UserType.STORYTELLER)
        storyteller_names = [cmd.name for cmd in storyteller_commands]

        assert "storyteller_cmd" in storyteller_names
        assert "all_cmd" in storyteller_names
        assert "player_cmd" not in storyteller_names

        # Verify descriptions are correct for each user type
        all_cmd_info = self.registry.commands["all_cmd"]
        assert all_cmd_info.get_description_for_user(UserType.PLAYER) == "Player view"
        assert all_cmd_info.get_description_for_user(UserType.STORYTELLER) == "Storyteller view"

    def test_get_commands_by_section_with_user_types(self):
        """Test that get_commands_by_section works with user-specific descriptions."""

        @self.registry.command(
            name="day_cmd",
            description={
                UserType.PLAYER: "Player day command",
                UserType.STORYTELLER: "Storyteller day command"
            },
            help_sections=[HelpSection.DAY],
            user_types=[UserType.NONE]
        )
        async def day_command(message, argument):
            pass

        # Test getting day commands for different user types
        player_day_commands = self.registry.get_commands_by_section(HelpSection.DAY)
        storyteller_day_commands = self.registry.get_commands_by_section(HelpSection.DAY)

        # Both should contain the command
        assert len(player_day_commands) == 1
        assert len(storyteller_day_commands) == 1

        # But descriptions should be different
        cmd_info = player_day_commands[0]
        assert cmd_info.get_description_for_user(UserType.PLAYER) == "Player day command"
        assert cmd_info.get_description_for_user(UserType.STORYTELLER) == "Storyteller day command"

    def test_command_info_direct_instantiation(self):
        """Test CommandInfo can be instantiated directly with different description types."""
        from types import MappingProxyType
        
        # Test with string description
        cmd1 = CommandInfo(
            name="test1",
            handler=lambda: None,
            description="Simple description",
            help_sections=(HelpSection.COMMON,),
            user_types=(UserType.NONE,)
        )

        assert cmd1.get_description_for_user(UserType.PLAYER) == "Simple description"
        assert cmd1.get_description_for_user(UserType.STORYTELLER) == "Simple description"

        # Test with MappingProxyType description (immutable dict)
        cmd2 = CommandInfo(
            name="test2",
            handler=lambda: None,
            description=MappingProxyType({
                UserType.PLAYER: "Player desc",
                UserType.STORYTELLER: "Storyteller desc"
            }),
            help_sections=(HelpSection.COMMON,),
            user_types=(UserType.NONE,)
        )

        assert cmd2.get_description_for_user(UserType.PLAYER) == "Player desc"
        assert cmd2.get_description_for_user(UserType.STORYTELLER) == "Storyteller desc"

    def test_realistic_vote_command_scenario(self):
        """Test a realistic scenario mimicking the actual vote command needs."""

        @self.registry.command(
            name="vote",
            description={
                UserType.PLAYER: "votes yes/no on ongoing nomination. Only works during your voting turn. Use 'yes', 'y', 'no', or 'n'.",
                UserType.STORYTELLER: "votes for the current player. Bot will prompt you to select which player to vote for. Timeout: 30 seconds."
            },
            help_sections=[HelpSection.DAY, HelpSection.PLAYER],
            user_types=[UserType.NONE],
            aliases=["v"]
        )
        async def vote_command(message, argument):
            pass

        # Test the main command
        vote_info = self.registry.commands["vote"]

        player_desc = vote_info.get_description_for_user(UserType.PLAYER)
        storyteller_desc = vote_info.get_description_for_user(UserType.STORYTELLER)

        assert "only works during your voting turn" in player_desc.lower()
        assert "bot will prompt you" in storyteller_desc.lower()

        # Test alias works
        assert "v" in self.registry.aliases
        assert self.registry.aliases["v"] == "vote"

        # Test it appears in correct sections for both user types
        day_player_cmds = self.registry.get_commands_by_section(HelpSection.DAY)
        day_storyteller_cmds = self.registry.get_commands_by_section(HelpSection.DAY)

        assert any(cmd.name == "vote" for cmd in day_player_cmds)
        assert any(cmd.name == "vote" for cmd in day_storyteller_cmds)

        # Verify different descriptions in context
        vote_in_player_section = next(cmd for cmd in day_player_cmds if cmd.name == "vote")
        vote_in_storyteller_section = next(cmd for cmd in day_storyteller_cmds if cmd.name == "vote")

        assert vote_in_player_section.get_description_for_user(
            UserType.PLAYER) != vote_in_storyteller_section.get_description_for_user(UserType.STORYTELLER)
