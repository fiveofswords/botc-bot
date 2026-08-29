"""
Specific character classes for Blood on the Clocktower game.
"""

import asyncio
import itertools

import bot_client
import global_vars
import utils.character_utils
import utils.message_utils
from utils import has_ability
from . import base


# Basic Character Classes

class Chef(base.Townsfolk):
    """The chef."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Chef"


class Empath(base.Townsfolk):
    """The empath."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Empath"


class Investigator(base.Townsfolk):
    """The investigator."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Investigator"


class FortuneTeller(base.Townsfolk):
    """The fortune teller."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Fortune Teller"


class Librarian(base.Townsfolk):
    """The librarian."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Librarian"


class Mayor(base.Townsfolk):
    """The mayor."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Mayor"


class Monk(base.Townsfolk):
    """The monk."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Monk"


class Slayer(base.Townsfolk):
    """The slayer."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Slayer"


class Soldier(base.Townsfolk):
    """The soldier."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Soldier"


class Ravenkeeper(base.Townsfolk):
    """The ravenkeeper."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Ravenkeeper"


class Undertaker(base.Townsfolk):
    """The undertaker."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Undertaker"


class Washerwoman(base.Townsfolk):
    """The washerwoman."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Washerwoman"


class Virgin(base.Townsfolk, base.NominationModifier):
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
                if isinstance(nominator.character, base.Townsfolk) and not self.is_poisoned:
                    if not nominator.is_ghost:
                        # fixme: nominator should be executed rather than killed
                        await nominator.kill()
        return proceed


class Chambermaid(base.Townsfolk):
    """The chambermaid."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Chambermaid"


class Exorcist(base.Townsfolk):
    """The exorcist."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Exorcist"


class Fool(base.Townsfolk, base.DeathModifier):
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
        return base.DeathModifier.PROTECTS_SELF
    
    def extra_info(self):
        if self.can_escape_death:
            return "Fool: Not Used"
        return "Fool: Used"


class Gambler(base.Townsfolk):
    """The gambler."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Gambler"


class Gossip(base.Townsfolk):
    """The gossip."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Gossip"


class Grandmother(base.Townsfolk):
    """The grandmother."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Grandmother"


class Innkeeper(base.Townsfolk):
    """The innkeeper."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Innkeeper"


class Minstrel(base.Townsfolk):
    """The minstrel."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Minstrel"


class Pacifist(base.Townsfolk):
    """The pacifist."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Pacifist"


class Professor(base.Townsfolk):
    """The professor."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Professor"


class Sailor(base.Townsfolk, base.DeathModifier):
    """The sailor."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Sailor"
    
    def on_death(self, person, dies):
        if self.parent == person and not self.is_poisoned:
            return False
        return dies
    
    def on_death_priority(self):
        return base.DeathModifier.PROTECTS_SELF


class TeaLady(base.Townsfolk, base.DeathModifier):
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
        return base.DeathModifier.PROTECTS_OTHERS


class Artist(base.Townsfolk):
    """The artist."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Artist"


class Clockmaker(base.Townsfolk):
    """The clockmaker."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Clockmaker"


class Dreamer(base.Townsfolk):
    """The dreamer."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Dreamer"


class Flowergirl(base.Townsfolk):
    """The flowergirl."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Flowergirl"


class Juggler(base.Townsfolk):
    """The juggler."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Juggler"


class Mathematician(base.Townsfolk):
    """The mathematician."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Mathematician"


class Oracle(base.Townsfolk):
    """The oracle."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Oracle"


class Philosopher(base.Townsfolk, base.AbilityModifier):
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
            if isinstance(ability, base.AbilityModifier):
                ability.add_ability(role)
                is_set = True
        if not is_set:
            self.abilities = [role(self.parent)]
    
    def extra_info(self):
        return "\n".join([("Philosophering: {}\n{}".format(x.role_name, x.extra_info())) for x in self.abilities])


class Sage(base.Townsfolk):
    """The sage."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Sage"


class Savant(base.Townsfolk):
    """The savant."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Savant"


class Seamstress(base.Townsfolk):
    """The seamstress."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Seamstress"


