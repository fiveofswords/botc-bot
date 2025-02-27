"""
Specific character classes for Blood on the Clocktower game.
"""

import asyncio
import itertools

import global_vars
from bot_client import client
from utils.message_utils import safe_send
from .base import (
    Townsfolk, Outsider, Minion, Demon, Traveler,
    DayStartModifier, NominationModifier,
    VoteBeginningModifier, DeathModifier, AbilityModifier,
    has_ability
)

# Basic Character Classes

class Chef(Townsfolk):
    """The chef."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Chef"


class Empath(Townsfolk):
    """The empath."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Empath"


class Investigator(Townsfolk):
    """The investigator."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Investigator"


class FortuneTeller(Townsfolk):
    """The fortune teller."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Fortune Teller"


class Librarian(Townsfolk):
    """The librarian."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Librarian"


class Mayor(Townsfolk):
    """The mayor."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Mayor"


class Monk(Townsfolk):
    """The monk."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Monk"


class Slayer(Townsfolk):
    """The slayer."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Slayer"


class Soldier(Townsfolk):
    """The soldier."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Soldier"


class Ravenkeeper(Townsfolk):
    """The ravenkeeper."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Ravenkeeper"


class Undertaker(Townsfolk):
    """The undertaker."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Undertaker"


class Washerwoman(Townsfolk):
    """The washerwoman."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Washerwoman"


class Virgin(Townsfolk, NominationModifier):
    """The virgin."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Virgin"
    
    def refresh(self):
        super().refresh()
        self.beenNominated = False
    
    async def on_nomination(self, nominee, nominator, proceed):
        if not global_vars.game.has_automated_life_and_death:
            return proceed
            
        # Returns bool -- whether the nomination proceeds
        if nominee == self.parent:
            if not self.beenNominated:
                self.beenNominated = True
                if isinstance(nominator.character, Townsfolk) and not self.is_poisoned:
                    if not nominator.is_ghost:
                        # fixme: nominator should be executed rather than killed
                        await nominator.kill()
        return proceed


class Chambermaid(Townsfolk):
    """The chambermaid."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Chambermaid"


class Exorcist(Townsfolk):
    """The exorcist."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Exorcist"


class Fool(Townsfolk, DeathModifier):
    """The fool."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Fool"
    
    def refresh(self):
        super().refresh()
        self.can_escape_death = True
    
    def on_death(self, person, dies):
        if self.parent == person and not self.is_poisoned and self.can_escape_death and dies:
            self.can_escape_death = False
            return False
        return dies
    
    def on_death_priority(self):
        return DeathModifier.PROTECTS_SELF
    
    def extra_info(self):
        if self.can_escape_death:
            return "Fool: Not Used"
        return "Fool: Used"


class Gambler(Townsfolk):
    """The gambler."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Gambler"


class Gossip(Townsfolk):
    """The gossip."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Gossip"


class Grandmother(Townsfolk):
    """The grandmother."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Grandmother"


class Innkeeper(Townsfolk):
    """The innkeeper."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Innkeeper"


class Minstrel(Townsfolk):
    """The minstrel."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Minstrel"


class Pacifist(Townsfolk):
    """The pacifist."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Pacifist"


class Professor(Townsfolk):
    """The professor."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Professor"


class Sailor(Townsfolk, DeathModifier):
    """The sailor."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Sailor"
    
    def on_death(self, person, dies):
        if self.parent == person and not self.is_poisoned:
            return False
        return dies
    
    def on_death_priority(self):
        return DeathModifier.PROTECTS_SELF


