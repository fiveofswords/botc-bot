"""Command registry system for organizing bot commands."""
from functools import wraps
from types import MappingProxyType
from typing import Dict, Callable, Awaitable, Optional, List, Union, NamedTuple

import discord

from commands.command_enums import HelpSection, UserType


class CommandInfo(NamedTuple):
    """Information about a registered command."""
    name: str
    handler: Callable
    description: Union[str, MappingProxyType[UserType, str]]
    help_sections: tuple[HelpSection, ...]
    user_types: tuple[UserType, ...]
    aliases: tuple[str, ...] = ()

    def get_description_for_user(self, user_type: UserType) -> str:
        """Get the appropriate description for a specific user type.
        
        When descriptions are provided as a dictionary:
        1. First tries to find description for the specific user_type
        2. Falls back to UserType.NONE if available
        3. Returns empty string if no match found
        
        This allows flexible description strategies:
        - Provide descriptions for all user types
        - Provide specific descriptions with NONE as fallback
        - Provide only specific descriptions (others get empty string)
        
        Args:
            user_type: The user type to get description for
            
        Returns:
            Description string for the user type, or empty string if not found
        """
        if isinstance(self.description, MappingProxyType):
            # Try specific user type first, then fallback to NONE, then empty string
            return (self.description.get(user_type) or
                    self.description.get(UserType.NONE) or "")
        else:
            # Single description string - works for all user types
            return self.description


class CommandRegistry:
    """Registry for bot commands with decorator-based registration."""

    def __init__(self):
        self.commands: Dict[str, CommandInfo] = {}
        self.aliases: Dict[str, str] = {}

    def command(self, name: str,
                description: Union[str, Dict[UserType, str]] = "",
                help_sections: Optional[List[HelpSection]] = None,
                user_types: Optional[List[UserType]] = None,
                aliases: Optional[List[str]] = None):
        """Decorator to register a command handler along with help metadata.

        Args:
            name (str): The primary name of the command.
            description (Union[str, dict[UserType, str]]): Help text for the command.
            help_sections (list[HelpSection]): Sections this command appears in.
            user_types (list[UserType]): User types that can access this command.
            aliases (list[str], optional): Alternative names for the command.

        Note:
            The `description` argument accepts either:
            - A string used for all user types.
            - A dict mapping `UserType` to role-specific descriptions.

            Description resolution order:
                1. User-specific key in the dict
                2. Fallback to `UserType.NONE`
                3. Empty string if no match found

            Examples:
                Single: `"command description"`
                Role-specific: `{UserType.PLAYER: "player desc", UserType.STORYTELLER: "storyteller desc"}`
                With fallback: `{UserType.STORYTELLER: "ST-only desc", UserType.NONE: "general desc"}`
        """
        if help_sections is None:
            help_sections = []
        if user_types is None:
            user_types = []
        if aliases is None:
            aliases = []

        def decorator(func: Callable[[discord.Message, str], Awaitable[None]]):
            # Convert mutable types to immutable for internal storage
            immutable_description = (
                MappingProxyType(description) if isinstance(description, dict)
                else description
            )
            
            command_info = CommandInfo(
                name=name,
                handler=func,
                description=immutable_description,
                help_sections=tuple(help_sections),
                user_types=tuple(user_types),
                aliases=tuple(aliases)
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
        if command_info:
            await command_info.handler(message, argument)
            return True
        return False

    def get_all_commands(self) -> Dict[str, CommandInfo]:
        """Get all registered commands."""
        return self.commands.copy()

    def get_commands_by_section(self, section: HelpSection) -> tuple[CommandInfo, ...]:
        """Get commands for a specific help section and user type."""
        result = []
        for command_info in self.commands.values():
            if section in command_info.help_sections:
                result.append(command_info)
        return tuple(sorted(result, key=lambda x: x.name))

    def get_commands_by_user_type(self, user_type: UserType) -> tuple[CommandInfo, ...]:
        """Get all commands available to a specific user type."""
        result = []
        for command_info in self.commands.values():
            if user_type in command_info.user_types or UserType.NONE in command_info.user_types:
                result.append(command_info)
        return tuple(sorted(result, key=lambda x: x.name))

    def log_registered_commands(self, logger):
        """Log all registered commands at startup."""
        command_list = sorted(self.commands.keys())
        alias_info = []

        for alias, command in self.aliases.items():
            alias_info.append(f"{alias} -> {command}")

        logger.info(f"📋 Command Registry: {len(command_list)} commands registered")
        logger.info(f"Commands: {', '.join(command_list)}")

        if alias_info:
            logger.info(f"Aliases: {', '.join(alias_info)}")


# Global registry instance
registry = CommandRegistry()