class SnakeCharmer(base.Townsfolk):
    """The snake charmer."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Snake Charmer"


class TownCrier(base.Townsfolk):
    """The town crier."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Town Crier"


class Courtier(base.Townsfolk):
    """The courtier."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Courtier"


# Outsiders

class Drunk(base.Outsider):
    """The drunk."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Drunk"


class Goon(base.Outsider):
    """The goon."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Goon"


class Butler(base.Outsider):
    """The butler."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Butler"


class Saint(base.Outsider):
    """The saint."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Saint"


class Recluse(base.Outsider):
    """The recluse."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Recluse"


class Moonchild(base.Outsider):
    """The moonchild."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Moonchild"


class Lunatic(base.Outsider):
    """The lunatic."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Lunatic"


class Tinker(base.Outsider):
    """The tinker."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Tinker"


class Barber(base.Outsider):
    """The barber."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Barber"


class Klutz(base.Outsider):
    """The klutz."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Klutz"


class Mutant(base.Outsider):
    """The mutant."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Mutant"


class Sweetheart(base.Outsider):
    """The sweetheart."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Sweetheart"


# Minions

class Godfather(base.Minion):
    """The godfather."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Godfather"


class Mastermind(base.Minion):
    """The mastermind."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Mastermind"


class Spy(base.Minion):
    """The spy."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Spy"


class Poisoner(base.Minion):
    """The poisoner."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Poisoner"


class ScarletWoman(base.Minion):
    """The scarlet woman."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Scarlet Woman"


class Baron(base.Minion):
    """The baron."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Baron"


class Assassin(base.Minion, base.DayStartModifier, base.DeathModifier):
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
            msg = await utils.message_utils.safe_send(origin, f"Does {self.parent.display_name} use Assassin ability?")
            try:
                choice = await bot_client.client.wait_for(
                    "message",
                    check=(lambda x: x.author == origin and x.channel == msg.channel),
                    timeout=200)
                    
                # Cancel
                if choice.content.lower() == "cancel":
                    await utils.message_utils.safe_send(origin, "Action cancelled!")
                    return False
                    
                # Yes
                if choice.content.lower() == "yes" or choice.content.lower() == "y":
                    msg = await utils.message_utils.safe_send(origin, "Who is Assassinated?")
                    player_choice = await bot_client.client.wait_for(
                        "message",
                        check=(lambda x: x.author == origin and x.channel == msg.channel),
                        timeout=200)
                    # Cancel
                    if player_choice.content.lower() == "cancel":
                        await utils.message_utils.safe_send(origin, "Action cancelled!")
                        return False
                        
                    from utils.player_utils import select_player
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
                    await utils.message_utils.safe_send(
                        origin, "Your answer must be 'yes,' 'y,' 'no,' or 'n' exactly."
                    )
                    return False
            except asyncio.TimeoutError:
                await utils.message_utils.safe_send(origin, "Message timed out!")
                return False
    
    def on_death(self, person, dies):
        if self.is_poisoned or self.parent.is_ghost:
            return dies
        if person == self.target:
            return True
        return dies
    
    def on_death_priority(self):
        return base.DeathModifier.FORCES_KILL


class DevilSAdvocate(base.Minion):
    """The devil's advocate."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Devil's Advocate"