class TeaLady(Townsfolk, DeathModifier):
    """The tea lady."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Tea Lady"
    
    def on_death(self, person, dies):
        # look left for living neighbor
        if not dies:
            return dies
        player_count = len(global_vars.game.seatingOrder)
        ccw = self.parent.position - 1
        neighbor1 = global_vars.game.seatingOrder[ccw]
        while neighbor1.is_ghost:
            ccw = ccw - 1
            neighbor1 = global_vars.game.seatingOrder[ccw]
            
        # look right for living neighbor
        cw = self.parent.position + 1 - player_count
        neighbor2 = global_vars.game.seatingOrder[cw]
        while neighbor2.is_ghost:
            cw = cw + 1
            neighbor2 = global_vars.game.seatingOrder[cw]
            
        if (
            # fixme: This does not consider neighbors who may falsely register as good or evil (recluse/spy)
            neighbor1.alignment == "good"
            and neighbor2.alignment == "good"
            and (person == neighbor1 or person == neighbor2)
            and not self.is_poisoned
        ):
            return False
        return dies
    
    def on_death_priority(self):
        return DeathModifier.PROTECTS_OTHERS


class Artist(Townsfolk):
    """The artist."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Artist"


class Clockmaker(Townsfolk):
    """The clockmaker."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Clockmaker"


class Dreamer(Townsfolk):
    """The dreamer."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Dreamer"


class Flowergirl(Townsfolk):
    """The flowergirl."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Flowergirl"


class Juggler(Townsfolk):
    """The juggler."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Juggler"


class Mathematician(Townsfolk):
    """The mathematician."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Mathematician"


class Oracle(Townsfolk):
    """The oracle."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Oracle"


class Philosopher(Townsfolk, AbilityModifier):
    """The philosopher."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Philosopher"
    
    def refresh(self):
        super().refresh()
        self.abilities = []
    
    def add_ability(self, role):
        is_set = False
        for ability in self.abilities:
            if isinstance(ability, AbilityModifier):
                ability.add_ability(role)
                is_set = True
        if not is_set:
            self.abilities = [role(self.parent)]
    
    def extra_info(self):
        return "\n".join([("Philosophering: {}\n{}".format(x.role_name, x.extra_info())) for x in self.abilities])


class Sage(Townsfolk):
    """The sage."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Sage"


class Savant(Townsfolk):
    """The savant."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Savant"


class Seamstress(Townsfolk):
    """The seamstress."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Seamstress"


class SnakeCharmer(Townsfolk):
    """The snake charmer."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Snake Charmer"


class TownCrier(Townsfolk):
    """The town crier."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Town Crier"


class Courtier(Townsfolk):
    """The courtier."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Courtier"


# Outsiders

class Drunk(Outsider):
    """The drunk."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Drunk"


class Goon(Outsider):
    """The goon."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Goon"


class Butler(Outsider):
    """The butler."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Butler"


class Saint(Outsider):
    """The saint."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Saint"


class Recluse(Outsider):
    """The recluse."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Recluse"


class Moonchild(Outsider):
    """The moonchild."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Moonchild"


class Lunatic(Outsider):
    """The lunatic."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Lunatic"


class Tinker(Outsider):
    """The tinker."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Tinker"


class Barber(Outsider):
    """The barber."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Barber"


class Klutz(Outsider):
    """The klutz."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Klutz"


class Mutant(Outsider):
    """The mutant."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Mutant"


class Sweetheart(Outsider):
    """The sweetheart."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Sweetheart"


# Minions

class Godfather(Minion):
    """The godfather."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Godfather"


class Mastermind(Minion):
    """The mastermind."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Mastermind"


class Spy(Minion):
    """The spy."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Spy"


class Poisoner(Minion):
    """The poisoner."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Poisoner"


class ScarletWoman(Minion):
    """The scarlet woman."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Scarlet Woman"


