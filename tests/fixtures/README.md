# Test Fixtures for BOTC Bot

This directory contains fixtures and test helpers for the Blood on the Clocktower Discord bot test suite.

## Available Fixtures

### Discord Mocks (`discord_mocks.py`)

Mock implementations of Discord objects:

- `MockChannel`: Discord text channel with message handling
- `MockMember`: Discord server member with role management
- `MockMessage`: Discord message with edit/pin functionality
- `MockGuild`: Discord server (guild) with member/channel lookup
- `MockRole`: Discord role with member tracking

Factory functions:

- `create_mock_message()`: Creates a mock message
- `create_mock_channel()`: Creates a mock channel
- `create_mock_member()`: Creates a mock member

Fixtures:

- `mock_discord_setup()`: Sets up a complete Discord environment for testing

### Game Fixtures (`game_fixtures.py`)

Game setup helpers:

- `setup_test_game()`: Creates a test game with players and storyteller
- `create_test_player()`: Creates a test player
- `setup_test_vote()`: Creates and sets up a vote
- `start_test_day()`: Starts a day for testing
- `setup_nomination_flow()`: Sets up a complete nomination flow

### Common Patches (`common_patches.py`)

Patch collections:

- `disable_backup()`: Disables backup functionality for tests
- `common_patches()`: Returns common patches needed for most tests
- `patch_file_operations()`: Disables all file operations
- `patch_discord_send()`: Mocks Discord message sending
- `patch_discord_reactions()`: Mocks Discord reaction handling
- `patch_game_functions()`: Mocks Game class methods

### Command Testing (`command_testing.py`)

Command testing helpers:

- `create_command_message()`: Creates a message for command testing
- `execute_command()`: Executes a command with proper patches
- `run_command_player()`: Tests player commands
- `run_command_storyteller()`: Tests storyteller commands
- `run_command_vote()`: Tests voting commands

## Usage

Import the fixtures in your test files:

```python
import pytest
from tests.fixtures.discord_mocks import mock_discord_setup
from tests.fixtures.game_fixtures import setup_test_game
from tests.fixtures.common_patches import common_patches
from tests.fixtures.command_testing import run_command_player


@pytest.mark.asyncio
async def test_some_command(mock_discord_setup, setup_test_game):
    # Test using the fixtures
    result = await run_command_player(
        "vote",
        "yes",
        setup_test_game['players']['alice'],
        mock_discord_setup['channels']['town_square'],
        on_message
    )

    # Verify results
    assert result.called
```

Always use the fixtures to minimize duplication and ensure consistent testing behavior.