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
- `MockClient`: Discord client with automatic guild/channel lookup

**Enhanced Features:**

- MockClient automatically provides `get_guild()` and `get_channel()` methods
- Automatic channel and category lookup by ID from the associated guild
- No manual client method setup required in tests

**Note:** Mock objects should be created directly using their class constructors (e.g., `MockMessage()`,
`MockChannel()`, `MockMember()`) for better clarity and explicitness.

Fixtures:

- `mock_discord_setup()`: Sets up a complete Discord environment with enhanced MockClient

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

Patch collections for different testing scenarios:

**Core patches (return lists for ExitStack):**

- `backup_patches_combined()`: Disables backup functionality
- `file_operation_patches_combined()`: Disables file system operations
- `discord_reaction_patches_combined()`: Mocks Discord reaction handling
- `file_operations_patches_combined()`: Disables all file operations

**Dictionary patches (for manual patching):**
- `discord_message_patches()`: Mocks Discord message sending
- `game_function_patches()`: Mocks Game class methods
- `base_bot_patches()`: Core patches for bot functionality
- `config_patches()`: Patches bot config values with mock Discord objects

**Targeted patches for specific scenarios:**
- `command_execution_patches()`: Patches for command testing
- `hand_status_patches()`: Patches for hand status testing
- `vote_execution_patches()`: Patches for vote execution testing
- `storyteller_command_patches()`: Patches for storyteller command testing

**Complete bot setup:**

- `full_bot_setup_patches_combined()`: Complete patches for bot initialization tests
- `disable_backup()`: Auto-fixture that disables backup for all tests

### Command Testing (`command_testing.py`)

Command testing helpers:

- `create_command_message()`: Creates a message for command testing
- `execute_command()`: Executes a command with proper patches
- `run_command_player()`: Tests player commands
- `run_command_storyteller()`: Tests storyteller commands
- `run_command_vote()`: Tests voting commands

**Enhanced helpers for common patterns:**

- `execute_command_with_wait_for()`: Execute commands with predefined client.wait_for responses
- `test_hand_command()`: Helper for testing hand commands with prevote interactions
- `patch_hand_status_testing()`: Context manager for hand status testing patches
- `patch_vote_testing()`: Context manager for vote testing patches

## Usage

Import the fixtures in your test files:

```python
import pytest
from unittest.mock import patch, AsyncMock
from contextlib import ExitStack
from tests.fixtures.discord_mocks import mock_discord_setup, MockMessage
from tests.fixtures.game_fixtures import setup_test_game
from tests.fixtures.common_patches import full_bot_setup_patches_combined
from bot_impl import on_message, on_ready


@pytest.mark.asyncio
async def test_bot_initialization(mock_discord_setup):
    """Example of bot initialization testing with complete setup."""
    # Use the complete bot setup patches
    patches = full_bot_setup_patches_combined(mock_discord_setup)
    with ExitStack() as stack:
        for p in patches:
            stack.enter_context(p)

        # Test bot initialization
        await on_ready()

        # Verify initialization completed
        assert global_vars.server == mock_discord_setup['guild']


@pytest.mark.asyncio
async def test_command_execution(mock_discord_setup, setup_test_game):
    """Example of testing commands with targeted patches."""
    game = setup_test_game['game']
    alice = setup_test_game['players']['alice']

    # Create a command message using MockMessage directly
    msg = MockMessage(
        content="@hand up",
        channel=alice.user.dm_channel,
        author=alice.user
    )

    # Use targeted patches for specific functionality
    with patch('bot_impl.get_player', return_value=alice):
        with patch('utils.message_utils.safe_send', new_callable=AsyncMock) as mock_safe_send:
            await on_message(msg)

            # Verify results
            assert mock_safe_send.called
```

Always use the fixtures to minimize duplication and ensure consistent testing behavior.