class Baron(Minion):
    """The baron."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Baron"


class Assassin(Minion, DayStartModifier, DeathModifier):
    """The assassin."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Assassin"
    
    def refresh(self):
        super().refresh()
        self.target = None
    
    def extra_info(self):
        return "Assassinated: {}".format(self.target and self.target.display_name)
    
    async def on_day_start(self, origin, kills):
        if not global_vars.game.has_automated_life_and_death:
            return True
        if self.parent.is_ghost or self.target or len(global_vars.game.days) < 1:
            return True
        else:
            msg = await safe_send(origin, f"Does {self.parent.display_name} use Assassin ability?")
            try:
                choice = await client.wait_for(
                    "message",
                    check=(lambda x: x.author == origin and x.channel == msg.channel),
                    timeout=200)
                    
                # Cancel
                if choice.content.lower() == "cancel":
                    await safe_send(origin, "Action cancelled!")
                    return False
                    
                # Yes
                if choice.content.lower() == "yes" or choice.content.lower() == "y":
                    msg = await safe_send(origin, "Who is Assassinated?")
                    player_choice = await client.wait_for(
                        "message",
                        check=(lambda x: x.author == origin and x.channel == msg.channel),
                        timeout=200)
                    # Cancel
                    if player_choice.content.lower() == "cancel":
                        await safe_send(origin, "Action cancelled!")
                        return False
                        
                    from bot_impl import select_player
                    assassination_target = await select_player(origin, player_choice.content, global_vars.game.seatingOrder)
                    if assassination_target is None:
                        return False
                    self.target = assassination_target
                    
                    if assassination_target not in kills:
                        kills.append(assassination_target)
                    return True
                    
                # No
                elif choice.content.lower() == "no" or choice.content.lower() == "n":
                    return True
                else:
                    await safe_send(
                        origin, "Your answer must be 'yes,' 'y,' 'no,' or 'n' exactly."
                    )
                    return False
            except asyncio.TimeoutError:
                await safe_send(origin, "Message timed out!")
                return False
    
    def on_death(self, person, dies):
        if self.is_poisoned or self.parent.is_ghost:
            return dies
        if person == self.target:
            return True
        return dies
    
    def on_death_priority(self):
        return DeathModifier.FORCES_KILL


class DevilSAdvocate(Minion):
    """The devil's advocate."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Devil's Advocate"


class Witch(Minion, NominationModifier, DayStartModifier):
    """The witch."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Witch"
    
    def refresh(self):
        super().refresh()
        self.witched = None
    
    async def on_day_start(self, origin, kills):
        if not global_vars.game.has_automated_life_and_death:
            return True
            
        # todo: consider minions killed by vigormortis as active
        if self.parent.is_ghost == True or self.parent in kills:
            self.witched = None
            return True
            
        msg = await safe_send(origin, "Who is witched?")
        try:
            reply = await client.wait_for(
                "message",
                check=(lambda x: x.author == origin and x.channel == msg.channel),
                timeout=200,
            )
        except asyncio.TimeoutError:
            await safe_send(origin, "Timed out.")
            return False
            
        from bot_impl import select_player
        person = await select_player(origin, reply.content, global_vars.game.seatingOrder)
        if person is None:
            return False
            
        self.witched = person
        return True
    
    async def on_nomination(self, nominee, nominator, proceed):
        if not global_vars.game.has_automated_life_and_death:
            return proceed
            
        if (
            self.witched
            and self.witched == nominator
            and not self.witched.is_ghost
            and not self.parent.is_ghost
            and not self.is_poisoned
        ):
            await self.witched.kill()
        return proceed
    
    def extra_info(self):
        if self.witched:
            return f"Witched: {self.witched.display_name}"
        return ""


class EvilTwin(Minion):
    """The evil twin."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Evil Twin"


class Cerenovus(Minion):
    """The cerenovus."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Cerenovus"


class PitHag(Minion):
    """The pit-hag."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Pit-Hag"


class Vizier(Minion):
    """The vizier."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Vizier"


# Demons

class Vortox(Demon):
    """The vortox."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Vortox"


class FangGu(Demon):
    """The fang gu."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Fang Gu"


class Imp(Demon):
    """The imp."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Imp"


class Kazali(Demon):
    """The kazali."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Kazali"


class LordOfTyphon(Demon):
    """The lord of typhon."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Lord of Typhon"


class NoDashii(Demon):
    """The no dashii."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "No Dashii"


class Po(Demon):
    """The po."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Po"


class Pukka(Demon):
    """The pukka."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Pukka"


class Shabaloth(Demon):
    """The shabaloth."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Shabaloth"


class Vigormortis(Demon):
    """The vigormortis."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Vigormortis"


class Zombuul(Demon):
    """The zombuul."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Zombuul"


# Travelers

class Beggar(Traveler):
    """The beggar."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Beggar"


class Gunslinger(Traveler):
    """The gunslinger."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Gunslinger"


class Scapegoat(Traveler):
    """The scapegoat."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Scapegoat"


