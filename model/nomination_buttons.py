from __future__ import annotations

import discord

import bot_client
import global_vars
from model import game, player
from utils import message_utils, player_utils

# Global tracking of nomination button messages by player ID
_active_nomination_messages: dict[int, tuple[discord.Message, 'NominationButtonsView']] = {}


class NominationButtonsView(discord.ui.View):
    """View with buttons for prevoting and hand raising during nominations."""

    def __init__(self, nominee_name: str, nominator_name: str, votes_needed: int, player_id: int):
        super().__init__(timeout=None)
        self.nominee_name = nominee_name
        self.nominator_name = nominator_name
        self.votes_needed = votes_needed
        self.player_id = player_id  # ID of the player this ST channel belongs to
        self.is_voting_turn = False  # Track if it's this player's turn to vote
        self._setup_buttons()

    def _setup_buttons(self):
        """Set up the initial button layout."""
        # Clear any existing items
        self.clear_items()

        # Row 1: Prevoting buttons
        self.add_item(PrevoteYesButton())
        self.add_item(PrevoteNoButton())
        self.add_item(RaiseHandButton(self._player_hand_raised()))

        # Add cancel prevote button if player has a prevote set
        if self._player_has_prevote():
            self.add_item(CancelPrevoteButton())

    def _player_has_prevote(self) -> bool:
        """Check if the player has a prevote set."""
        if global_vars.game is game.NULL_GAME or not global_vars.game.isDay:
            return False
        if not global_vars.game.days[-1].votes or global_vars.game.days[-1].votes[-1].done:
            return False

        current_vote = global_vars.game.days[-1].votes[-1]
        return self.player_id in current_vote.presetVotes

    def _player_hand_raised(self) -> bool:
        """Check if the player has their hand raised."""
        if global_vars.game is game.NULL_GAME:
            return False

        # Find the player object
        for player_obj in global_vars.game.seatingOrder:
            if player_obj.user.id == self.player_id:
                return player_obj.hand_raised
        return False

    def update_for_voting_turn(self):
        """Update buttons when it's this player's turn to vote."""
        self.is_voting_turn = True
        self.clear_items()

        # Row 1: Disabled prevoting buttons
        prevote_yes = PrevoteYesButton()
        prevote_yes.disabled = True
        prevote_no = PrevoteNoButton()
        prevote_no.disabled = True
        raise_hand = RaiseHandButton(self._player_hand_raised())
        raise_hand.disabled = True

        self.add_item(prevote_yes)
        self.add_item(prevote_no)
        self.add_item(raise_hand)

        if self._player_has_prevote():
            cancel_prevote = CancelPrevoteButton()
            cancel_prevote.disabled = True
            self.add_item(cancel_prevote)

        # Row 2: Vote buttons
        self.add_item(VoteYesButton(row=1))
        self.add_item(VoteNoButton(row=1))

    async def _handle_prevote(self, interaction: discord.Interaction, vote_value: str):
        """Handle prevote button clicks using existing presetvote logic."""
        # Check if the user is the player this ST channel belongs to
        if interaction.user.id != self.player_id:
            await interaction.response.send_message("These buttons are only for the player this ST channel belongs to.", ephemeral=True)
            return

        # Check if there's an active game and vote
        if global_vars.game is game.NULL_GAME:
            await interaction.response.send_message("There's no game right now.", ephemeral=True)
            return

        if not global_vars.game.isDay:
            await interaction.response.send_message("It's not day right now.", ephemeral=True)
            return

        if not global_vars.game.days[-1].votes or global_vars.game.days[-1].votes[-1].done:
            await interaction.response.send_message("There's no active vote right now.", ephemeral=True)
            return

        # Find the player who clicked the button
        player_obj = player_utils.get_player(interaction.user)
        if not player_obj:
            await interaction.response.send_message("You are not in the game.", ephemeral=True)
            return

        # Get the current vote
        current_vote = global_vars.game.days[-1].votes[-1]

        # Set the preset vote using existing logic
        vote_int = 1 if vote_value == "yes" else 0
        current_vote.presetVotes[player_obj.user.id] = vote_int

        # Send confirmation
        await interaction.response.send_message(
            f"Your vote has been preset to **{vote_value}** for {self.nominee_name}.",
            ephemeral=True
        )

        # Update seating order message to reflect changes
        await global_vars.game.update_seating_order_message()

        # Refresh buttons to show cancel prevote button
        self._setup_buttons()
        if hasattr(self, 'message') and self.message:
            await self.message.edit(view=self)

        bot_client.logger.info(f"{player_obj.display_name} preset vote {vote_value} for {self.nominee_name}")

    async def _handle_cancel_prevote(self, interaction: discord.Interaction):
        """Handle cancel prevote button click."""
        # Check if the user is the player this ST channel belongs to
        if interaction.user.id != self.player_id:
            await interaction.response.send_message("These buttons are only for the player this ST channel belongs to.", ephemeral=True)
            return

        # Check if there's an active game and vote
        if global_vars.game is game.NULL_GAME:
            await interaction.response.send_message("There's no game right now.", ephemeral=True)
            return

        if not global_vars.game.isDay:
            await interaction.response.send_message("It's not day right now.", ephemeral=True)
            return

        if not global_vars.game.days[-1].votes or global_vars.game.days[-1].votes[-1].done:
            await interaction.response.send_message("There's no active vote right now.", ephemeral=True)
            return

        # Find the player who clicked the button
        player_obj = player_utils.get_player(interaction.user)
        if not player_obj:
            await interaction.response.send_message("You are not in the game.", ephemeral=True)
            return

        # Get the current vote and remove prevote
        current_vote = global_vars.game.days[-1].votes[-1]
        if self.player_id in current_vote.presetVotes:
            del current_vote.presetVotes[self.player_id]

        # Send confirmation
        await interaction.response.send_message("Your prevote has been cancelled.", ephemeral=True)

        # Update seating order message to reflect changes
        await global_vars.game.update_seating_order_message()

        # Refresh buttons to hide cancel prevote button
        self._setup_buttons()
        if hasattr(self, 'message') and self.message:
            await self.message.edit(view=self)

        bot_client.logger.info(f"{player_obj.display_name} cancelled prevote for {self.nominee_name}")

    async def _handle_hand_toggle(self, interaction: discord.Interaction):
        """Handle hand raise/lower toggle using existing hand logic."""
        # Check if the user is the player this ST channel belongs to
        if interaction.user.id != self.player_id:
            await interaction.response.send_message("These buttons are only for the player this ST channel belongs to.", ephemeral=True)
            return

        # Check if there's an active game
        if global_vars.game is game.NULL_GAME:
            await interaction.response.send_message("There's no game right now.", ephemeral=True)
            return

        if not global_vars.game.isDay:
            await interaction.response.send_message("It's not day right now.", ephemeral=True)
            return

        if not global_vars.game.days[-1].votes or global_vars.game.days[-1].votes[-1].done:
            await interaction.response.send_message("You can only raise or lower your hand during an active vote.", ephemeral=True)
            return

        # Find the player who clicked the button
        player_obj = player_utils.get_player(interaction.user)
        if not player_obj:
            await interaction.response.send_message("You are not in the game.", ephemeral=True)
            return

        if player_obj.hand_locked_for_vote:
            await interaction.response.send_message(
                "Your hand is currently locked by your vote and cannot be changed for this nomination.",
                ephemeral=True
            )
            return

        # Toggle hand status using existing logic
        if player_obj.hand_raised:
            player_obj.hand_raised = False
            status_msg = "Your hand is lowered."
        else:
            player_obj.hand_raised = True
            status_msg = "Your hand is raised."

        await interaction.response.send_message(status_msg, ephemeral=True)

        # Update seating order message
        await global_vars.game.update_seating_order_message()

        # Refresh buttons to update the hand button label
        if not self.is_voting_turn:
            self._setup_buttons()
        else:
            # Update for voting turn to get the correct hand button label
            self.update_for_voting_turn()

        if hasattr(self, 'message') and self.message:
            try:
                await self.message.edit(view=self)
            except:
                pass  # Ignore edit failures

        bot_client.logger.info(f"{player_obj.display_name} {'raised' if player_obj.hand_raised else 'lowered'} hand for {self.nominee_name} nomination")

    async def _handle_vote(self, interaction: discord.Interaction, vote_value: int):
        """Handle direct vote button clicks when it's the player's turn."""
        # Check if the user is the player this ST channel belongs to
        if interaction.user.id != self.player_id:
            await interaction.response.send_message("These buttons are only for the player this ST channel belongs to.", ephemeral=True)
            return

        # Check if there's an active game and vote
        if global_vars.game is game.NULL_GAME:
            await interaction.response.send_message("There's no game right now.", ephemeral=True)
            return

        if not global_vars.game.isDay:
            await interaction.response.send_message("It's not day right now.", ephemeral=True)
            return

        if not global_vars.game.days[-1].votes or global_vars.game.days[-1].votes[-1].done:
            await interaction.response.send_message("There's no active vote right now.", ephemeral=True)
            return

        # Find the player who clicked the button
        player_obj = player_utils.get_player(interaction.user)
        if not player_obj:
            await interaction.response.send_message("You are not in the game.", ephemeral=True)
            return

        # Send confirmation first to acknowledge the interaction
        vote_text = "yes" if vote_value == 1 else "no"
        await interaction.response.send_message(f"You voted **{vote_text}** for {self.nominee_name}.", ephemeral=True)

        # Disable buttons immediately to prevent double clicks
        for item in self.children:
            item.disabled = True
        if hasattr(self, 'message') and self.message:
            try:
                await self.message.edit(view=self)
            except:
                pass  # Ignore edit failures

        # Get the current vote and place the vote
        current_vote = global_vars.game.days[-1].votes[-1]
        await current_vote.vote(vote_value, voter=player_obj)

        bot_client.logger.info(f"{player_obj.display_name} voted {vote_text} for {self.nominee_name} via button")

    async def on_timeout(self):
        """Disable all buttons when view times out."""
        for item in self.children:
            item.disabled = True
        if hasattr(self, 'message') and self.message:
            try:
                await self.message.edit(view=self)
            except discord.NotFound:
                pass  # Message was deleted


