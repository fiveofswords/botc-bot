"""
Player class for Blood on the Clocktower game.
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any, Dict, Optional, TypedDict

import discord
from discord import Member, TextChannel

import global_vars
from bot_client import client, logger
from model.channels import ChannelManager

# Constants
STORYTELLER_ALIGNMENT = "neutral"


class MessageDict(TypedDict):
    """Type definition for message history entries."""
    from_player: 'Player'
    to_player: 'Player'
    content: str
    day: int
    time: datetime
    jump: str


class Player:
    """Stores information about a player in the game."""

    def __init__(
            self,
            character_class: type,
            alignment: str,
            user: Member,
            st_channel: Optional[TextChannel],
            position: Optional[int]):
        """Initialize a Player.
        
        Args:
            character_class: The class of character this player has
            alignment: The alignment of the player (e.g., "good", "evil")
            user: The Discord member object for the player
            st_channel: The storyteller channel for this player
            position: The position of the player in the seating order
        """
        self.character = character_class(self)
        self.alignment = alignment
        self.user = user  # Discord member object for the player
        self.st_channel = st_channel  # Storyteller channel for this player
        self.name = user.name  # Discord username
        self.display_name = user.display_name  # Display name with nickname if applicable
        self.position = position  # Position in the seating order
        self.is_ghost = False  # Is the player dead?
        self.dead_votes = 0 # Number of dead votes the player has.
        self.is_active = False  # Has the player spoken today?
        self.is_inactive = False  # Is the player marked inactive by STs?
        self.can_nominate = True  # Can the player nominate?
        self.can_be_nominated = True  # Can the player be nominated?
        self.has_skipped = False  # Has the player skipped their nomination?
        self.has_checked_in = False  # Has the player checked in?
        self.message_history = []
        self.riot_nominee = False
        self.last_active = datetime.now().timestamp() # Timestamp of last activity
        self.hand_raised = False
        self.hand_locked_for_vote = False

        if global_vars.inactive_role in self.user.roles:
            self.is_inactive = True

    def __getstate__(self) -> Dict[str, Any]:
        """Prepare the object for pickling."""
        state = self.__dict__.copy()
        state["user"] = self.user.id
        state["st_channel"] = self.st_channel.id if self.st_channel else None
        return state

    def __setstate__(self, state: Dict[str, Any]) -> None:
        """Restore the object after unpickling."""
        self.__dict__.update(state)
        self.user = global_vars.server.get_member(state["user"])
        self.st_channel = global_vars.server.get_channel(state["st_channel"]) if state["st_channel"] else None

    async def morning(self) -> None:
        """Reset player state for the morning."""
        if global_vars.inactive_role in self.user.roles:
            self.is_inactive = True
        else:
            self.is_inactive = False
        self.can_nominate = not self.is_ghost
        self.can_be_nominated = True
        self.is_active = self.is_inactive
        self.has_skipped = self.is_inactive
        self.has_checked_in = self.is_inactive
        self.riot_nominee = False
        self.hand_raised = False
        self.hand_locked_for_vote = False

    async def kill(self, suppress: bool = False, force: bool = False) -> bool:
        """Kill the player.
        
        Args:
            suppress: Whether to suppress death announcement
            force: Whether to force the kill even if death modifiers would prevent it
            
        Returns:
            Whether the player dies
        """
        from utils.message_utils import safe_send

        dies = True
        if global_vars.game.has_automated_life_and_death:
            on_death_characters = sorted(
                [person.character for person in global_vars.game.seatingOrder
                 if hasattr(person.character, 'on_death')],
                key=lambda c: c.on_death_priority() if hasattr(c, 'on_death_priority') else 0
            )
            for player_character in on_death_characters:
                dies = player_character.on_death(self, dies)

        if not dies and not force:
            return dies

        self.is_ghost = True
        self.dead_votes = 1

        if not suppress:
            announcement = await safe_send(
                global_vars.channel, "{} has died.".format(self.user.mention)
            )
            await announcement.pin()

        await self.user.add_roles(global_vars.ghost_role, global_vars.dead_vote_role)
        if self.st_channel:
            await ChannelManager(client).set_ghost(self.st_channel.id)
        else:
        #     inform storytellers that the player is dead, but that the st channel has not been updated to reflect that
            for user in global_vars.gamemaster_role.members:
                await safe_send(
                    user,
                    f"{self.user.mention} has died, but the ST channel could not be updated to reflect that."
                )
        await global_vars.game.reseat(global_vars.game.seatingOrder)

        return dies

    async def execute(self, user: Member, force: bool = False) -> None:
        """Execute the player.
        
        Args:
            user: The user executing the player
            force: Whether to force the kill
        """
        from utils.message_utils import safe_send

        msg = await safe_send(user, "Do they die? yes or no")

        try:
            choice = await client.wait_for(
                "message",
                check=(lambda x: x.author == user and x.channel == msg.channel),
                timeout=200,
            )
        except asyncio.TimeoutError:
            await safe_send(user, "Message timed out!")
            return

        # Cancel
        if choice.content.lower() == "cancel":
            await safe_send(user, "Action cancelled!")
            return

        # Yes or No
        if choice.content.lower() in ["yes", "y"]:
            die = True
        elif choice.content.lower() in ["no", "n"]:
            die = False
        else:
            await safe_send(
                user, "Your answer must be 'yes,' 'y,' 'no,' or 'n' exactly."
            )
            return

        msg = await safe_send(user, "Does the day end? yes or no")

        try:
            choice = await client.wait_for(
                "message",
                check=(lambda x: x.author == user and x.channel == msg.channel),
                timeout=200,
            )
        except asyncio.TimeoutError:
            await safe_send(user, "Message timed out!")
            return

        # Cancel
        if choice.content.lower() == "cancel":
            await safe_send(user, "Action cancelled!")
            return

        # Yes or No
        if choice.content.lower() in ["yes", "y"]:
            end = True
        elif choice.content.lower() in ["no", "n"]:
            end = False
        else:
            await safe_send(
                user, "Your answer must be 'yes,' 'y,' 'no,' or 'n' exactly."
            )
            return

        # Handle the execution
        if die:
            die = await self.kill(suppress=True, force=force)
            if die:
                announcement = await safe_send(
                    global_vars.channel, "{} has been executed, and dies.".format(self.user.mention)
                )
                await announcement.pin()
            else:
                if self.is_ghost:
                    await safe_send(
                        global_vars.channel,
                        "{} has been executed, but is already dead.".format(
                            self.user.mention
                        ),
                    )
                else:
                    await safe_send(
                        global_vars.channel,
                        "{} has been executed, but does not die.".format(
                            self.user.mention
                        ),
                    )
        else:
            if self.is_ghost:
                await safe_send(
                    global_vars.channel,
                    "{} has been executed, but is already dead.".format(
                        self.user.mention
                    ),
                )
            else:
                await safe_send(
                    global_vars.channel,
                    "{} has been executed, but does not die.".format(self.user.mention),
                )

        global_vars.game.days[-1].isExecutionToday = True

        if end and global_vars.game.isDay:
            await global_vars.game.days[-1].end()

    async def revive(self) -> None:
        """Revive the player."""
        from utils.message_utils import safe_send

        self.is_ghost = False
        self.dead_votes = 0

        announcement = await safe_send(
            global_vars.channel, "{} has come back to life.".format(self.user.mention)
        )
        await announcement.pin()

        self.character.refresh()
        await self.user.remove_roles(global_vars.ghost_role, global_vars.dead_vote_role)
        if self.st_channel:
            await ChannelManager(client).remove_ghost(self.st_channel.id)
        else:
            # Inform storytellers that the player is dead, but that the st channel has not been updated to reflect that
            for user in global_vars.gamemaster_role.members:
                await safe_send(
                    user,
                    f"{self.user.mention} has come back to life, but the ST channel could not be updated to reflect that."
                )
        await global_vars.game.reseat(global_vars.game.seatingOrder)

    async def change_character(self, character_class: type) -> None:
        """Change the player's character.
        
        Args:
            character_class: The new character class
        """
        self.character = character_class(self)
        await global_vars.game.reseat(global_vars.game.seatingOrder)

    async def change_alignment(self, alignment: str) -> None:
        """Change the player's alignment.
        
        Args:
            alignment: The new alignment
        """
        self.alignment = alignment

    async def message(self, from_player: 'Player', content: str, jump: str) -> None:
        """Send a message to this player.
        
        Args:
            from_player: The player sending the message
            content: The message content
            jump: The jump URL to the original message
        """
        from utils.message_utils import safe_send

        try:
            message = await safe_send(
                self.user,
                f"Message from {from_player.display_name}: **{content}**"
            )
        except discord.errors.HTTPException as e:
            await safe_send(
                from_player.user,
                f"Something went wrong with your message to {self.display_name}! Please try again"
            )
            logger.info(
                f"could not send message to {self.display_name}; "
                f"it is {len(content)} characters long; error {e.text}"
            )
            return

        # Create message records
        message_to: MessageDict = {
            "from_player": from_player,
            "to_player": self,
            "content": content,
            "day": len(global_vars.game.days),
            "time": message.created_at,
            "jump": message.jump_url,
        }

        message_from: MessageDict = {
            "from_player": from_player,
            "to_player": self,
            "content": content,
            "day": len(global_vars.game.days),
            "time": message.created_at,
            "jump": jump,
        }

        self.message_history.append(message_to)
        from_player.message_history.append(message_from)

        # Send to storytellers
        if global_vars.whisper_channel:
            await safe_send(
                global_vars.whisper_channel,
                f"Message from {from_player.display_name} to {self.display_name}: **{content}**"
            )
        else:
            for user in global_vars.gamemaster_role.members:
                if user != self.user:
                    await safe_send(
                        user,
                        f"**[**{from_player.display_name} **>** {self.display_name}**]** {content}"
                    )

        await safe_send(from_player.user, "Message sent!")

    async def make_inactive(self) -> None:
        """Mark the player as inactive."""
        from utils.message_utils import safe_send

        self.is_inactive = True
        await self.user.add_roles(global_vars.inactive_role)
        self.has_skipped = True
        self.is_active = True
        self.has_checked_in = True

        if global_vars.game.isDay:
            # Notify storytellers about active players
            not_active = [
                player
                for player in global_vars.game.seatingOrder
                if not player.is_active and player.alignment != STORYTELLER_ALIGNMENT
            ]

            if len(not_active) == 1:
                for memb in global_vars.gamemaster_role.members:
                    await safe_send(
                        memb, f"Just waiting on {not_active[0].display_name} to speak."
                    )
            elif len(not_active) == 0:
                for memb in global_vars.gamemaster_role.members:
                    await safe_send(memb, "Everyone has spoken!")

            # Notify storytellers about nominations
            can_nominate = [
                player
                for player in global_vars.game.seatingOrder
                if player.can_nominate
                   and not player.has_skipped
                   and player.alignment != STORYTELLER_ALIGNMENT
                   and not player.is_ghost
            ]

            if len(can_nominate) == 1:
                for memb in global_vars.gamemaster_role.members:
                    await safe_send(
                        memb,
                        f"Just waiting on {can_nominate[0].display_name} to nominate or skip."
                    )
            elif len(can_nominate) == 0:
                for memb in global_vars.gamemaster_role.members:
                    await safe_send(memb, "Everyone has nominated or skipped!")
        else:
            # Night phase
            from utils.player_utils import check_and_print_if_one_or_zero_to_check_in
            await check_and_print_if_one_or_zero_to_check_in()

    async def undo_inactive(self) -> None:
        """Remove the inactive status from the player."""
        self.is_inactive = False
        await self.user.remove_roles(global_vars.inactive_role)
        self.has_skipped = False
        self.has_checked_in = False

    def update_last_active(self) -> None:
        """Update the timestamp of the player's last activity."""
        self.last_active = datetime.now().timestamp()

    async def add_dead_vote(self) -> None:
        """Add a dead vote to the player."""
        if self.dead_votes == 0:
            await self.user.add_roles(global_vars.dead_vote_role)
        self.dead_votes += 1
        await global_vars.game.reseat(global_vars.game.seatingOrder)

    async def remove_dead_vote(self) -> None:
        """Remove a dead vote from the player."""
        if self.dead_votes == 1:
            await self.user.remove_roles(global_vars.dead_vote_role)
        self.dead_votes -= 1
        await global_vars.game.reseat(global_vars.game.seatingOrder)

    async def wipe_roles(self) -> None:
        """Remove all game-related roles from the player."""
        try:
            await self.user.remove_roles(
                global_vars.traveler_role,
                global_vars.ghost_role,
                global_vars.dead_vote_role
            )
        except discord.HTTPException as e:
            # Cannot remove role from user who doesn't exist on the server
            logger.info("could not remove roles for %s: %s", self.display_name, e.text)
