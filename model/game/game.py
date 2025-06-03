import discord.errors

import global_vars
from bot_client import client
from model.characters import Storyteller, SeatingOrderModifier, DayStartModifier
from model.game.whisper_mode import WhisperMode
from model.player import Player, STORYTELLER_ALIGNMENT
from utils.game_utils import update_presence, remove_backup
from utils.message_utils import safe_send
from model.channels.channel_utils import reorder_channels

class Game:
    """Represents a game of Blood on the Clocktower.
    
    Attributes:
        days: List of days that have passed
        isDay: Whether it is currently day
        script: The script being used
        seatingOrder: The seating order of players
        whisper_mode: The current whisper mode
        seatingOrderMessage: The message with the seating order
        storytellers: List of storyteller players
        show_tally: Whether to show the whisper tally
        has_automated_life_and_death: Whether life and death is automated
    """

    def __init__(self, seating_order, seating_order_message, script, skip_storytellers=False):
        """Initialize a Game.
        
        Args:
            seating_order: The seating order of players
            seating_order_message: The message with the seating order
            script: The script being used
            skip_storytellers: Whether to skip adding storytellers
        """
        self.days = []
        self.isDay = False
        self.script = script
        self.seatingOrder = seating_order
        self.whisper_mode = WhisperMode.ALL
        self.seatingOrderMessage = seating_order_message
        self.storytellers = [
            Player(Storyteller, STORYTELLER_ALIGNMENT, person, st_channel=None, position=None)
            for person in global_vars.gamemaster_role.members
        ] if not skip_storytellers else []
        self.show_tally = False
        self.has_automated_life_and_death = False

    async def update_seating_order_message(self):
        """Updates the pinned seating order message with current hand status."""
        message_text = "**Seating Order:**"
        for person in self.seatingOrder:
            person_display_name = person.display_name
            if person.is_ghost:
                if person.dead_votes <= 0:
                    person_display_name = "~~" + person_display_name + "~~ X"
                else:
                    person_display_name = (
                        "~~" + person_display_name + "~~ " + "O" * person.dead_votes
                    )

            if person.hand_raised:
                person_display_name += " ✋"

            message_text += "\n{}".format(person_display_name)

            if isinstance(person.character, SeatingOrderModifier):
                message_text += person.character.seating_order_message(self.seatingOrder)

        if self.seatingOrderMessage:
            try:
                await self.seatingOrderMessage.edit(content=message_text)
            except discord.errors.NotFound:
                # The message might have been deleted, handle this case if necessary
                print(f"Warning: Seating order message (ID: {self.seatingOrderMessage.id}) not found. Could not update.")
            except Exception as e:
                print(f"Error updating seating order message: {e}")

    async def end(self, winner):
        """Ends the game.
        
        Args:
            winner: The winning team ('good', 'evil', or 'tie')
        """
        # remove roles
        for person in self.seatingOrder:
            await person.wipe_roles()

        # unpin messages
        try:
            for msg in await global_vars.channel.pins():
                if msg.created_at >= self.seatingOrderMessage.created_at:
                    await msg.unpin()

            if global_vars.whisper_channel:
                for msg in await global_vars.whisper_channel.pins():
                    await msg.unpin()
        except discord.errors.NotFound:
            pass
        except discord.errors.DiscordServerError:
            pass

        # announcement
        winner = winner.lower()
        await safe_send(
            global_vars.channel,
            f"{global_vars.player_role.mention}, {'The game is over.' if winner == 'tie' else f'{winner} has won.'} Good game!",
        )

        """
        # save backup
        i = 0
        while True:
            i += 1
            if not os.path.isfile('game_{}.pckl'.format(str(i))):
                break
        backup('game_{}.pckl'.format(str(i)))
        """

        # delete old backup
        remove_backup("current_game.pckl")

        # turn off
        global_vars.game = NULL_GAME
        await update_presence(client)

    async def reseat(self, new_seating_order):
        """Reseats the table.
        
        Args:
            new_seating_order: The new seating order
        """
        # Seating order
        self.seatingOrder = new_seating_order

        # Seating order message
        message_text = "**Seating Order:**"
        for index, person in enumerate(self.seatingOrder):

            if person.is_ghost:
                if person.dead_votes <= 0:
                    message_text += "\n{}".format("~~" + person.display_name + "~~ X")
                else:
                    message_text += "\n{}".format(
                        "~~" + person.display_name + "~~ " + "O" * person.dead_votes
                    )

            else:
                message_text += "\n{}".format(person.display_name)

            if isinstance(person.character, SeatingOrderModifier):
                message_text += person.character.seating_order_message(self.seatingOrder)

            person.position = index

        await self.seatingOrderMessage.edit(content=message_text)
        await reorder_channels([x.st_channel for x in self.seatingOrder])

    async def add_traveler(self, person):
        """Add a traveler to the game.
        
        Args:
            person: The traveler to add
        """
        self.seatingOrder.insert(person.position, person)
        await person.user.add_roles(global_vars.player_role, global_vars.traveler_role)
        await self.reseat(self.seatingOrder)
        await safe_send(
            global_vars.channel,
            "{} has joined the town as the {}.".format(
                person.display_name, person.character.role_name
            ),
        )

    async def remove_traveler(self, person):
        """Remove a traveler from the game.
        
        Args:
            person: The traveler to remove
        """
        self.seatingOrder.remove(person)
        await person.user.remove_roles(global_vars.player_role, global_vars.traveler_role)
        await self.reseat(self.seatingOrder)
        announcement = await safe_send(
            global_vars.channel, "{} has left the town.".format(person.display_name)
        )
        await announcement.pin()

    async def start_day(self, kills=None, origin=None):
        """Start the day phase.
        
        Args:
            kills: List of players to kill
            origin: The origin of the day start
        """
        if kills is None:
            kills = []

        for person in global_vars.game.seatingOrder:
            await person.morning()
            if isinstance(person.character, DayStartModifier):
                if not await person.character.on_day_start(origin, kills):
                    return

        deaths = [await person.kill() for person in kills]
        if deaths == [] and len(self.days) > 0:
            no_kills = await safe_send(global_vars.channel, "No one has died.")
            await no_kills.pin()
        await safe_send(
            global_vars.channel,
            "{}, wake up! Message the storytellers to set default votes for today.".format(
                global_vars.player_role.mention
            ),
        )

        self.days.append(Day())
        self.isDay = True

        if global_vars.whisper_channel:
            message = await safe_send(global_vars.whisper_channel, f"Start of day {len(self.days)}")
            await message.pin()

        await update_presence(client)


# Import at the end to avoid circular imports
from model.game.day import Day

# Create a null game to use as a placeholder
NULL_GAME = Game(seating_order=[], seating_order_message=0, script=[], skip_storytellers=True)
