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

**Enhanced helpers for common patterns:**

- `setup_vote_with_preset()`: Create a vote with preset votes for testing
- `setup_hand_states()`: Set up hand states for multiple players
- `create_active_vote_scenario()`: Create a complete active vote scenario for testing
- `setup_storyteller_permissions()`: Set up storyteller permissions for testing

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

**Enhanced helpers for common patterns:**

- `execute_command_with_wait_for()`: Execute commands with predefined client.wait_for responses

**Note:** For MockMessage creation, use `MockMessage` directly instead of wrapper functions for better clarity and
explicitness.

## Usage

Import the fixtures in your test files:

```python
import pytest
from unittest.mock import patch, AsyncMock
from tests.fixtures.discord_mocks import mock_discord_setup
from tests.fixtures.game_fixtures import setup_test_game, setup_vote_with_preset, setup_storyteller_permissions
from tests.fixtures.discord_mocks import MockMessage
from bot_impl import on_message


@pytest.mark.asyncio
async def test_some_command(mock_discord_setup, setup_test_game):
    # Test using the enhanced fixtures
    game = setup_test_game['game']
    alice = setup_test_game['players']['alice']
    storyteller = setup_test_game['players']['storyteller']

    # Set up a vote with preset votes using shared infrastructure
    vote = setup_vote_with_preset(
        game=game,
        nominee=alice,
        nominator=storyteller,
        voters=[alice],
        preset_votes={alice.user.id: 1}
    )

    # Set up storyteller permissions using shared helper
    setup_storyteller_permissions(
        storyteller=storyteller,
        mock_discord_setup=mock_discord_setup
    )

    # Create a command message using MockMessage directly
    msg = MockMessage(
        content="@vote yes",
        channel=alice.user.dm_channel,
        author=alice.user
    )

    # Test with individual patches (recommended approach)
    with patch('bot_impl.get_player', return_value=alice),
            patch('bot_impl.backup') as mock_backup,
            patch('bot_impl.safe_send', new_callable=AsyncMock) as mock_safe_send:
        await on_message(msg)

        # Verify results
        assert mock_backup.called
        assert mock_safe_send.called
```

Always use the fixtures to minimize duplication and ensure consistent testing behavior.