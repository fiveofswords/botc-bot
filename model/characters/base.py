"""
Base character classes for Blood on the Clocktower game.
"""

import model

class Character:
    """A generic character."""

    parent: 'model.player.Player'
    role_name: str
    _is_poisoned: bool
    
    def __init__(self, parent):
        """Initialize a character.
        
        Args:
            parent: The player object this character belongs to
        """
        self.parent = parent
        self.role_name = "Character"
        self._is_poisoned = False
        self.refresh()

    def refresh(self):
        """Reset the character state."""
        pass

    def extra_info(self):
        """Get additional information about this character."""
        return ""

    @property
    def is_poisoned(self):
        """Check if the character is poisoned."""
        return self._is_poisoned

    def poison(self):
        """Poison the character."""
        self._is_poisoned = True

    def unpoison(self):
        """Remove poison from the character."""
        self._is_poisoned = False


class Townsfolk(Character):
    """A generic townsfolk."""

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Townsfolk"


class Outsider(Character):
    """A generic outsider."""

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Outsider"


class Minion(Character):
    """A generic minion."""

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Minion"


class Demon(Character):
    """A generic demon."""

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Demon"


class SeatingOrderModifier(Character):
    """A character which modifies the seating order or seating order message."""

    def __init__(self, parent):
        super().__init__(parent)

    def seating_order(self, seatingOrder):
        """Returns a seating order after the character's modifications."""
        return seatingOrder

    def seating_order_message(self, seatingOrder):
        """Returns a string to be added to the seating order message."""
        return ""


class DayStartModifier(Character):
    """A character which modifies the start of the day."""

    def __init__(self, parent):
        super().__init__(parent)

    async def on_day_start(self, origin, kills):
        """Called on the start of the day.
        
        Returns:
            bool: Whether to continue with the day start
        """
        return True


class NomsCalledModifier(Character):
    """A character which is affected when nominations are called."""

    def __init__(self, parent):
        super().__init__(parent)

    def on_noms_called(self):
        """Called when nominations are called for the first time each day."""
        pass


class NominationModifier(Character):
    """A character which triggers on a nomination."""

    def __init__(self, parent):
        super().__init__(parent)

    async def on_nomination(self, nominee, nominator, proceed):
        """Called when a nomination occurs.
        
        Returns:
            bool: Whether the nomination proceeds
        """
        return proceed


class DayEndModifier(Character):
    """A character which modifies the end of the day."""

    def __init__(self, parent):
        super().__init__(parent)

    def on_day_end(self):
        """Called on the end of the day."""
        pass


class VoteBeginningModifier(Character):
    """A character which modifies the value of players' votes."""

    def __init__(self, parent):
        super().__init__(parent)

    def modify_vote_values(self, order, values, majority):
        """Modify vote values.
        
        Returns:
            tuple: order, values, majority
        """
        return order, values, majority


class VoteModifier(Character):
    """A character which modifies the effect of votes."""

    def __init__(self, parent):
        super().__init__(parent)

    def on_vote_call(self, toCall):
        """Called every time a player is called to vote."""
        pass

    def on_vote(self):
        """Called every time a player votes."""
        pass

    def on_vote_conclusion(self, dies, tie):
        """Called at the conclusion of voting.
        
        Returns:
            tuple: Whether the nominee is about to die, whether the vote is tied
        """
        return dies, tie