class Witch(base.Minion, base.NominationModifier, base.DayStartModifier):
    """The witch."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Witch"
        self.witched = None
    
    def refresh(self):
        super().refresh()
        self.witched = None
    
    async def on_day_start(self, origin, kills):
        self.witched = None
        if not global_vars.game.has_automated_life_and_death:
            return True

        # todo: consider minions killed by vigormortis as active
        if self.parent.is_ghost == True or self.parent in kills:
            self.witched = None
            return True

        people_alive = len([p for p in global_vars.game.seatingOrder if not p.is_ghost and p not in kills])
        inquiry_to_storyteller = "Who is witched?" if people_alive > 3 else "Who is witched? (Will not affect anything if there are no longer at least 4 alive.)"
        msg = await utils.message_utils.safe_send(origin, inquiry_to_storyteller)
        try:
            reply = await bot_client.client.wait_for(
                "message",
                check=(lambda x: x.author == origin and x.channel == msg.channel),
                timeout=200,
            )
        except asyncio.TimeoutError:
            await utils.message_utils.safe_send(origin, "Timed out.")
            return False
            
        from utils.player_utils import select_player
        person = await select_player(origin, reply.content, global_vars.game.seatingOrder)
        if person is None:
            return False
            
        self.witched = person
        return True
    
    async def on_nomination(self, nominee, nominator, proceed):
        if not global_vars.game.has_automated_life_and_death:
            return proceed

        # if there are less than four players alive, the witch does not kill
        alive_players = [p for p in global_vars.game.seatingOrder if not p.is_ghost]
        if len(alive_players) < 4:
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


class EvilTwin(base.Minion):
    """The evil twin."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Evil Twin"


class Cerenovus(base.Minion):
    """The cerenovus."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Cerenovus"


class PitHag(base.Minion):
    """The pit-hag."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Pit-Hag"


class Vizier(base.Minion):
    """The vizier."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Vizier"


# Demons

class Vortox(base.Demon):
    """The vortox."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Vortox"


class FangGu(base.Demon):
    """The fang gu."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Fang Gu"


class Imp(base.Demon):
    """The imp."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Imp"


class Kazali(base.Demon):
    """The kazali."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Kazali"


class LordOfTyphon(base.Demon):
    """The lord of typhon."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Lord of Typhon"


class NoDashii(base.Demon):
    """The no dashii."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "No Dashii"


class Po(base.Demon):
    """The po."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Po"


class Pukka(base.Demon):
    """The pukka."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Pukka"


class Shabaloth(base.Demon):
    """The shabaloth."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Shabaloth"


class Vigormortis(base.Demon):
    """The vigormortis."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Vigormortis"


class Zombuul(base.Demon):
    """The zombuul."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Zombuul"


# Travelers

class Beggar(base.Traveler):
    """The beggar."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Beggar"


class Gunslinger(base.Traveler):
    """The gunslinger."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Gunslinger"


class Scapegoat(base.Traveler):
    """The scapegoat."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Scapegoat"


class Apprentice(base.Traveler, base.AbilityModifier):
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
            if isinstance(ability, base.AbilityModifier):
                ability.add_ability(role)
                is_set = True
        if not is_set:
            self.abilities = [role(self.parent)]
    
    def extra_info(self):
        return "\n".join([("Apprenticing: {}\n{}".format(x.role_name, x.extra_info())) for x in self.abilities])


class Matron(base.Traveler, base.DayStartModifier):
    """The matron."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Matron"
    
    async def on_day_start(self, origin, kills):
        if self.parent.is_ghost or self.parent in kills:
            return True
        # If matron is alive, then only allow neighbor whispers
        from model.game import WhisperMode
        global_vars.game.whisper_mode = WhisperMode.NEIGHBORS
        return True


class Judge(base.Traveler):
    """The judge."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Judge"


class Voudon(base.Traveler):
    """The voudon."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Voudon"
        # todo: consider Voudon when taking away ghost votes


class Bishop(base.Traveler):
    """The bishop."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "bishop"


class Butcher(base.Traveler):
    """The butcher."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Butcher"


class BoneCollector(base.Traveler):
    """The bone collector."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Bone Collector"
        # todo: boneCollector makes a dead player regain their ability


class Harlot(base.Traveler):
    """The harlot."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Harlot"


class Barista(base.Traveler):
    """The barista."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Barista"


class Deviant(base.Traveler):
    """The deviant."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Deviant"


class Gangster(base.Traveler):
    """The gangster."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Gangster"


class Gnome(base.Traveler):
    """The gnome."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Gnome"


class Cacklejack(base.Traveler):
    """The Cacklejack."""

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Cacklejack"