class Apprentice(Traveler, AbilityModifier):
    """The apprentice."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Apprentice"
    
    def refresh(self):
        super().refresh()
        self.abilities = []
    
    def add_ability(self, role):
        is_set = False
        for ability in self.abilities:
            if isinstance(ability, AbilityModifier):
                ability.add_ability(role)
                is_set = True
        if not is_set:
            self.abilities = [role(self.parent)]
    
    def extra_info(self):
        return "\n".join([("Apprenticing: {}\n{}".format(x.role_name, x.extra_info())) for x in self.abilities])


class Matron(Traveler, DayStartModifier):
    """The matron."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Matron"
    
    async def on_day_start(self, origin, kills):
        if self.parent.is_ghost or self.parent in kills:
            return True
        # If matron is alive, then only allow neighbor whispers
        from bot_impl import WhisperMode
        global_vars.game.whisper_mode = WhisperMode.NEIGHBORS
        return True


class Judge(Traveler):
    """The judge."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Judge"


class Voudon(Traveler):
    """The voudon."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Voudon"
        # todo: consider Voudon when taking away ghost votes


class Bishop(Traveler):
    """The bishop."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "bishop"


class Butcher(Traveler):
    """The butcher."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Butcher"


class BoneCollector(Traveler):
    """The bone collector."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Bone Collector"
        # todo: boneCollector makes a dead player regain their ability


class Harlot(Traveler):
    """The harlot."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Harlot"


class Barista(Traveler):
    """The barista."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Barista"


class Deviant(Traveler):
    """The deviant."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Deviant"


class Gangster(Traveler):
    """The gangster."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Gangster"


class Gnome(Traveler):
    """The gnome."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Gnome"


class Bureaucrat(Traveler, DayStartModifier, VoteBeginningModifier):
    """The bureaucrat."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Bureaucrat"
        self.target = None
    
    async def on_day_start(self, origin, kills):
        if self.is_poisoned or self.parent.is_ghost == True or self.parent in kills:
            self.target = None
            return True
            
        msg = await safe_send(origin, "Who is bureaucrated?")
        try:
            reply = await client.wait_for(
                "message",
                check=(lambda x: x.author == origin and x.channel == msg.channel),
                timeout=200,
            )
        except asyncio.TimeoutError:
            await safe_send(origin, "Timed out.")
            return
            
        from bot_impl import select_player
        person = await select_player(origin, reply.content, global_vars.game.seatingOrder)
        if person is None:
            return
            
        self.target = person
        return True
    
    def modify_vote_values(self, order, values, majority):
        if self.target and not self.is_poisoned and not self.parent.is_ghost:
            values[self.target] = (values[self.target][0], values[self.target][1] * 3)
            
        return order, values, majority


class Thief(Traveler, DayStartModifier, VoteBeginningModifier):
    """The thief."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Thief"
        self.target = None
    
    async def on_day_start(self, origin, kills):
        if self.parent.is_ghost == True or self.parent in kills:
            self.target = None
            return True
            
        msg = await safe_send(origin, "Who is thiefed?")
        try:
            reply = await client.wait_for(
                "message",
                check=(lambda x: x.author == origin and x.channel == msg.channel),
                timeout=200,
            )
        except asyncio.TimeoutError:
            await safe_send(origin, "Timed out.")
            return
            
        from bot_impl import select_player
        person = await select_player(origin, reply.content, global_vars.game.seatingOrder)
        if person is None:
            return
            
        self.target = person
        return True
    
    def modify_vote_values(self, order, values, majority):
        if self.target and not self.is_poisoned and not self.parent.is_ghost:
            values[self.target] = (values[self.target][0], values[self.target][1] * -1)
            
        return order, values, majority


# Special Character Classes

class Cannibal(Townsfolk, AbilityModifier):
    """The cannibal."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Cannibal"
    
    def add_ability(self, role):
        is_set = False
        for ability in self.abilities:
            if isinstance(ability, AbilityModifier):
                ability.add_ability(role)
                is_set = True
        if not is_set:
            self.abilities = [role(self.parent)]
    
    def extra_info(self):
        return "\n".join([("Eaten: {}\n{}".format(x.role_name, x.extra_info())) for x in self.abilities])


class Balloonist(Townsfolk):
    """The balloonist."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Balloonist"


