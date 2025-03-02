"""
Game fixtures for testing the Blood on the Clocktower Discord bot.

This module provides fixtures and helper functions for setting up test games,
votes, nominations, and game phases.
"""

from unittest.mock import AsyncMock, patch

import pytest_asyncio

import global_vars
from bot_impl import Game, Script, Vote, Day
from model.characters import Character, Storyteller
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
            seatingOrder=[alice_player, bob_player, charlie_player],
            seatingOrderMessage=seating_message,
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