class Bureaucrat(base.Traveler, base.DayStartModifier, base.VoteBeginningModifier):
    """The bureaucrat."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Bureaucrat"
        self.target = None
    
    async def on_day_start(self, origin, kills):
        if self.is_poisoned or self.parent.is_ghost == True or self.parent in kills:
            self.target = None
            return True

        msg = await utils.message_utils.safe_send(origin, "Who is bureaucrated?")
        try:
            reply = await bot_client.client.wait_for(
                "message",
                check=(lambda x: x.author == origin and x.channel == msg.channel),
                timeout=200,
            )
        except asyncio.TimeoutError:
            await utils.message_utils.safe_send(origin, "Timed out.")
            return
            
        from utils.player_utils import select_player
        person = await select_player(origin, reply.content, global_vars.game.seatingOrder)
        if person is None:
            return
            
        self.target = person
        return True
    
    def modify_vote_values(self, order, values, majority):
        if self.target and not self.is_poisoned and not self.parent.is_ghost:
            values[self.target] = (values[self.target][0], values[self.target][1] * 3)
            
        return order, values, majority


class Thief(base.Traveler, base.DayStartModifier, base.VoteBeginningModifier):
    """The thief."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Thief"
        self.target = None
    
    async def on_day_start(self, origin, kills):
        if self.parent.is_ghost == True or self.parent in kills:
            self.target = None
            return True

        msg = await utils.message_utils.safe_send(origin, "Who is thiefed?")
        try:
            reply = await bot_client.client.wait_for(
                "message",
                check=(lambda x: x.author == origin and x.channel == msg.channel),
                timeout=200,
            )
        except asyncio.TimeoutError:
            await utils.message_utils.safe_send(origin, "Timed out.")
            return
            
        from utils.player_utils import select_player
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

class Cannibal(base.Townsfolk, base.AbilityModifier):
    """The cannibal."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Cannibal"
    
    def add_ability(self, role):
        is_set = False
        for ability in self.abilities:
            if isinstance(ability, base.AbilityModifier):
                ability.add_ability(role)
                is_set = True
        if not is_set:
            self.abilities = [role(self.parent)]
    
    def extra_info(self):
        return "\n".join([("Eaten: {}\n{}".format(x.role_name, x.extra_info())) for x in self.abilities])


class Balloonist(base.Townsfolk):
    """The balloonist."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Balloonist"


class Fisherman(base.Townsfolk):
    """The fisherman."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Fisherman"


class Widow(base.Minion):
    """The widow."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Widow"


class Goblin(base.Minion):
    """The goblin."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Goblin"


class Leviathan(base.Demon):
    """The leviathan."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Leviathan"


class Amnesiac(base.Townsfolk, base.AbilityModifier):
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
            if isinstance(ability, base.AbilityModifier):
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


class BountyHunter(base.Townsfolk):
    """The bounty hunter."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Bounty Hunter"


class Lycanthrope(base.Townsfolk):
    """The lycanthrope."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Lycanthrope"


class CultLeader(base.Townsfolk):
    """The cult leader."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Cult Leader"


class General(base.Townsfolk):
    """The general."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "General"


class Pixie(base.Townsfolk, base.AbilityModifier):
    """The pixie."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Pixie"
    
    def add_ability(self, role):
        is_set = False
        for ability in self.abilities:
            if isinstance(ability, base.AbilityModifier):
                ability.add_ability(role)
                is_set = True
        if not is_set:
            self.abilities = [role(self.parent)]
    
    def extra_info(self):
        return "" if self.abilities == [] else f"Has Ability {self.abilities[0].role_name}"


class Acrobat(base.Outsider):
    """The acrobat."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Acrobat"


class LilMonsta(base.Demon):
    """The lil' monsta."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Lil' Monsta"


class Politician(base.Outsider):
    """The politician."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Politician"


class Preacher(base.Townsfolk):
    """The preacher."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Preacher"


class Noble(base.Townsfolk):
    """The noble."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Noble"


class Farmer(base.Townsfolk):
    """The farmer."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Farmer"


class PoppyGrower(base.Townsfolk):
    """The poppy grower."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Poppy Grower"