# Button classes
class PrevoteYesButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Prevote Yes", style=discord.ButtonStyle.green, row=0)

    async def callback(self, interaction: discord.Interaction):
        view: NominationButtonsView = self.view
        await view._handle_prevote(interaction, "yes")


class PrevoteNoButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Prevote No", style=discord.ButtonStyle.red, row=0)

    async def callback(self, interaction: discord.Interaction):
        view: NominationButtonsView = self.view
        await view._handle_prevote(interaction, "no")


class RaiseHandButton(discord.ui.Button):
    def __init__(self, hand_raised: bool = False):
        label = "Lower Hand" if hand_raised else "Raise Hand"
        super().__init__(label=label, style=discord.ButtonStyle.primary, row=0)

    async def callback(self, interaction: discord.Interaction):
        view: NominationButtonsView = self.view
        await view._handle_hand_toggle(interaction)


class CancelPrevoteButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Cancel Prevote", style=discord.ButtonStyle.gray, row=0)

    async def callback(self, interaction: discord.Interaction):
        view: NominationButtonsView = self.view
        await view._handle_cancel_prevote(interaction)


class VoteYesButton(discord.ui.Button):
    def __init__(self, row: int = 0):
        super().__init__(label="Vote Yes", style=discord.ButtonStyle.green, row=row)

    async def callback(self, interaction: discord.Interaction):
        view: NominationButtonsView = self.view
        await view._handle_vote(interaction, 1)


