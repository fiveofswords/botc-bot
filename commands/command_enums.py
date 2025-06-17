"""Enums for command help system categorization."""

from enum import Enum


class HelpSection(Enum):
    """Categories for help command organization."""
    COMMON = "common"
    PROGRESSION = "progression"
    DAY = "day"
    GAMESTATE = "gamestate"
    CONFIGURE = "configure"
    INFO = "info"
    MISC = "misc"
    PLAYER = "player"


class UserType(Enum):
    """Types of users for command visibility."""
    STORYTELLER = "storyteller"
    OBSERVER = "observer"
    PLAYER = "player"
    NONE = "none"  # Someone who is none of Storyteller, Observer, or Player
