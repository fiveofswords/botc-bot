from __future__ import annotations
from model.characters import Character

from typing import TYPE_CHECKING, Type

if TYPE_CHECKING:
    from bot import Player


class SeatingOrderModifier(Character):
    """ A character which modifies the seating order or seating order message"""

    def __init__(self, parent: Player):
        super().__init__(parent)

    def seating_order(self, seating_order: list[Player]):
        # returns a seating order after the character's modifications
        return seating_order

    def seating_order_message(self, seating_order: list[Player]):
        # returns a string to be added to the seating order message specifically (not just to the seating order)
        return ""


class DayStartModifier(Character):
    """A character which modifies the start of the day"""

    def __init__(self, parent: Player):
        super().__init__(parent)

    async def on_day_start(self, origin, kills: list[Player]) -> bool:
        # Called on the start of the day
        return True


class NomsCalledModifier(Character):
    """A character which modifies the start of the day"""

    def __init__(self, parent: Player):
        super().__init__(parent)

    def on_noms_called(self):
        # Called when nominations are called for the first time each day
        pass


class NominationModifier(Character):
    """A character which triggers on a nomination"""

    def __init__(self, parent: Player):
        super().__init__(parent)

    async def on_nomination(self, nominee: Player, nominator: Player, proceed: bool) -> bool:
        # Returns bool -- whether the nomination proceeds
        return proceed


class DayEndModifier(Character):
    """A character which modifies the start of the day"""

    def __init__(self, parent: Player):
        super().__init__(parent)

    def on_day_end(self):
        # Called on the end of the day
        pass


class VoteBeginningModifier(Character):
    """A character which modifies the value of players' votes"""

    def __init__(self, parent: Player):
        super().__init__(parent)

    def modify_vote_values(self, order: list[Player], values: dict[Player, tuple[int, int]], majority: float) \
            -> tuple[list[Player], dict[Player, tuple[int, int]], float]:
        # returns a list of the vote's order, a dictionary of vote values, and majority
        return order, values, majority


class VoteModifier(Character):
    """A character which modifies the effect of votes"""

    def __init__(self, parent: Player):
        super().__init__(parent)

    def on_vote_call(self, to_call: Player):
        # Called every time a player is called to vote
        pass

    def on_vote(self):
        # Called every time a player votes
        pass

    def on_vote_conclusion(self, dies: bool, tie: bool) -> tuple[bool, bool]:
        # returns boolean -- whether the nominee is about to die, whether the vote is tied
        return dies, tie


class DeathModifier(Character):
    """A character which triggers on a player's death"""
    PROTECTS_OTHERS = 1
    PROTECTS_SELF = 2
    KILLS_SELF = 3
    FORCES_KILL = 1000
    UNSET = 999

    def __init__(self, parent: Player):
        super().__init__(parent)

    def on_death(self, person: Player, dies: bool) -> bool:
        # Returns bool -- does person die
        return dies

    def on_death_priority(self):
        return DeathModifier.UNSET


class AbilityModifier(
    SeatingOrderModifier,
    DayStartModifier,
    NomsCalledModifier,
    NominationModifier,
    DayEndModifier,
    VoteBeginningModifier,
    VoteModifier,
    DeathModifier,
):
    """ A character which can have different abilities"""

    def __init__(self, parent: Player):
        super().__init__(parent)
        self.abilities = []

    def refresh(self):
        super().refresh()
        self.abilities = []

    def add_ability(self, role: Type[Character]):
        self.abilities.append(role(self.parent))

    def clear_ability(self):
        removed_ability = None
        for ability in self.abilities:
            if isinstance(ability, AbilityModifier):
                removed_ability = ability.clear_ability()
        if not removed_ability:
            if len(self.abilities):
                removed_ability = self.abilities.pop()
        return removed_ability

    def seating_order(self, seating_order: list[Player]):
        # returns a seating order after the character's modifications
        for role in self.abilities:
            if isinstance(role, SeatingOrderModifier):
                seating_order = role.seating_order(seating_order)
        return seating_order

    async def on_day_start(self, origin: Player, kills: list[Player]):
        # Called on the start of the day
        if not self.is_poisoned:
            for role in self.abilities:
                if isinstance(role, DayStartModifier):
                    await role.on_day_start(origin, kills)

        return True

    def poison(self):
        super().poison()
        for role in self.abilities:
            role.poison()

    def unpoison(self):
        super().unpoison()
        for role in self.abilities:
            role.unpoison()

    def on_noms_called(self):
        # Called when nominations are called for the first time each day
        if not self.is_poisoned:
            for role in self.abilities:
                if isinstance(role, NomsCalledModifier):
                    role.on_noms_called()

    async def on_nomination(self, nominee: Player, nominator: Player, proceed: bool):
        # Returns bool -- whether the nomination proceeds
        if not self.is_poisoned:
            for role in self.abilities:
                if isinstance(role, NominationModifier):
                    proceed = await role.on_nomination(nominee, nominator, proceed)
        return proceed

    def on_day_end(self):
        # Called on the end of the day
        if not self.is_poisoned:
            for role in self.abilities:
                if isinstance(role, DayEndModifier):
                    role.on_day_end()

    def modify_vote_values(self, order: list[Player], values: dict, majority: int):
        # returns a list of the vote's order, a dictionary of vote values, and majority
        if not self.is_poisoned:
            for role in self.abilities:
                if isinstance(role, VoteBeginningModifier):
                    order, values, majority = role.modify_vote_values(
                        order, values, majority
                    )
        return order, values, majority

    def on_vote_call(self, to_call: Player):
        # Called every time a player is called to vote
        if not self.is_poisoned:
            for role in self.abilities:
                if isinstance(role, VoteModifier):
                    role.on_vote_call(to_call)

    def on_vote(self):
        # Called every time a player votes
        if not self.is_poisoned:
            for role in self.abilities:
                if isinstance(role, VoteModifier):
                    role.on_vote()

    def on_vote_conclusion(self, dies: bool, tie: bool) -> tuple[bool, bool]:
        # returns boolean -- whether the nominee is about to die, whether the vote is tied
        if not self.is_poisoned:
            for role in self.abilities:
                if isinstance(role, VoteModifier):
                    dies, tie = role.on_vote_conclusion(dies, tie)
        return dies, tie

    def on_death(self, person: Player, dies: bool) -> bool:
        # Returns bool -- does person die
        if not self.is_poisoned:
            for role in self.abilities:
                if isinstance(role, DeathModifier):
                    dies = role.on_death(person, dies)
        return dies

    def on_death_priority(self) -> int:
        priority = DeathModifier.UNSET
        if not self.is_poisoned and not self.parent.isGhost:
            for role in self.abilities:
                if isinstance(role, DeathModifier):
                    priority = min(priority, role.on_death_priority())
        return priority