class VoteNoButton(discord.ui.Button):
    def __init__(self, row: int = 0):
        super().__init__(label="Vote No", style=discord.ButtonStyle.red, row=row)

    async def callback(self, interaction: discord.Interaction):
        view: NominationButtonsView = self.view
        await view._handle_vote(interaction, 0)


async def send_nomination_buttons_to_st_channels(nominee_name: str, nominator_name: str, votes_needed: int):
    """Send nomination buttons to all active player ST channels."""
    if not global_vars.game or global_vars.game is game.NULL_GAME:
        return

    # Get game settings to find ST channels
    game_settings = None
    try:
        from model import settings
        game_settings = settings.GameSettings.load()
    except Exception as e:
        bot_client.logger.error(f"Failed to load game settings: {e}")
        return

    # Determine who is the first voter (if voting has started)
    first_voter_id = None
    if global_vars.game.days[-1].votes and not global_vars.game.days[-1].votes[-1].done:
        current_vote = global_vars.game.days[-1].votes[-1]
        if current_vote.position < len(current_vote.order):
            first_voter_id = current_vote.order[current_vote.position].user.id

    # Send to all players
    for player_obj in global_vars.game.seatingOrder:
        try:
            # Get the player's ST channel
            st_channel_id = game_settings.get_st_channel(player_obj.user.id)
            if not st_channel_id:
                continue

            st_channel = bot_client.client.get_channel(st_channel_id)
            if not st_channel:
                continue

            # Check if this is the first voter - they get voting turn message instead
            if player_obj.user.id == first_voter_id:
                # This player's turn to vote - send voting turn message
                message_content = f"**{player_obj.display_name}, it's your turn to vote!**\n\n{nominee_name} has been nominated by {nominator_name}. {votes_needed} to execute"
                view = NominationButtonsView(nominee_name, nominator_name, votes_needed, player_obj.user.id)
                view.update_for_voting_turn()  # Set up voting buttons immediately
            else:
                # Regular prevote message for other players
                message_content = f"**Please set a prevote**\n\n{nominee_name} has been nominated by {nominator_name}. {votes_needed} to execute"
                view = NominationButtonsView(nominee_name, nominator_name, votes_needed, player_obj.user.id)

            message = await message_utils.safe_send(st_channel, message_content, view=view)
            if message:
                view.message = message
                # Track this message globally for vote turn updates
                _active_nomination_messages[player_obj.user.id] = (message, view)

        except Exception as e:
            bot_client.logger.error(f"Failed to send nomination buttons to {player_obj.display_name}: {e}")