class DeathModifier(Character):
    """A character which triggers on a player's death."""
    
    # Constants for death modifier priority
    PROTECTS_OTHERS = 1
    PROTECTS_SELF = 2
    KILLS_SELF = 3
    FORCES_KILL = 1000
    UNSET = 999

    def __init__(self, parent):
        super().__init__(parent)

    def on_death(self, person, dies):
        """Called when a player is killed.
        
        Returns:
            bool: Whether the player dies
        """
        return dies

    def on_death_priority(self):
        """Get the priority of this death modifier."""
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
    """A character which can have different abilities."""

    abilities: list[Character]

    def __init__(self, parent):
        super().__init__(parent)
        self.abilities = []

    def refresh(self):
        super().refresh()
        self.abilities = []

    def add_ability(self, role):
        """Add an ability to this character."""
        self.abilities.append(role(self.parent))

    def clear_ability(self):
        """Remove an ability from this character."""
        removed_ability = None
        for ability in self.abilities:
            if isinstance(ability, AbilityModifier):
                removed_ability = ability.clear_ability()
        if not removed_ability:
            if len(self.abilities):
                removed_ability = self.abilities.pop()
        return removed_ability

    def seating_order(self, seatingOrder):
        """Returns a seating order after the character's modifications."""
        for role in self.abilities:
            if isinstance(role, SeatingOrderModifier):
                seatingOrder = role.seating_order(seatingOrder)
        return seatingOrder

    async def on_day_start(self, origin, kills):
        """Called on the start of the day."""
        if not self.is_poisoned:
            for role in self.abilities:
                if isinstance(role, DayStartModifier):
                    await role.on_day_start(origin, kills)

        return True

    def poison(self):
        """Poison this character and all its abilities."""
        super().poison()
        for role in self.abilities:
            role.poison()

    def unpoison(self):
        """Remove poison from this character and all its abilities."""
        super().unpoison()
        for role in self.abilities:
            role.unpoison()

    def on_noms_called(self):
        """Called when nominations are called for the first time each day."""
        if not self.is_poisoned:
            for role in self.abilities:
                if isinstance(role, NomsCalledModifier):
                    role.on_noms_called()

    async def on_nomination(self, nominee, nominator, proceed):
        """Called when a nomination occurs."""
        if not self.is_poisoned:
            for role in self.abilities:
                if isinstance(role, NominationModifier):
                    proceed = await role.on_nomination(nominee, nominator, proceed)
        return proceed

    def on_day_end(self):
        """Called on the end of the day."""
        if not self.is_poisoned:
            for role in self.abilities:
                if isinstance(role, DayEndModifier):
                    role.on_day_end()

    def modify_vote_values(self, order, values, majority):
        """Modify vote values."""
        if not self.is_poisoned:
            for role in self.abilities:
                if isinstance(role, VoteBeginningModifier):
                    order, values, majority = role.modify_vote_values(
                        order, values, majority
                    )
        return order, values, majority

    def on_vote_call(self, toCall):
        """Called every time a player is called to vote."""
        if not self.is_poisoned:
            for role in self.abilities:
                if isinstance(role, VoteModifier):
                    role.on_vote_call(toCall)

    def on_vote(self):
        """Called every time a player votes."""
        if not self.is_poisoned:
            for role in self.abilities:
                if isinstance(role, VoteModifier):
                    role.on_vote()

    def on_vote_conclusion(self, dies, tie):
        """Called at the conclusion of voting."""
        if not self.is_poisoned:
            for role in self.abilities:
                if isinstance(role, VoteModifier):
                    dies, tie = role.on_vote_conclusion(dies, tie)
        return dies, tie

    def on_death(self, person, dies):
        """Called when a player is killed."""
        if not self.is_poisoned:
            for role in self.abilities:
                if isinstance(role, DeathModifier):
                    dies = role.on_death(person, dies)
        return dies

    def on_death_priority(self):
        """Get the priority of this death modifier."""
        priority = DeathModifier.UNSET
        if not self.is_poisoned and not self.parent.is_ghost:
            for role in self.abilities:
                if isinstance(role, DeathModifier):
                    priority = min(priority, role.on_death_priority())
        return priority


class Traveler(SeatingOrderModifier):
    """A generic traveler."""

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Traveler"

    def seating_order_message(self, seatingOrder):
        """Returns a string to add to the seating order message."""
        return f" - {self.role_name}"

    async def exile(self, person, user):
        """Exile this traveler."""
        import asyncio
        from global_vars import channel
        from bot_client import client
        from utils import message_utils

        msg = await message_utils.safe_send(user, "Do they die? yes or no")

        try:
            choice = await client.wait_for(
                "message",
                check=(lambda x: x.author == user and x.channel == msg.channel),
                timeout=200,
            )
        except asyncio.TimeoutError:
            await message_utils.safe_send(user, "Message timed out!")
            return

        # Cancel
        if choice.content.lower() == "cancel":
            await message_utils.safe_send(user, "Action cancelled!")
            return

        # Yes
        if choice.content.lower() == "yes" or choice.content.lower() == "y":
            die = True
        # No
        elif choice.content.lower() == "no" or choice.content.lower() == "n":
            die = False
        else:
            await message_utils.safe_send(
                user, "Your answer must be 'yes,' 'y,' 'no,' or 'n' exactly."
            )
            return

        if die:
            die = await person.kill(suppress=True)
            if die:
                announcement = await message_utils.safe_send(channel,
                                                             f"{person.user.mention} has been exiled, and dies.")
                await announcement.pin()
            else:
                if person.is_ghost:
                    await message_utils.safe_send(
                        channel,
                        f"{person.user.mention} has been exiled, but is already dead."
                    )
                else:
                    await message_utils.safe_send(
                        channel,
                        f"{person.user.mention} has been exiled, but does not die."
                    )
        else:
            if person.is_ghost:
                await message_utils.safe_send(
                    channel,
                    f"{person.user.mention} has been exiled, but is already dead."
                )
            else:
                await message_utils.safe_send(
                    channel,
                    f"{person.user.mention} has been exiled, but does not die."
                )
        from global_vars import traveler_role
        await person.user.add_roles(traveler_role)


class Storyteller(SeatingOrderModifier):
    """The storyteller."""

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Storyteller"

    def seating_order_message(self, seatingOrder):
        """Returns a string to add to the seating order message."""
        return f" - {self.role_name}"