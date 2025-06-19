"""Enums for command help system categorization and requirements."""

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
    """Types of users for command visibility and permission checking."""
    STORYTELLER = "storyteller"
    OBSERVER = "observer"
    PLAYER = "player"
    PUBLIC = "public"  # Someone who is none of Storyteller, Observer, or Player


class GamePhase(Enum):
    """Game phases for phase requirements."""
    DAY = "day"  # Day phase
    NIGHT = "night"  # Night phase
