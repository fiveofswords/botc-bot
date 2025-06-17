"""Command registry system for organizing bot commands."""
from functools import wraps
from types import MappingProxyType
from typing import Dict, Callable, Awaitable, Optional, List, Union, NamedTuple

import discord

from commands.command_enums import (
    HelpSection, UserType, GamePhase
)


class CommandArgument(NamedTuple):
    """Definition of a command argument.
    
    Args:
        name_or_choices: Either a string (for generic arguments like "player") 
                        or a tuple of strings (for specific choices like ("yes", "no"))
        optional: Whether the argument is optional (default: False)
    
    Examples:
        CommandArgument("player")                    # Required generic argument
        CommandArgument("player", optional=True)     # Optional generic argument  
        CommandArgument(("yes", "no"))              # Required choice argument
        CommandArgument(("red", "blue"), optional=True) # Optional choice argument
    """
    name_or_choices: Union[str, tuple[str, ...]]
    optional: bool = False


class CommandInfo(NamedTuple):
    """Information about a registered command."""
    name: str
    handler: Callable
    description: Union[str, MappingProxyType[UserType, str]]
    help_sections: tuple[HelpSection, ...]
    user_types: tuple[UserType, ...]
    aliases: tuple[str, ...] = ()
    arguments: Union[tuple[CommandArgument, ...], MappingProxyType[UserType, tuple[CommandArgument, ...]]] = ()
    # New requirement fields  
    required_phases: tuple[GamePhase, ...] = ()
    implemented: bool = True

    def get_description_for_user(self, user_type: UserType) -> str:
        """Get the appropriate description for a specific user type.
        
        Args:
            user_type: The user type to get description for
            
        Returns:
            Description string for the user type
            
        Raises:
            KeyError: If user_type is not found in description dict
        """
        if isinstance(self.description, MappingProxyType):
            return self.description[user_type]
        else:
            # Single description string - works for all user types
            return self.description

    def get_arguments_for_user(self, user_type: UserType) -> tuple[CommandArgument, ...]:
        """Get the appropriate arguments for a specific user type.
        
        Args:
            user_type: The user type to get arguments for
            
        Returns:
            Tuple of CommandArgument for the user type
            
        Raises:
            KeyError: If user_type is not found in arguments dict
        """
        if isinstance(self.arguments, MappingProxyType):
            return self.arguments[user_type]
        else:
            return self.arguments

    def get_formatted_name_for_user(self, user_type: UserType) -> str:
        """Get the command name formatted with arguments for a specific user type.
        
        Args:
            user_type: The user type to format for
            
        Returns:
            Formatted command name with arguments (e.g., "execute <player>")
        """
        args = self.get_arguments_for_user(user_type)
        if not args:
            return self.name

        def _format_arg(arg: CommandArgument) -> str:
            wrapper = "[{}]" if arg.optional else "<{}>"
            if isinstance(arg.name_or_choices, tuple):
                return wrapper.format("|".join(arg.name_or_choices))
            return wrapper.format(arg.name_or_choices)

        formatted_args = [_format_arg(arg) for arg in args]
        return f"{self.name} {' '.join(formatted_args)}"