class Nightwatchman(base.Townsfolk):
    """The nightwatchman."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Nightwatchman"


class Atheist(base.Townsfolk, base.DayStartModifier):
    """The atheist."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Atheist"

    async def on_day_start(self, origin, kills):
        # message storytellers if there is an atheist set but the game is not set to allow st nominations.
        if not global_vars.game.is_atheist:
            await utils.message_utils.notify_storytellers("An atheist is in play. Use the `setatheist true` command to allow nominations on storytellers.")
        return await super().on_day_start(origin, kills)


class Huntsman(base.Townsfolk):
    """The huntsman."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Huntsman"


class Alchemist(base.Townsfolk, base.AbilityModifier):
    """The alchemist."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Alchemist"
    
    def extra_info(self):
        return "\n".join([("Alchemy: {}\n{}".format(x.role_name, x.extra_info())) for x in self.abilities])
    
    def add_ability(self, role):
        is_set = False
        for ability in self.abilities:
            if isinstance(ability, base.AbilityModifier):
                ability.add_ability(role)
                is_set = True
        if not is_set:
            self.abilities = [role(self.parent)]


class Choirboy(base.Townsfolk):
    """The choirboy."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Choirboy"


class Engineer(base.Townsfolk):
    """The engineer."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Engineer"


class King(base.Townsfolk):
    """The king."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "King"


class Magician(base.Townsfolk):
    """The magician."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Magician"


class HighPriestess(base.Townsfolk):
    """The high priestess."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "High Priestess"


class Steward(base.Townsfolk):
    """The steward."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Steward"


class Knight(base.Townsfolk):
    """The knight."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Knight"


class Shugenja(base.Townsfolk):
    """The shugenja."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Shugenja"


class VillageIdiot(base.Townsfolk):
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


class Banshee(base.Townsfolk, base.DayStartModifier):
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

        msg = await utils.message_utils.safe_send(origin,
                                                  f"Was Banshee {self.parent.display_name} killed by the demon?")
        try:
            choice = await bot_client.client.wait_for(
                "message",
                check=(lambda x: x.author == origin and x.channel == msg.channel),
                timeout=200)
                
            # Cancel
            if choice.content.lower() == "cancel":
                await utils.message_utils.safe_send(origin, "Action cancelled!")
                return False
                
            # Yes
            if choice.content.lower() == "yes" or choice.content.lower() == "y":
                self.is_screaming = True
                self.remaining_nominations = 2
                scream = await utils.message_utils.safe_send(global_vars.channel, BANSHEE_SCREAM)
                await scream.pin()
                return True
            # No
            elif choice.content.lower() == "no" or choice.content.lower() == "n":
                return True
            else:
                await utils.message_utils.safe_send(
                    origin, "Your answer must be 'yes,' 'y,' 'no,' or 'n' exactly. Day start cancelled!"
                )
                return False
        except asyncio.TimeoutError:
            await utils.message_utils.safe_send(origin, "Message timed out!")
            return False
    
    def extra_info(self):
        return "Banshee: Has Ability" if self.is_screaming else super().extra_info()


class Alsaahir(base.Townsfolk):
    """The alsaahir."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Alsaahir"


class Princess(base.Townsfolk):
    """The princess."""

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Princess"
        self.hasNominated = False


class Golem(base.Outsider, base.NominationModifier):
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
                    not isinstance(nominee.character, base.Demon)
                and not self.is_poisoned
                and not self.parent.is_ghost
                and not self.hasNominated
            ):
                await nominee.kill()
            self.hasNominated = True
        return proceed


class Damsel(base.Outsider):
    """The damsel."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Damsel"


class Heretic(base.Outsider):
    """The heretic."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Heretic"


class Puzzlemaster(base.Outsider):
    """The puzzlemaster."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Puzzlemaster"


class Snitch(base.Outsider):
    """The snitch."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Snitch"


class PlagueDoctor(base.Outsider):
    """The plague doctor."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Plague Doctor"


class Hatter(base.Outsider):
    """The hatter."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Hatter"


class Ogre(base.Outsider):
    """The ogre."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Ogre"