async def update_buttons_for_voting_turn(player_id: int) -> None:
    """Update nomination buttons for a player when it's their turn to vote."""
    if player_id not in _active_nomination_messages:
        return

    try:
        message, view = _active_nomination_messages[player_id]

        # Update the view for voting turn
        view.update_for_voting_turn()

        # Get player display name for the message
        player_obj = None
        for p in global_vars.game.seatingOrder:
            if p.user.id == player_id:
                player_obj = p
                break

        if player_obj:
            # Update message text to mention it's their turn
            new_content = f"**{player_obj.display_name}, it's your turn to vote!**\n\n{view.nominee_name} has been nominated by {view.nominator_name}. {view.votes_needed} to execute"
            await message.edit(content=new_content, view=view)
            bot_client.logger.info(f"Updated nomination buttons for {player_obj.display_name} - it's their turn to vote")

    except Exception as e:
        bot_client.logger.error(f"Failed to update buttons for player {player_id}: {e}")


async def disable_buttons_for_voter(player_id: int) -> None:
    """Disable nomination buttons for a player when it's their turn to vote."""
    if player_id not in _active_nomination_messages:
        return

    try:
        message, view = _active_nomination_messages[player_id]

        # If already in voting turn mode, don't update again
        if view.is_voting_turn:
            bot_client.logger.info(f"Player {player_id} already has voting turn buttons - skipping update")
            return

        # Use the update function for players who don't already have voting turn buttons
        await update_buttons_for_voting_turn(player_id)

    except Exception as e:
        bot_client.logger.error(f"Failed to check voting turn status for player {player_id}: {e}")


async def enable_buttons_for_voter(player_id: int) -> None:
    """Re-enable nomination buttons for a player after they vote."""
    if player_id not in _active_nomination_messages:
        return

    try:
        message, view = _active_nomination_messages[player_id]

        # Reset to normal button layout
        view.is_voting_turn = False
        view._setup_buttons()

        # Reset message text
        original_content = f"**Please set a prevote**\n\n{view.nominee_name} has been nominated by {view.nominator_name}. {view.votes_needed} to execute"
        await message.edit(content=original_content, view=view)
        bot_client.logger.info(f"Re-enabled nomination buttons for player {player_id} - they finished voting")

    except Exception as e:
        bot_client.logger.error(f"Failed to re-enable buttons for player {player_id}: {e}")


async def clear_nomination_messages() -> None:
    """Delete all tracked nomination button messages (call when vote ends)."""
    # Delete all nomination button messages
    for player_id, (message, view) in _active_nomination_messages.items():
        try:
            # Delete the message with buttons
            await message.delete()
            bot_client.logger.info(f"Deleted nomination buttons message for player {player_id}")
        except Exception as e:
            bot_client.logger.error(f"Failed to delete buttons message for player {player_id}: {e}")

    # Clear the tracking dictionary
    _active_nomination_messages.clear()
    bot_client.logger.info("Cleared all nomination button messages")