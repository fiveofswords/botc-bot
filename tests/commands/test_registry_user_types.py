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

    def test_get_commands_by_user_type_with_specific_descriptions(self):
        """Test that get_commands_by_user_type works with user-specific descriptions."""

        @self.registry.command(
            name="player_cmd",
            description={
                UserType.PLAYER: "Player-specific description"
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
            user_types=[UserType.PLAYER, UserType.STORYTELLER],
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


class TestUserTypeConsistencyValidation:
    """Test that command descriptions and arguments have consistent user_types."""

    def setup_method(self):
        """Set up a fresh registry for each test."""
        self.registry = CommandRegistry()

    def test_description_dict_must_match_user_types_exactly(self):
        """Test that description dict keys match command user_types exactly."""

        # Valid command with matching user types
        @self.registry.command(
            name="valid_cmd",
            description={
                UserType.PLAYER: "Player description",
                UserType.STORYTELLER: "Storyteller description"
            },
            user_types=[UserType.PLAYER, UserType.STORYTELLER]
        )
        async def valid_command(message, argument):
            pass

        # Valid command with NONE
        @self.registry.command(
            name="valid_none_cmd",
            description={
                UserType.NONE: "Description for users with no specific role"
            },
            user_types=[UserType.NONE]
        )
        async def valid_none_command(message, argument):
            pass

        # Check that all registered commands have consistent user types
        def validate_command_user_types(registry):
            from collections.abc import Mapping
            errors = []
            for command_name, command_info in registry.commands.items():
                if isinstance(command_info.description, Mapping):
                    desc_user_types = set(command_info.description.keys())
                    command_user_types = set(command_info.user_types)

                    if desc_user_types != command_user_types:
                        errors.append(f"Command '{command_name}' has description keys {desc_user_types} "
                                      f"but user_types {command_user_types}. They must match exactly.")

                if isinstance(command_info.arguments, Mapping):
                    args_user_types = set(command_info.arguments.keys())
                    command_user_types = set(command_info.user_types)

                    if args_user_types != command_user_types:
                        errors.append(f"Command '{command_name}' has argument keys {args_user_types} "
                                      f"but user_types {command_user_types}. They must match exactly.")
            return errors

        errors = validate_command_user_types(self.registry)
        assert len(errors) == 0, f"Found validation errors: {errors}"

    def test_arguments_dict_must_match_user_types_exactly(self):
        """Test that arguments dict keys match command user_types exactly."""

        from commands.registry import CommandArgument

        # Valid command with matching user types  
        @self.registry.command(
            name="valid_args_cmd",
            arguments={
                UserType.PLAYER: [CommandArgument("player_name")],
                UserType.STORYTELLER: [CommandArgument("player1"), CommandArgument("player2")]
            },
            user_types=[UserType.PLAYER, UserType.STORYTELLER]
        )
        async def valid_args_command(message, argument):
            pass

        # Valid command with NONE arguments
        @self.registry.command(
            name="valid_none_args_cmd",
            arguments={
                UserType.NONE: [CommandArgument("general_arg")]
            },
            user_types=[UserType.NONE]
        )
        async def valid_none_args_command(message, argument):
            pass

        # Validation should pass for both commands
        from collections.abc import Mapping
        for command_name, command_info in self.registry.commands.items():
            if isinstance(command_info.arguments, Mapping):
                args_user_types = set(command_info.arguments.keys())
                command_user_types = set(command_info.user_types)

                assert args_user_types == command_user_types, (
                    f"Command '{command_name}' has argument keys {args_user_types} "
                    f"but user_types {command_user_types}. They must match exactly."
                )

    def test_missing_user_type_in_description_dict_fails(self):
        """Test that missing user types in description dict are detected."""

        # Register a command missing a user type in description
        @self.registry.command(
            name="missing_desc_cmd",
            description={
                UserType.PLAYER: "Player description"
                # Missing UserType.STORYTELLER
            },
            user_types=[UserType.PLAYER, UserType.STORYTELLER]
        )
        async def missing_desc_command(message, argument):
            pass

        # Validation should fail
        command_info = self.registry.commands["missing_desc_cmd"]
        desc_user_types = set(command_info.description.keys())
        command_user_types = set(command_info.user_types)

        assert desc_user_types != command_user_types, (
            "Command should have been detected as invalid - missing user type in description"
        )

    def test_extra_user_type_in_description_dict_fails(self):
        """Test that extra user types in description dict are detected."""

        # Register a command with extra user type in description
        @self.registry.command(
            name="extra_desc_cmd",
            description={
                UserType.PLAYER: "Player description",
                UserType.OBSERVER: "Observer description"  # Not in user_types
            },
            user_types=[UserType.PLAYER]
        )
        async def extra_desc_command(message, argument):
            pass

        # Validation should fail
        command_info = self.registry.commands["extra_desc_cmd"]
        desc_user_types = set(command_info.description.keys())
        command_user_types = set(command_info.user_types)

        assert desc_user_types != command_user_types, (
            "Command should have been detected as invalid - extra user type in description"
        )

    def test_missing_user_type_in_arguments_dict_fails(self):
        """Test that missing user types in arguments dict are detected."""

        from commands.registry import CommandArgument

        # Register a command missing a user type in arguments
        @self.registry.command(
            name="missing_args_cmd",
            arguments={
                UserType.PLAYER: [CommandArgument("player_name")]
                # Missing UserType.STORYTELLER
            },
            user_types=[UserType.PLAYER, UserType.STORYTELLER]
        )
        async def missing_args_command(message, argument):
            pass

        # Validation should fail
        command_info = self.registry.commands["missing_args_cmd"]
        args_user_types = set(command_info.arguments.keys())
        command_user_types = set(command_info.user_types)

        assert args_user_types != command_user_types, (
            "Command should have been detected as invalid - missing user type in arguments"
        )

    def test_extra_user_type_in_arguments_dict_fails(self):
        """Test that extra user types in arguments dict are detected."""

        from commands.registry import CommandArgument

        # Register a command with extra user type in arguments
        @self.registry.command(
            name="extra_args_cmd",
            arguments={
                UserType.PLAYER: [CommandArgument("player_name")],
                UserType.OBSERVER: [CommandArgument("target")]  # Not in user_types
            },
            user_types=[UserType.PLAYER]
        )
        async def extra_args_command(message, argument):
            pass

        # Validation should fail
        command_info = self.registry.commands["extra_args_cmd"]
        args_user_types = set(command_info.arguments.keys())
        command_user_types = set(command_info.user_types)

        assert args_user_types != command_user_types, (
            "Command should have been detected as invalid - extra user type in arguments"
        )

    def test_validate_all_commands_in_registry(self):
        """Test validation function that checks all commands in registry for user type consistency."""

        from commands.registry import CommandArgument

        # Add valid commands
        @self.registry.command(
            name="good_cmd1",
            description="Simple string description",  # Not a dict, so no validation needed
            user_types=[UserType.PLAYER]
        )
        async def good_command1(message, argument):
            pass

        @self.registry.command(
            name="good_cmd2",
            description={
                UserType.PLAYER: "Player desc",
                UserType.STORYTELLER: "ST desc"
            },
            arguments={
                UserType.PLAYER: [CommandArgument("arg1")],
                UserType.STORYTELLER: [CommandArgument("arg2")]
            },
            user_types=[UserType.PLAYER, UserType.STORYTELLER]
        )
        async def good_command2(message, argument):
            pass

        @self.registry.command(
            name="good_none_cmd",
            description={
                UserType.NONE: "Description for users with no specific role"
            },
            arguments={
                UserType.NONE: [CommandArgument("general_arg")]
            },
            user_types=[UserType.NONE]
        )
        async def good_none_command(message, argument):
            pass

        # Add invalid commands
        @self.registry.command(
            name="bad_desc_cmd",
            description={
                UserType.PLAYER: "Player desc",
                UserType.OBSERVER: "Observer desc"  # Invalid - not in user_types
            },
            user_types=[UserType.PLAYER]
        )
        async def bad_desc_command(message, argument):
            pass

        @self.registry.command(
            name="bad_args_cmd",
            arguments={
                UserType.STORYTELLER: [CommandArgument("arg1")]  # Invalid - not in user_types
            },
            user_types=[UserType.PLAYER]
        )
        async def bad_args_command(message, argument):
            pass

        # Function to validate all commands
        def validate_all_commands(registry):
            from collections.abc import Mapping
            errors = []
            for command_name, command_info in registry.commands.items():
                command_user_types = set(command_info.user_types)

                # Check description consistency
                if isinstance(command_info.description, Mapping):
                    desc_user_types = set(command_info.description.keys())
                    if desc_user_types != command_user_types:
                        errors.append(
                            f"Command '{command_name}' description keys {desc_user_types} != user_types {command_user_types}")

                # Check arguments consistency
                if isinstance(command_info.arguments, Mapping):
                    args_user_types = set(command_info.arguments.keys())
                    if args_user_types != command_user_types:
                        errors.append(
                            f"Command '{command_name}' argument keys {args_user_types} != user_types {command_user_types}")

            return errors

        errors = validate_all_commands(self.registry)

        # Should find errors in both bad commands
        assert len(errors) == 2
        assert any("bad_desc_cmd" in error and "description keys" in error for error in errors)
        assert any("bad_args_cmd" in error and "argument keys" in error for error in errors)

    def test_global_registry_user_type_consistency(self):
        """Test that the actual global registry has consistent user types."""

        from commands.registry import registry as global_registry
        from collections.abc import Mapping

        errors = []
        for command_name, command_info in global_registry.commands.items():
            command_user_types = set(command_info.user_types)

            # Check description consistency
            if isinstance(command_info.description, Mapping):
                desc_user_types = set(command_info.description.keys())
                if desc_user_types != command_user_types:
                    errors.append(
                        f'Command "{command_name}" description keys {desc_user_types} != user_types {command_user_types}')

            # Check arguments consistency
            if isinstance(command_info.arguments, Mapping):
                args_user_types = set(command_info.arguments.keys())
                if args_user_types != command_user_types:
                    errors.append(
                        f'Command "{command_name}" argument keys {args_user_types} != user_types {command_user_types}')

        # Print errors for debugging if test fails
        if errors:
            print("\nGlobal registry validation errors:")
            for error in errors:
                print(f"  {error}")

        assert len(errors) == 0, f"Global registry has {len(errors)} user type consistency violations: {errors}"