class CommandRegistry:
    """Registry for bot commands with decorator-based registration."""

    def __init__(self):
        self.commands: Dict[str, CommandInfo] = {}
        self.aliases: Dict[str, str] = {}

    def command(self, name: str,
                aliases: Optional[List[str]] = None,
                user_types: Optional[List[UserType]] = None,
                arguments: Union[List[CommandArgument], Dict[UserType, List[CommandArgument]]] = None,
                description: Union[str, Dict[UserType, str]] = "",
                help_sections: Optional[List[HelpSection]] = None,
                # New requirement parameters
                required_phases: Optional[List[GamePhase]] = None,
                implemented: bool = True):
        """Decorator to register a command handler along with help metadata and requirements.

        Args:
            name (str): The primary name of the command.
            aliases (list[str], optional): Alternative names for the command.
            user_types (list[UserType]): User types that can access this command.
            arguments (Union[list[CommandArgument], dict[UserType, list[CommandArgument]]], optional):
                Command arguments, either shared or per user type.
            description (Union[str, dict[UserType, str]]): Help text for the command.
            help_sections (list[HelpSection]): Sections this command appears in.
            required_phases (list[GamePhase], optional): Required game phases. 
                Empty list = no game needed, [DAY] = day only, [NIGHT] = night only,
                [DAY, NIGHT] = works in any phase when game exists.
            implemented (bool): Whether this command implementation should be used (default: True).
                Set to False during migration to fall back to bot_impl.

        Note:
            The `description` and `arguments` parameters accept either:
            - A string/list used for all user types
            - A dict mapping `UserType` to role-specific descriptions/arguments
            
            **IMPORTANT**: When using dictionaries, they must contain exactly the same
            user types as specified in `user_types`. No fallback behavior exists - 
            missing user types will raise KeyError.

            Examples:
                ```python
                @registry.command(
                    name="kill",
                    description="Kill a player (make them a ghost)",
                    help_sections=[HelpSection.COMMON],
                    user_types=[UserType.STORYTELLER],
                    arguments=[CommandArgument("player")],
                    required_phases=[GamePhase.DAY, GamePhase.NIGHT]  # Works in any phase
                )
                ```
        """
        if help_sections is None:
            help_sections = []
        if user_types is None:
            user_types = []
        if aliases is None:
            aliases = []
        if arguments is None:
            arguments = []
        if required_phases is None:
            required_phases = []

        def decorator(func: Callable[[discord.Message, str], Awaitable[None]]):
            # Convert mutable types to immutable for internal storage
            immutable_description = (
                MappingProxyType(description) if isinstance(description, dict)
                else description
            )

            immutable_arguments = (
                MappingProxyType({k: tuple(v) for k, v in arguments.items()}) if isinstance(arguments, dict)
                else tuple(arguments)
            )

            command_info = CommandInfo(
                name=name,
                handler=func,
                description=immutable_description,
                help_sections=tuple(help_sections),
                user_types=tuple(user_types),
                aliases=tuple(aliases),
                arguments=immutable_arguments,
                # New requirement fields
                required_phases=tuple(required_phases),
                implemented=implemented
            )
            self.commands[name] = command_info

            # Register aliases
            for alias in aliases:
                self.aliases[alias] = name

            @wraps(func)
            async def wrapper(*args, **kwargs):
                return await func(*args, **kwargs)

            return wrapper

        return decorator

    async def handle_command(self, command: str, message: discord.Message, argument: str):
        """Handle a command by looking up and calling its handler."""
        # Check for alias first
        actual_command = self.aliases.get(command, command)

        command_info = self.commands.get(actual_command)
        if command_info and command_info.implemented:
            await command_info.handler(message, argument)
            return True
        return False  # Fall back to bot_impl for unimplemented commands

    def get_all_commands(self) -> Dict[str, CommandInfo]:
        """Get all registered commands."""
        return self.commands.copy()

    def get_commands_by_section(self, section: HelpSection) -> tuple[CommandInfo, ...]:
        """Get commands for a specific help section."""
        result = []
        for command_info in self.commands.values():
            if section in command_info.help_sections:
                result.append(command_info)
        return tuple(sorted(result, key=lambda x: x.name))

    def get_commands_by_user_type(self, user_type: UserType) -> tuple[CommandInfo, ...]:
        """Get all commands available to a specific user type."""
        result = []
        for command_info in self.commands.values():
            if user_type in command_info.user_types or UserType.PUBLIC in command_info.user_types:
                result.append(command_info)
        return tuple(sorted(result, key=lambda x: x.name))

    def log_registered_commands(self, logger):
        """Log all registered commands at startup, differentiating implemented vs skeleton."""
        implemented_commands = []
        skeleton_commands = []

        for name, command_info in self.commands.items():
            if command_info.implemented:
                implemented_commands.append(name)
            else:
                skeleton_commands.append(name)

        implemented_commands.sort()
        skeleton_commands.sort()

        total_commands = len(implemented_commands) + len(skeleton_commands)

        # Log summary
        logger.info(f"📋 Command Registry: {total_commands} commands registered")
        logger.info(f"✅ Implemented: {len(implemented_commands)} commands")
        logger.info(f"🏗️ Skeleton (fallback to bot_impl): {len(skeleton_commands)} commands")

        # Log detailed lists
        if implemented_commands:
            logger.info(f"Implemented commands: {', '.join(implemented_commands)}")

        if skeleton_commands:
            logger.info(f"Skeleton commands: {', '.join(skeleton_commands)}")

        # Log aliases, split by implementation status
        implemented_aliases = []
        skeleton_aliases = []
        
        for alias, command in self.aliases.items():
            alias_entry = f"{alias} -> {command}"
            command_info = self.commands.get(command)
            if command_info and command_info.implemented:
                implemented_aliases.append(alias_entry)
            else:
                skeleton_aliases.append(alias_entry)

        if implemented_aliases:
            logger.info(f"✅ Implemented aliases: {', '.join(implemented_aliases)}")

        if skeleton_aliases:
            logger.info(f"🏗️ Skeleton aliases: {', '.join(skeleton_aliases)}")

    def save_state(self) -> tuple[dict, dict]:
        """Save the current state of the registry for restoration later.
        
        Returns:
            Tuple of (commands_copy, aliases_copy) for restoration
        """
        return (self.commands.copy(), self.aliases.copy())

    def restore_state(self, state: tuple[dict, dict]) -> None:
        """Restore the registry to a previously saved state.
        
        Args:
            state: Tuple of (commands, aliases) from save_state()
        """
        commands, aliases = state
        self.commands = commands.copy()
        self.aliases = aliases.copy()

    def clear(self) -> None:
        """Clear all commands and aliases from the registry."""
        self.commands.clear()
        self.aliases.clear()


# Global registry instance
registry = CommandRegistry()