class Zealot(base.Outsider):
    """The zealot."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Zealot"


class Hermit(base.Outsider, base.AbilityModifier):
    """The hermit."""

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Hermit"

    def extra_info(self):
        # list the extra info for each ability
        base_info = super().extra_info()
        for ability in self.abilities:
            info = ability.extra_info()
            base_info += f"\nHas Ability: {ability.role_name}"
            if info:
                base_info = base_info + f"\n{info}"
        return base_info.strip()


class Marionette(base.Minion):
    """The marionette."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Marionette"


class OrganGrinder(base.Minion, base.NominationModifier):
    """The organ grinder."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Organ Grinder"
    
    async def on_nomination(self, nominee, nominator, proceed):
        if not self.is_poisoned and not self.parent.is_ghost:
            nominee_display_name = nominator.display_name if nominator else "the storytellers"
            nominator_mention = nominee.user.mention if nominee else "the storytellers"
            announcement = await utils.message_utils.safe_send(
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
            await utils.message_utils.safe_send(global_vars.channel, messageText)
            return False
        return proceed


class Mezepheles(base.Minion):
    """The mezepheles."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Mezepheles"


class Harpy(base.Minion):
    """The harpy."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Harpy"


# techically this should be an ability modifier on the demon in play, but having the additional ability be provided by the boffin is cleaner implementation
class Boffin(base.Minion, base.AbilityModifier):
    """The boffin."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Boffin"
    
    def extra_info(self):
        return "\n".join([("Boffin'd: {}\n{}".format(x.role_name, x.extra_info())) for x in self.abilities]).strip()


class Xaan(base.Minion):
    """The Xaan."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Xaan"


class Wizard(base.Minion):
    """The Wizard."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Wizard"


class AlHadikhia(base.Demon):
    """The al-hadikhia."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Al-Hadikhia"


class Legion(base.Demon):
    """The legion."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Legion"


class Lleech(base.Demon, base.DeathModifier, base.DayStartModifier):
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

        msg = await utils.message_utils.safe_send(origin, "Who is hosted by the Lleech?")
        try:
            reply = await bot_client.client.wait_for(
                "message",
                check=(lambda x: x.author == origin and x.channel == msg.channel),
                timeout=200,
            )
        except asyncio.TimeoutError:
            await utils.message_utils.safe_send(origin, "Timed out.")
            return False
            
        from utils.player_utils import select_player
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
        return base.DeathModifier.KILLS_SELF
    
    def extra_info(self):
        if self.hosted:
            return "Leech Host: " + self.hosted.display_name
        else:
            return ""