class Fisherman(Townsfolk):
    """The fisherman."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Fisherman"


class Widow(Minion):
    """The widow."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Widow"


class Goblin(Minion):
    """The goblin."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Goblin"


class Leviathan(Demon):
    """The leviathan."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Leviathan"


class Amnesiac(Townsfolk, AbilityModifier):
    """The amnesiac."""
    
    def __init__(self, parent):
        super().__init__(parent)
        #      initialize the AbilityModifier aspect as well
        self.role_name = "Amnesiac"
        self.vote_mod = 1
        self.player_with_votes = None
    
    def add_ability(self, role):
        is_set = False
        for ability in self.abilities:
            if isinstance(ability, AbilityModifier):
                ability.add_ability(role)
                is_set = True
        if not is_set:
            self.abilities = [role(self.parent)]
    
    def extra_info(self):
        base_info = super().extra_info()
        if self.player_with_votes and self.vote_mod != 1:
            # add to base_info
            base_info = base_info + f"\n{self.player_with_votes.display_name} votes times {self.vote_mod}"
        for ability in self.abilities:
            info = ability.extra_info()
            base_info += f"\nHas Ability: {ability.role_name}"
            if info:
                base_info = base_info + f"\n{info}"
        return base_info.strip()
    
    def modify_vote_values(self, order, values, majority):
        if self.player_with_votes and not self.is_poisoned and not self.parent.is_ghost:
            values[self.player_with_votes] = (values[self.player_with_votes][0], values[self.player_with_votes][1] * self.vote_mod)
            
        return order, values, majority
    
    def enhance_votes(self, player, multiplier):
        self.player_with_votes = player
        self.vote_mod = multiplier
    
    def on_day_end(self):
        self.vote_mod = 1
        self.player_with_votes = None
        super().on_day_end()


class BountyHunter(Townsfolk):
    """The bounty hunter."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Bounty Hunter"


class Lycanthrope(Townsfolk):
    """The lycanthrope."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Lycanthrope"


class CultLeader(Townsfolk):
    """The cult leader."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Cult Leader"


class General(Townsfolk):
    """The general."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "General"


class Pixie(Townsfolk, AbilityModifier):
    """The pixie."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Pixie"
    
    def add_ability(self, role):
        is_set = False
        for ability in self.abilities:
            if isinstance(ability, AbilityModifier):
                ability.add_ability(role)
                is_set = True
        if not is_set:
            self.abilities = [role(self.parent)]
    
    def extra_info(self):
        return "" if self.abilities == [] else f"Has Ability {self.abilities[0].role_name}"


class Acrobat(Outsider):
    """The acrobat."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Acrobat"


class LilMonsta(Demon):
    """The lil' monsta."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Lil' Monsta"


class Politician(Outsider):
    """The politician."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Politician"


class Preacher(Townsfolk):
    """The preacher."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Preacher"


class Noble(Townsfolk):
    """The noble."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Noble"


class Farmer(Townsfolk):
    """The farmer."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Farmer"


class PoppyGrower(Townsfolk):
    """The poppy grower."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Poppy Grower"


class Nightwatchman(Townsfolk):
    """The nightwatchman."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Nightwatchman"


class Atheist(Townsfolk):
    """The atheist."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Atheist"


class Huntsman(Townsfolk):
    """The huntsman."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Huntsman"


class Alchemist(Townsfolk, AbilityModifier):
    """The alchemist."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Alchemist"
    
    def extra_info(self):
        return "\n".join([("Alchemy: {}\n{}".format(x.role_name, x.extra_info())) for x in self.abilities])
    
    def add_ability(self, role):
        is_set = False
        for ability in self.abilities:
            if isinstance(ability, AbilityModifier):
                ability.add_ability(role)
                is_set = True
        if not is_set:
            self.abilities = [role(self.parent)]


class Choirboy(Townsfolk):
    """The choirboy."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Choirboy"


class Engineer(Townsfolk):
    """The engineer."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Engineer"


