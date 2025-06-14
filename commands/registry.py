"""Command registry system for organizing bot commands."""
from functools import wraps
from typing import Dict, Callable, Awaitable, Optional

import discord


class CommandRegistry:
    """Registry for bot commands with decorator-based registration."""

    def __init__(self):
        self.commands: Dict[str, Callable] = {}
        self.aliases: Dict[str, str] = {}

    def command(self, name: str, aliases: Optional[list] = None):
        """Decorator to register a command handler."""

        def decorator(func: Callable[[discord.Message, str], Awaitable[None]]):
            self.commands[name] = func

            # Register aliases
            if aliases:
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

        handler = self.commands.get(actual_command)
        if handler:
            await handler(message, argument)
            return True
        return False

    def get_all_commands(self) -> Dict[str, Callable]:
        """Get all registered commands."""
        return self.commands.copy()

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
