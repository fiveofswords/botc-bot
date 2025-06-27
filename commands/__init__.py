"""
Command system for the Blood on the Clocktower Discord bot.

This module provides the command registry system with help integration
and command categorization.
"""

from .command_enums import HelpSection, UserType, GamePhase
from .help_commands import HelpGenerator
from .registry import registry, CommandRegistry, ValidationError

__all__ = [
    'registry',
    'CommandRegistry',
    'ValidationError',
    'HelpSection',
    'UserType',
    'GamePhase',
    'HelpGenerator'
]