class King(Townsfolk):
    """The king."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "King"


class Magician(Townsfolk):
    """The magician."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Magician"


class HighPriestess(Townsfolk):
    """The high priestess."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "High Priestess"


class Steward(Townsfolk):
    """The steward."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Steward"


class Knight(Townsfolk):
    """The knight."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Knight"


class Shugenja(Townsfolk):
    """The shugenja."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Shugenja"


class VillageIdiot(Townsfolk):
    """The village idiot."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Village Idiot"


# Special effect characters

# FIXME: this is probably gonna be obnoxious...
# noinspection SpellCheckingInspection
BANSHEE_SCREAM = """
 ```
 AAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
 AAaaaaaaaAAAAAAAAAAAAAAAAAAAAA
 AAa THE aAAAAAAAAAAAAAAAAAAAAA
 AAaaaaaaaAAAAAAAAAAAAAAAAAAAAA
 AAAAAAAAaaaaaaaaaaaaAAAAAAAAAA
 AAAAAAAAAa BANSHEE aAAAAAAAAAA
 AAAAAAAAAaaaaaaaaaaaAAAAAAAAAA
 AAAAAAAAAAAAAAAAAAAaaaaaaaaaAA
 AAAAAAAAAAAAAAAAAAAa WAKES aAA
 AAAAAAAAAAAAAAAAAAAaaaaaaaaaAA
 AAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
 ```"""


class Banshee(Townsfolk, DayStartModifier):
    """The banshee."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Banshee"
        self.is_screaming = False
        self.remaining_nominations = 2
    
    def refresh(self):
        super().refresh()
        self.is_screaming = False
    
    async def on_day_start(self, origin, kills):
        if self.is_screaming:
            self.remaining_nominations = 2
            return True
            
        #  check if kills includes me
        if self.parent not in kills:
            return True
        if self.is_poisoned:
            return True
            
        msg = await safe_send(origin, f"Was Banshee {self.parent.display_name} killed by the demon?")
        try:
            choice = await client.wait_for(
                "message",
                check=(lambda x: x.author == origin and x.channel == msg.channel),
                timeout=200)
                
            # Cancel
            if choice.content.lower() == "cancel":
                await safe_send(origin, "Action cancelled!")
                return False
                
            # Yes
            if choice.content.lower() == "yes" or choice.content.lower() == "y":
                self.is_screaming = True
                self.remaining_nominations = 2
                scream = await safe_send(global_vars.channel, BANSHEE_SCREAM)
                await scream.pin()
                return True
            # No
            elif choice.content.lower() == "no" or choice.content.lower() == "n":
                return True
            else:
                await safe_send(
                    origin, "Your answer must be 'yes,' 'y,' 'no,' or 'n' exactly. Day start cancelled!"
                )
                return False
        except asyncio.TimeoutError:
            await safe_send(origin, "Message timed out!")
            return False
    
    def extra_info(self):
        return "Banshee: Has Ability" if self.is_screaming else super().extra_info()


class Alsaahir(Townsfolk):
    """The alsaahir."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Alsaahir"


class Golem(Outsider, NominationModifier):
    """The golem."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Golem"
    
    def refresh(self):
        super().refresh()
        self.hasNominated = False
    
    async def on_nomination(self, nominee, nominator, proceed):
        if not global_vars.game.has_automated_life_and_death:
            return proceed
            
        # fixme: golem instantly kills a recluse when it should be ST decision
        if nominator == self.parent:
            if (
                not isinstance(nominee.character, Demon)
                and not self.is_poisoned
                and not self.parent.is_ghost
                and not self.hasNominated
            ):
                await nominee.kill()
            self.hasNominated = True
        return proceed


class Damsel(Outsider):
    """The damsel."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Damsel"


class Heretic(Outsider):
    """The heretic."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Heretic"


class Puzzlemaster(Outsider):
    """The puzzlemaster."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Puzzlemaster"


class Snitch(Outsider):
    """The snitch."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Snitch"


class PlagueDoctor(Outsider):
    """The plague doctor."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Plague Doctor"


class Hatter(Outsider):
    """The hatter."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Hatter"


