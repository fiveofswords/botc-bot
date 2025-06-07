"""
Game fixtures for testing the Blood on the Clocktower Discord bot.

This module provides fixtures and helper functions for setting up test games,
votes, nominations, and game phases.
"""

from unittest.mock import AsyncMock, patch

import pytest_asyncio

import global_vars
from model.characters import Character, Storyteller
from model.game.day import Day
from model.game.game import Game
from model.game.script import Script
from model.game.vote import Vote
from model.player import Player
from model.player import STORYTELLER_ALIGNMENT


@pytest_asyncio.fixture
async def setup_test_game(mock_discord_setup):
    """Set up a test game for command testing."""
    # Create Players
    alice_player = Player(
        Character,
        "good",
        mock_discord_setup['members']['alice'],
        mock_discord_setup['channels']['st1'],
        0
    )

    bob_player = Player(
        Character,
        "good",
        mock_discord_setup['members']['bob'],
        mock_discord_setup['channels']['st2'],
        1
    )

    charlie_player = Player(
        Character,
        "evil",
        mock_discord_setup['members']['charlie'],
        mock_discord_setup['channels']['st3'],
        2
    )

    storyteller_player = Player(
        Storyteller,
        STORYTELLER_ALIGNMENT,
        mock_discord_setup['members']['storyteller'],
        None,
        None
    )

    # Create seating order message
    seating_message = await mock_discord_setup['channels']['town_square'].send(
        "**Seating Order:**\nAlice\nBob\nCharlie")

    # Mock the start_day and end methods to avoid Discord API calls
    with patch('bot_impl.update_presence'):
        # Create game object with patched methods
        game = Game(
            seating_order=[alice_player, bob_player, charlie_player],
            seating_order_message=seating_message,
            script=Script([])
        )

        # Create a Day object with mocked methods to avoid Discord API calls
        day = Day()
        day.open_pms = AsyncMock()
        day.open_noms = AsyncMock()
        day.nomination = AsyncMock()
        day.end = AsyncMock()

        # Add a mocked day to the game
        game.days.append(day)

        # Override start_day method to avoid Discord API calls
        original_start_day = game.start_day

        async def mocked_start_day(kills=None, origin=None):
            game.isDay = True
            if not game.days:
                game.days.append(day)
            return

        game.start_day = mocked_start_day

        # Add storyteller
        game.storytellers = [storyteller_player]

        # Store the game in global_vars
        global_vars.game = game

        return {
            'game': game,
            'players': {
                'alice': alice_player,
                'bob': bob_player,
                'charlie': charlie_player,
                'storyteller': storyteller_player
            }
        }


def create_test_player(character_class, alignment, user, channel, position):
    """Create a test player with the given parameters."""
    return Player(character_class, alignment, user, channel, position)


def setup_test_vote(game, nominee, nominator, voters=None):
    """Create and set up a test vote."""
    vote = Vote(nominee, nominator)
    if voters:
        vote.order = voters
        vote.position = 0
    game.days[-1].votes.append(vote)
    return vote


async def start_test_day(game):
    """Start a day for testing."""
    await game.start_day()
    return game.days[-1]


async def setup_nomination_flow(game, nominee, nominator):
    """Set up a nomination flow for testing."""
    # Start the day and open nominations
    day = game.days[-1] if game.days else await start_test_day(game)
    day.isNoms = True

    # Create a vote from the nomination
    vote = setup_test_vote(game, nominee, nominator)

    # Return the vote and day objects
    return vote, day


def setup_vote_with_preset(game, nominee, nominator, voters, preset_votes=None):
    """Create a vote with preset votes for testing."""
    vote = setup_test_vote(game, nominee, nominator, voters)

    if preset_votes:
        for player_id, vote_value in preset_votes.items():
            vote.presetVotes[player_id] = vote_value

    return vote


def setup_hand_states(players, hand_states):
    """Set up hand states for multiple players."""
    for player_name, states in hand_states.items():
        if player_name in players:
            player = players[player_name]
            if 'hand_raised' in states:
                player.hand_raised = states['hand_raised']
            if 'hand_locked_for_vote' in states:
                player.hand_locked_for_vote = states['hand_locked_for_vote']


def create_active_vote_scenario(game, nominee, nominator, voters, preset_votes=None, hand_states=None):
    """Create a complete active vote scenario for testing."""
    # Ensure day is started
    if not game.days:
        from model.game.day import Day
        day = Day()
        game.days.append(day)
        game.isDay = True

    # Create vote
    vote = setup_vote_with_preset(game, nominee, nominator, voters, preset_votes)

    # Set up hand states if provided
    if hand_states:
        setup_hand_states({
            'alice': game.seatingOrder[0] if len(game.seatingOrder) > 0 else None,
            'bob': game.seatingOrder[1] if len(game.seatingOrder) > 1 else None,
            'charlie': game.seatingOrder[2] if len(game.seatingOrder) > 2 else None,
            **hand_states
        }, hand_states)

    return vote


def setup_storyteller_permissions(storyteller, mock_discord_setup):
    """Set up storyteller permissions for testing."""
    storyteller.user.roles = [mock_discord_setup['roles']['gamemaster']]
    mock_discord_setup['guild'].get_member = lambda user_id: storyteller.user
