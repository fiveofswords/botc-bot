"""
Character classes for Blood on the Clocktower game.
"""

# Import base classes and modifiers
from .base import (
    Character, Townsfolk, Outsider, Minion, Demon, Traveler, Storyteller,
    SeatingOrderModifier, DayStartModifier, NomsCalledModifier, NominationModifier,
    DayEndModifier, VoteBeginningModifier, VoteModifier, DeathModifier, AbilityModifier
)
# Specific character imports are done lazily to avoid circular imports
# Re-export character registry
from .registry import CHARACTER_REGISTRY, str_to_class
# Make all character classes available directly from the characters module
# This provides the same interface as before but without listing all classes
from .registry import CHARACTER_REGISTRY as _registry
from .specific import (
    Amnesiac, Banshee, Voudon
)

# Import utility functions
globals().update(_registry)