class Ogre(Outsider):
    """The ogre."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Ogre"


class Zealot(Outsider):
    """The zealot."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Zealot"


class Marionette(Minion):
    """The marionette."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Marionette"


class OrganGrinder(Minion, NominationModifier):
    """The organ grinder."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Organ Grinder"
    
    async def on_nomination(self, nominee, nominator, proceed):
        if not self.is_poisoned and not self.parent.is_ghost:
            nominee_display_name = nominator.display_name if nominator else "the storytellers"
            nominator_mention = nominee.user.mention if nominee else "the storytellers"
            announcement = await safe_send(
                global_vars.channel,
                f"{global_vars.player_role.mention}, {nominator_mention} has been nominated by {nominee_display_name}. Organ Grinder is in play. Message your votes to the storytellers."
            )
            await announcement.pin()
            this_day = global_vars.game.days[-1]
            this_day.votes[-1].announcements.append(announcement.id)
            message_tally = {
                X: 0 for X in itertools.combinations(global_vars.game.seatingOrder, 2)
            }
            
            has_had_multiple_votes = len(this_day.votes) > 1
            last_vote_message = None if not has_had_multiple_votes else await global_vars.channel.fetch_message(
                this_day.votes[-2].announcements[0])
            for person in global_vars.game.seatingOrder:
                for msg in person.message_history:
                    if msg["from_player"] == person:
                        if has_had_multiple_votes:
                            if msg["time"] >= last_vote_message.created_at:
                                if (person, msg["to_player"]) in message_tally:
                                    message_tally[(person, msg["to_player"])] += 1
                                elif (msg["to_player"], person) in message_tally:
                                    message_tally[(msg["to_player"], person)] += 1
                                else:
                                    message_tally[(person, msg["to_player"])] = 1
                        else:
                            if msg["day"] == len(global_vars.game.days):
                                if (person, msg["to_player"]) in message_tally:
                                    message_tally[(person, msg["to_player"])] += 1
                                elif (msg["to_player"], person) in message_tally:
                                    message_tally[(msg["to_player"], person)] += 1
                                else:
                                    message_tally[(person, msg["to_player"])] = 1
            sorted_tally = sorted(message_tally.items(), key=lambda x: -x[1])
            messageText = "**Message Tally:**"
            for pair in sorted_tally:
                if pair[1] > 0:
                    messageText += "\n> {person1} - {person2}: {n}".format(
                        person1=pair[0][0].display_name, person2=pair[0][1].display_name, n=pair[1]
                    )
                else:
                    messageText += "\n> All other pairs: 0"
                    break
            await safe_send(global_vars.channel, messageText)
            return False
        return proceed


class Mezepheles(Minion):
    """The mezepheles."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Mezepheles"


class Harpy(Minion):
    """The harpy."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Harpy"


# techically this should be an ability modifier on the demon in play, but having the additional ability be provided by the boffin is cleaner implementation
class Boffin(Minion, AbilityModifier):
    """The boffin."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Boffin"
    
    def extra_info(self):
        return "\n".join([("Boffin'd: {}\n{}".format(x.role_name, x.extra_info())) for x in self.abilities]).strip()


class Xaan(Minion):
    """The Xaan."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Xaan"


class Wizard(Minion):
    """The Wizard."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Wizard"


class AlHadikhia(Demon):
    """The al-hadikhia."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Al-Hadikhia"


class Legion(Demon):
    """The legion."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Legion"


class Lleech(Demon, DeathModifier, DayStartModifier):
    """The lleech."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Lleech"
    
    def refresh(self):
        super().refresh()
        self.hosted = None
    
    async def on_day_start(self, origin, kills):
        if not global_vars.game.has_automated_life_and_death:
            return True
        if self.hosted or self.parent.is_ghost:
            return True
            
        msg = await safe_send(origin, "Who is hosted by the Lleech?")
        try:
            reply = await client.wait_for(
                "message",
                check=(lambda x: x.author == origin and x.channel == msg.channel),
                timeout=200,
            )
        except asyncio.TimeoutError:
            await safe_send(origin, "Timed out.")
            return False
            
        from bot_impl import select_player
        person = await select_player(origin, reply.content, global_vars.game.seatingOrder)
        if person is None:
            return False
            
        self.hosted = person
        return True
    
    def on_death(self, person, dies):
        # todo: if the host has died, the lleech should also die
        if self.parent == person and not self.is_poisoned:
            if not (self.hosted and self.hosted.is_ghost):
                return False
        return dies
    
    def on_death_priority(self):
        return DeathModifier.KILLS_SELF
    
    def extra_info(self):
        if self.hosted:
            return "Leech Host: " + self.hosted.display_name
        else:
            return ""


