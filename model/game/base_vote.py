import asyncio
from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional

import discord

import global_vars
import model.settings
from utils import message_utils, player_utils


class VoteOutcome(Enum):
    """Possible outcomes of a vote."""
    PASS = "PASS"
    TIE = "TIE"
    FAIL = "FAIL"


class BaseVote(ABC):
    """Base class for voting systems with shared logic.

    Attributes:
        nominee: The player being nominated
        nominator: The player making the nomination
        order: The order of players voting
        votes: The number of votes
        voted: The players who voted
        history: The voting history
        announcements: The announcement messages
        presetVotes: The preset votes
        values: The vote weights for each player, tuple of (no votes, yes votes)
        majority: The number of votes needed for a majority
        position: The current position in the vote order
        done: Whether the vote is done
    """

    # Type annotations for instance attributes
    nominee: Optional[model.player.Player]
    nominator: Optional[model.player.Player]
    order: list[model.player.Player]
    votes: int
    voted: list[model.player.Player]
    history: list[int]
    announcements: list[int]
    presetVotes: dict[int, int]
    values: dict[model.player.Player, tuple[int, int]]
    majority: int
    position: int
    done: bool
    _vote_lock: asyncio.Lock

    def __init__(self, nominee: Optional[model.player.Player], nominator: Optional[model.player.Player]) -> None:
        """Initialize a BaseVote.

        Args:
            nominee: The player being nominated
            nominator: The player making the nomination
        """
        self.nominee = nominee
        self.nominator = nominator
        self.order = self._get_voting_order()
        self.votes = 0
        self.voted = []
        self.history = []
        self.announcements = []
        self.presetVotes = {}
        self.values = {person: (0, 1) for person in self.order}
        self.majority = self._calculate_majority()
        self.position = 0
        self.done = False
        self._vote_lock = asyncio.Lock()  # Prevent race conditions on voting

    # Do not allow pickling of the vote lock
    def __getstate__(self):
        """Exclude _vote_lock from pickling since asyncio.Lock is not serializable."""
        state = self.__dict__.copy()
        state.pop('_vote_lock', None)
        return state

    def __setstate__(self, state):
        """Recreate _vote_lock after unpickling."""
        self.__dict__.update(state)
        self._vote_lock = asyncio.Lock()

    # Abstract methods (must be implemented by subclasses)
    @abstractmethod
    def _get_voting_order(self) -> list[model.player.Player]:
        """Get the order of players for voting."""
        pass

    @abstractmethod
    def _calculate_majority(self) -> int:
        """Calculate the majority needed for this vote type."""
        pass

    @abstractmethod
    def _determine_outcome(self) -> VoteOutcome:
        """Determine the outcome of the vote.

        Returns:
            VoteOutcome: The outcome of the vote
        """
        pass

    @abstractmethod
    def _get_outcome_message(self, outcome: VoteOutcome) -> str:
        """Get the message for a given vote outcome.

        Args:
            outcome: The vote outcome

        Returns:
            str: Message describing the outcome
        """
        pass

    # Hook methods (can be overridden by subclasses)
    async def _apply_outcome_effects(self, outcome: VoteOutcome) -> None:
        """Apply side effects based on vote outcome. Override in subclasses if needed."""
        pass

    def _cleanup_player_state(self) -> None:
        """Clean up player state after vote. Override in subclasses if needed."""
        pass

    def _validate_vote(self, voter: model.player.Player, vt: int) -> tuple[bool, str]:
        """Validate if a vote is allowed.

        Args:
            voter: The player voting
            vt: The vote weight (0 or 1)

        Returns:
            tuple: (allowed: bool, reason: str)
        """
        return True, ""

    def _apply_vote_effects(self, voter: model.player.Player, vt: int) -> None:
        """Apply any special effects when a vote is cast.

        Args:
            voter: The player voting
            vt: The vote weight (0 or 1)
        """
        # Manage hand state based on vote
        if vt == 1:  # Yes vote
            voter.hand_raised = True
        else:  # No vote
            voter.hand_raised = False
        voter.hand_locked_for_vote = True

        # Update seating order message immediately
        asyncio.create_task(global_vars.game.update_seating_order_message())

    def _should_skip_voter(self, voter: model.player.Player) -> bool:
        """Check if a player should be skipped (not asked to vote).

        Args:
            voter: The player to check

        Returns:
            bool: True if the player should be skipped
        """
        return False

    # Core voting workflow methods
    async def call_next(self) -> None:
        """Calls for person to vote."""
        to_call_player = self.order[self.position]
        to_call_display_name = to_call_player.display_name
        to_call_user = to_call_player.user
        to_call_user_id = to_call_player.user.id
        nominee_name = player_utils.get_player_display_name(self.nominee)

        # Check for preset votes
        if to_call_user_id in self.presetVotes:
            preset_player_vote = self.presetVotes[to_call_user_id]
            self.presetVotes[to_call_user_id] -= 1
            await self.vote(int(preset_player_vote > 0), voter=to_call_player)
            return

        # Check if player should be skipped
        if self._should_skip_voter(to_call_player):
            await self.vote(0, voter=to_call_player)
            return

        # Call for manual vote
        await message_utils.safe_send(global_vars.channel,
                                      f"{to_call_user.mention}, your vote on {nominee_name}. Current votes: {self.votes}.")

        # Handle default votes
        global_settings: model.settings.GlobalSettings = model.settings.GlobalSettings.load()
        default: Optional[tuple[int, int]] = global_settings.get_default_vote(to_call_user_id)
        if default:
            time = default[1]
            yes_no = ["no", "yes"][default[0]]
            mins = str(time // 60)
            await message_utils.safe_send(to_call_user, f"Will enter a {yes_no} vote in {mins} minutes.")
            await message_utils.notify_storytellers(
                f"{to_call_display_name}'s vote on {nominee_name}. Their default is {yes_no} in {mins} minutes. Current votes: {self.votes}.")
            await asyncio.sleep(time)
            this_nomination = global_vars.game.days[-1].votes[-1]
            if to_call_player == this_nomination.order[this_nomination.position]:
                # Place default vote if still this player's turn
                await self.vote(default[0], voter=to_call_player)
        else:
            await message_utils.notify_storytellers(
                f"{to_call_display_name}'s vote on {nominee_name}. They have no default. Current votes: {self.votes}.")

    async def vote(self, vt: int, voter: model.player.Player, operator: Optional[discord.Member] = None) -> None:
        """Executes a vote.

        Args:
            vt: 0 if no, 1 if yes
            voter: The player who is voting
            operator: The operator making the vote (storyteller, etc.)
        """
        async with self._vote_lock:
            # Check if voting is still valid (vote may have ended while waiting for lock)
            if self.done or self.position >= len(self.order):
                if operator:
                    await message_utils.safe_send(operator, "This vote has already ended.")
                return

            # Determine the expected voter
            expected_voter = self.order[self.position]

            # Validate it's the correct player's turn
            if voter.user.id != expected_voter.user.id:
                error_msg = f"It's {expected_voter.display_name}'s turn to vote, not {voter.display_name}'s."
                if operator:
                    await message_utils.safe_send(operator, error_msg)
                else:
                    await message_utils.safe_send(voter.user, error_msg)
                return

            # Validate the vote
            allowed, reason = self._validate_vote(voter, vt)
            if not allowed:
                if not operator:
                    await message_utils.safe_send(voter.user, reason)
                else:
                    await message_utils.safe_send(operator, reason)
                return

            # Apply vote effects
            self._apply_vote_effects(voter, vt)

            # Vote tracking
            self.history.append(vt)
            self.votes += self.values[voter][vt]
            if vt == 1:
                self.voted.append(voter)
        # end critical section with vote lock

        # Announcement
        text = "yes" if vt == 1 else "no"
        self.announcements.append(
            (
                await message_utils.safe_send(
                    global_vars.channel,
                    f"{voter.display_name} votes {text}. {str(self.votes)} votes.",
                )
            ).id
        )
        await (await global_vars.channel.fetch_message(self.announcements[-1])).pin()

        # Next vote
        self.position += 1
        if self.position == len(self.order):
            await self.end_vote()
            return
        await self.call_next()

    async def end_vote(self) -> None:
        """When the vote is over."""
        # Format voter list
        voters_text = self._format_voters_list()

        # Determine outcome and apply effects
        outcome = self._determine_outcome()
        await self._apply_outcome_effects(outcome)

        # Send announcement
        message = self._get_outcome_message(outcome)
        await self._send_final_announcement(voters_text, message)

        # Clean up all vote state
        await self._cleanup_vote_state()

        # Finalize and reopen game interactions
        await self._finalize_vote()

    # Helper methods for end_vote
    def _format_voters_list(self) -> str:
        """Format the list of voters into a readable string."""
        the_voters = list(dict.fromkeys(self.voted))  # Remove duplicates while preserving order

        if len(the_voters) == 0:
            return "no one"
        elif len(the_voters) == 1:
            return the_voters[0].display_name
        elif len(the_voters) == 2:
            return f"{the_voters[0].display_name} and {the_voters[1].display_name}"
        else:
            names = ", ".join(voter.display_name for voter in the_voters[:-1])
            return f"{names}, and {the_voters[-1].display_name}"

    async def _send_final_announcement(self, voters_text: str, outcome_message: str) -> discord.Message:
        """Send the final vote announcement and pin it."""
        nominee_name = player_utils.get_player_display_name(self.nominee)
        nominator_name = player_utils.get_player_display_name(self.nominator)

        message_suffix = f". {outcome_message}" if outcome_message else "."

        announcement = await message_utils.safe_send(
            global_vars.channel,
            f"{self.votes} votes on {nominee_name} (nominated by {nominator_name}): {voters_text}{message_suffix}"
        )

        await announcement.pin()
        global_vars.game.days[-1].voteEndMessages.append(announcement.id)
        return announcement

    async def _cleanup_vote_messages(self) -> None:
        """Unpin individual vote messages."""
        for msg_id in self.announcements:
            try:
                message = await global_vars.channel.fetch_message(msg_id)
                await message.unpin()
            except discord.errors.NotFound:
                print("Missing message: ", str(msg_id))
            except discord.errors.DiscordServerError:
                print("Discord server error: ", str(msg_id))

    async def _reset_player_hands(self) -> None:
        """Reset hand states for all players and update seating order display."""
        for person in global_vars.game.seatingOrder:
            person.hand_raised = False
            person.hand_locked_for_vote = False

        # Update seating order message to reflect hand state changes
        await global_vars.game.update_seating_order_message()

    async def _cleanup_vote_state(self) -> None:
        """Clean up all per-nomination state after voting concludes."""
        # Clean up vote messages
        await self._cleanup_vote_messages()

        # Reset player hands
        await self._reset_player_hands()

        # Additional cleanup in subclasses
        self._cleanup_player_state()

    async def _finalize_vote(self) -> None:
        """Finalize vote state and reopen game interactions."""
        self.done = True
        await global_vars.game.days[-1].open_noms()
        await global_vars.game.days[-1].open_pms()

    # Vote management methods
    async def preset_vote(self, person: model.player.Player, vt: int,
                          operator: Optional[discord.Member] = None) -> None:
        """Preset a vote.

        Args:
            person: The player to preset
            vt: The vote value
            operator: The operator making the preset
        """
        # Validate the preset vote
        allowed, reason = self._validate_vote(person, vt)
        if not allowed:
            if not operator:
                await message_utils.safe_send(person.user, reason)
            else:
                await message_utils.safe_send(operator, reason)
            return

        self.presetVotes[person.user.id] = vt

    async def cancel_preset(self, person: model.player.Player) -> None:
        """Cancel a preset vote.

        Args:
            person: The player to cancel the preset for
        """
        if person.user.id in self.presetVotes:
            del self.presetVotes[person.user.id]

    async def delete(self) -> None:
        """Undoes an unintentional nomination."""
        if self.nominator:
            self.nominator.can_nominate = True
        if self.nominee:
            self.nominee.can_be_nominated = True

        for msg in self.announcements:
            try:
                await (await global_vars.channel.fetch_message(msg)).unpin()
            except discord.errors.NotFound:
                pass
        self.done = True
        global_vars.game.days[-1].votes.remove(self)