class Ojo(base.Demon):
    """The ojo."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Ojo"


class Riot(base.Demon, base.NominationModifier, base.DayStartModifier):
    """The riot."""
    
    # Shared Riot notification state across all Riot instances.
    __notification_sent = {
        "day": None,
        "automate": False,
        "minion": False,
        "poisoned": False,
    }

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Riot"

    @classmethod
    def _get_notification_state(cls, current_day_number):
        defaults = {
            "day": None,
            "automate": False,
            "minion": False,
            "poisoned": False,
        }
        for key, value in defaults.items():
            cls.__notification_sent.setdefault(key, value)

        if cls.__notification_sent["day"] != current_day_number:
            cls.__notification_sent = {
                "day": current_day_number,
                "automate": False,
                "minion": False,
                "poisoned": False,
            }
        return cls.__notification_sent

    async def on_day_start(self, origin, kills):
        current_day_number = len(global_vars.game.days) + 1
        notification_state = Riot._get_notification_state(current_day_number)

        bot_client.logger.debug(
            "riot.day_start automated=%s day=%s poisoned=%s riot_ghost=%s",
            global_vars.game.has_automated_life_and_death,
            current_day_number,
            self.is_poisoned,
            self.parent.is_ghost,
        )
        if not global_vars.game.has_automated_life_and_death:
            # if there is a riot alive on day 3 and the game does not have automated life and death, prompt sts to set it.
            if current_day_number >= 3 and not self.parent.is_ghost and not notification_state["automate"]:
                await utils.message_utils.safe_send(origin, "A Riot is in play. Use the `automatekills true` command to enable Riot chaining")
                notification_state["automate"] = True

            bot_client.logger.debug("riot.day_start decision=skip reason=automation_disabled")
            return True

        # Check if there's a minion in the game
        has_minion = any(isinstance(player.character, base.Minion) for player in global_vars.game.seatingOrder)

        bot_client.logger.debug(
            "riot.day_start minion_check has_minion=%s notification_sent=%s",
            has_minion,
            Riot._get_notification_state(current_day_number)
        )
        if current_day_number >= 3 and not notification_state["minion"] and has_minion:
            bot_client.logger.debug(
                "riot.day_start decision=notify_storytellers day=%s",
                current_day_number,
            )

            # Send minion update reminder regardless of Riot's state
            # (even if poisoned or ghost, storytellers need to update minions)
            if not notification_state["minion"]:
                await utils.safe_send(origin, f"Riot is active on day {current_day_number}!\nPlease update all minion characters to Riot at the appropriate time{'.' if (current_day_number == 3) else '?'}")
                notification_state["minion"] = True

        # Only if ALL living players with Riot abilities are poisoned should this message be sent.
        # If every living Riot is poisoned, don't chain (storytellers handle the decision)
        living_riots = [
            player for player in global_vars.game.seatingOrder
            if has_ability(player.character, Riot)
               and not player.is_ghost
        ]
        if living_riots and all(riot_player.character.is_poisoned for riot_player in living_riots):
            bot_client.logger.debug("riot.day_start decision=non_chaining reason=all_riots_poisoned")
            if not notification_state["poisoned"]:
                await utils.message_utils.safe_send(origin, "All living Riot players are currently poisoned. Use the `unpoison` command if appropriate.")
                notification_state["poisoned"] = True
            return True

        # If Riot is a ghost, don't chain
        if self.parent.is_ghost:
            bot_client.logger.debug("riot.day_start decision=non_chaining reason=riot_dead")
            return True

        bot_client.logger.debug("riot.day_start decision=ready")
        return True

    async def on_nomination(self, nominee, nominator, proceed):
        assert global_vars.game is not None
        nominee_name = nominee.display_name if nominee else "storytellers"
        nominator_name = nominator.display_name if nominator else "storytellers"
        nomination_source = "storyteller" if nominator is None else "player"
        current_day_number = len(global_vars.game.days)
        eligible_riots = [
            player for player in global_vars.game.seatingOrder
            if player.character.role_name == "Riot"
            if not player.character.is_poisoned
            if not player.is_ghost
        ]
        eligible_riot_count = len(eligible_riots)
        bot_client.logger.debug(
            "riot.nomination start proceed=%s nominee=%s nominator=%s automated=%s poisoned=%s riot_ghost=%s",
            proceed,
            nominee_name,
            nominator_name,
            global_vars.game.has_automated_life_and_death,
            self.is_poisoned,
            self.parent.is_ghost,
        )
        bot_client.logger.debug(
            "riot.nomination eligibility source=%s day=%s eligible_riot_count=%s",
            nomination_source,
            current_day_number,
            eligible_riot_count,
        )
        if not global_vars.game.has_automated_life_and_death:
            bot_client.logger.debug("riot.nomination decision=pass_through reason=automation_disabled")
            return proceed

        if not nominee:
            bot_client.logger.debug(
                "riot.nomination decision=pass_through reason=storyteller_nominee source=%s day=%s eligible_riot_count=%s",
                nomination_source,
                current_day_number,
                eligible_riot_count,
            )
            return proceed

        this_day = global_vars.game.days[-1]

        # Days 1-2: Regular nominations, no riot behavior
        if current_day_number < 3:
            bot_client.logger.debug(
                "riot.nomination decision=pass_through reason=pre_day3 day=%s source=%s eligible_riot_count=%s",
                current_day_number,
                nomination_source,
                eligible_riot_count,
            )
            return proceed

        if eligible_riot_count < 1:
            bot_client.logger.debug(
                "riot.nomination decision=pass_through reason=no_eligible_riot day=%s source=%s",
                current_day_number,
                nomination_source,
            )
            return proceed

        bot_client.logger.debug(
            "riot.nomination decision=chain reason=eligible_riot_present day=%s source=%s eligible_riot_count=%s",
            current_day_number,
            nomination_source,
            eligible_riot_count,
        )
        
        # Day 3: Riot chaining behavior
        nominee_nick = nominator.display_name if nominator else "the storytellers"
        announcement = await utils.message_utils.safe_send(
            global_vars.channel,
            "{}, {} has been nominated by {}."
            .format(global_vars.player_role.mention, nominee.user.mention, nominee_nick),
        )
        if announcement:
            await announcement.pin()
            this_day.votes[-1].announcements.append(announcement.id)
        else:
            bot_client.logger.warning("announcent to pin not received!")
        bot_client.logger.debug(
            "riot.nomination announce nominee=%s nominator=%s announcement_id=%s",
            nominee_name,
            nominator_name,
            announcement.id if announcement else None,
        )
        
        if not this_day.riot_active and global_vars.game.show_tally:
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
            await utils.message_utils.safe_send(global_vars.channel, messageText)
            
        this_day.riot_active = True
        bot_client.logger.debug(
            "riot.nomination riot_chain_activated day=%s source=%s eligible_riot_count=%s",
            current_day_number,
            nomination_source,
            eligible_riot_count,
        )
        
        # REMOVED: Old soldier_jinx and golem_jinx logic
        # Soldier jinx is handled by storyteller intervention (they stop the game and announce good wins)
        # Golem jinx is removed entirely per clarifications
        # TODO: Future work - Golem smash should apply BEFORE Riot execute (sequencing issue)

        # Kill the nominee (all nominees die during Riot chaining)
        did_kill = False
        if not nominator:
            if this_day.st_riot_kill_override:
                this_day.st_riot_kill_override = False
                bot_client.logger.debug("riot.nomination kill decision=execute_by_st_override nominee=%s", nominee_name)
                did_kill = await nominee.kill()
            else:
                bot_client.logger.debug("riot.nomination kill decision=spare_by_st_override nominee=%s", nominee_name)
        else:
            # Riots always kill their nominees
            bot_client.logger.debug("riot.nomination kill decision=execute nominee=%s", nominee_name)
            did_kill = await nominee.kill()

        if did_kill:
            living_players = [player for player in global_vars.game.seatingOrder if not player.is_ghost]
            if len(living_players) <= 2:
                await utils.message_utils.safe_send(
                    global_vars.channel,
                    "The game is over! Please wait for the storytellers to conclude the game.",
                )
                return False

        riot_announcement = f"Riot is in play. {nominee.user.mention} to nominate"
        
        if nominator:
            nominator.riot_nominee = False
        else:
            # no players should be the most recent riot_nominee, so iterate all
            for p in global_vars.game.seatingOrder:
                p.riot_nominee = False
        if nominee:
            nominee.riot_nominee = True
            nominee.can_nominate = True
            bot_client.logger.debug(
                "riot.nomination next_nominator nominee=%s can_nominate=%s",
                nominee_name,
                nominee.can_nominate,
            )

        msg = await utils.message_utils.safe_send(
            global_vars.channel,
            riot_announcement,
        )
        bot_client.logger.debug("riot.nomination prompt_sent message_id=%s", msg.id if msg else None)
        
        await this_day.open_noms()
        bot_client.logger.debug(
            "riot.nomination decision=intercept proceed=False source=%s",
            nomination_source,
        )
        return False


class Yaggababble(base.Demon):
    """The yaggababble."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Yaggababble"


class Boomdandy(base.Minion):
    """The boomdandy."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Boomdandy"


class Fearmonger(base.Minion):
    """The fearmonger."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Fearmonger"


class Psychopath(base.Minion):
    """The psychopath."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Psychopath"


class Summoner(base.Minion):
    """The summoner."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Summoner"


class Wraith(base.Minion):
    """The wraith."""

    def __init__(self, parent):
        super().__init__(parent)
        self.role_name = "Wraith"