class Ojo(Demon):
    """The ojo."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Ojo"


class Riot(Demon, NominationModifier):
    """The riot."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Riot"
    
    async def on_nomination(self, nominee, nominator, proceed):
        if not global_vars.game.has_automated_life_and_death:
            return proceed
        if self.is_poisoned or self.parent.is_ghost or not nominee:
            return proceed
            
        nominee_nick = nominator.display_name if nominator else "the storytellers"
        announcemnt = await safe_send(
            global_vars.channel,
            "{}, {} has been nominated by {}."
            .format(global_vars.player_role.mention, nominee.user.mention, nominee_nick),
        )
        await announcemnt.pin()
        this_day = global_vars.game.days[-1]
        this_day.votes[-1].announcements.append(announcemnt.id)
        
        if not this_day.riot_active:
            # show tally on first nomination
            import itertools
            message_tally = {
                X: 0 for X in itertools.combinations(global_vars.game.seatingOrder, 2)
            }
            for person in global_vars.game.seatingOrder:
                for msg in person.message_history:
                    if msg["from_player"] == person:
                        if msg["day"] == len(global_vars.game.days):
                            if (person, msg["to_player"]) in message_tally:
                                message_tally[(person, msg["to_player"])] += 1
                            elif (msg["to_player"], person) in message_tally:
                                message_tally[(msg["to_player"], person)] += 1
                            else:
                                message_tally[(person, msg["to_player"])] = 1
            sorted_tally = sorted(message_tally.items(), key=lambda x: -x[1])
            messageText = "**Message Tally:**"
            for pair in sorted_tally:
                if pair[1] > 0:
                    messageText += "\n> {person1} - {person2}: {n}".format(
                        person1=pair[0][0].display_name, person2=pair[0][1].display_name, n=pair[1]
                    )
                else:
                    messageText += "\n> All other pairs: 0"
                    break
            await safe_send(global_vars.channel, messageText)
            
        this_day.riot_active = True
        
        # handle the soldier jinx - If Riot nominates the Soldier, the Soldier does not die
        soldier_jinx = nominator and nominee and not nominee.character.is_poisoned and has_ability(nominator.character, Riot) and has_ability(nominee.character, Soldier)
        golem_jinx = nominator and nominee and not nominator.character.is_poisoned and not nominator.is_ghost and has_ability(nominee.character, Riot) and has_ability(nominator.character, Golem)
        if not (nominator):
            if this_day.st_riot_kill_override:
                this_day.st_riot_kill_override = False
                await nominee.kill()
        elif not (soldier_jinx or golem_jinx):
            await nominee.kill()
            
        riot_announcement = f"Riot is in play. {nominee.user.mention} to nominate"
        if len(global_vars.game.days) < 3:
            riot_announcement = riot_announcement + " or skip"
            
        if nominator:
            nominator.riot_nominee = False
        else:
            # no players should be the most recent riot_nominee, so iterate all
            for p in global_vars.game.seatingOrder:
                p.riot_nominee = False
        if nominee:
            nominee.riot_nominee = True
            nominee.can_nominate = True
            
        msg = await safe_send(
            global_vars.channel,
            riot_announcement,
        )
        
        await this_day.open_noms()
        return False


class Yaggababble(Demon):
    """The yaggababble."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Yaggababble"


class Boomdandy(Minion):
    """The boomdandy."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Boomdandy"


class Fearmonger(Minion):
    """The fearmonger."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Fearmonger"


class Psychopath(Minion):
    """The psychopath."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Psychopath"


class Summoner(Minion):
    """The summoner."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Summoner"