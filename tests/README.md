# Blood on the Clocktower Bot Test Suite

## Overview

This test suite implements comprehensive testing for the Blood on the Clocktower Discord bot. The tests verify the
functionality of all commands and features while preventing unwanted side effects like file creation or modification
during testing.

## Test Organization

The test suite is organized by functionality:

```
tests/
├── fixtures/                           # Shared test fixtures and utilities
│   ├── __init__.py
│   ├── README.md                       # Documentation for fixtures
│   ├── discord_mocks.py                # Discord object mock implementations
│   ├── game_fixtures.py                # Game setup fixtures and helpers
│   ├── common_patches.py               # Common patch collections
│   └── command_testing.py              # Command testing helpers
├── core/                               # Core functionality tests
│   ├── test_backup_functions.py        # Tests for backup and restore functionality
│   ├── test_day_class.py               # Tests for Day class functionality
│   ├── test_vote_class.py              # Tests for Vote class functionality
│   └── test_game_class.py              # Tests for Game class functionality
├── discord/                            # Discord API integration tests
│   ├── test_channel_management.py      # Tests for Discord channel management
│   ├── test_on_message.py              # Tests for message handling functionality
│   └── test_command_interactions.py    # Tests for interactions between commands
├── game/                               # Game mechanics tests
│   ├── test_character_functionality.py # Tests for character mechanics
│   └── test_whisper_mode.py            # Tests for whisper mode functionality
├── commands/                           # Command tests
│   ├── run_player_commands.py         # Tests for player-specific commands
│   ├── run_storyteller_commands.py    # Tests for storyteller commands
│   └── test_settings_functionality.py  # Tests for settings commands
├── model/                              # Model class tests
│   ├── channels/
│   │   └── test_channel_manager.py     # Tests for the ChannelManager class
│   ├── characters/
│   │   └── test_registry.py            # Tests for the character registry
│   ├── player/
│   │   └── test_player.py              # Tests for the Player class
│   └── settings/
│       ├── test_game_settings.py       # Tests for game settings
│       └── test_global_settings.py     # Tests for global settings
├── utils/                              # Utility function tests
│   ├── test_string_utils.py            # Tests for string manipulation utilities
│   ├── test_message_utils.py           # Tests for message sending utilities
│   └── test_player_utils.py            # Tests for player management utilities
├── time_utils/                         # Time utility tests
│   └── test_time_utils.py              # Tests for time parsing and manipulation
├── test_bot_integration.py             # Core integration tests
└── test_commands.py                    # Tests for basic bot commands
```

## Key Test Fixtures

The test suite uses a dedicated fixtures directory (`tests/fixtures/`) with the following components:

### Discord Mocks (`discord_mocks.py`)

- **mock_discord_setup**: Creates a mock Discord environment with users, channels, and roles
- Mock implementations of Discord objects (MockChannel, MockMember, MockMessage, etc.)
- Factory functions for creating Discord mock objects

### Game Fixtures (`game_fixtures.py`)

- **setup_test_game**: Sets up a test game with players and a storyteller
- Helper functions for creating test players, votes, and nominations
- Functions for setting up different game phases

### Common Patches (`common_patches.py`)

- **disable_backup**: Disables backup functionality during tests
- **common_patches**: Standard patch sets for Discord API and file operations
- Additional patch collections for specific testing scenarios

### Command Testing (`command_testing.py`)

- Helper functions for testing player and storyteller commands
- Functions for simulating command execution
- Vote testing utilities

## Running Tests

```bash
# Run all tests
python -m pytest

# Run tests in a specific category
python -m pytest tests/utils/

# Run a specific test file
python -m pytest tests/game/test_whisper_mode.py

# Run a specific test function
python -m pytest tests/commands/run_command_player_commands.py::test_player_vote

# Run with coverage report
python -m pytest --cov=.
```

## Testing Strategy

Our tests follow these key principles:

1. **Isolation**: Tests don't modify real files or Discord channels
2. **Mocking**: We mock Discord API and file I/O operations
3. **Direct Function Testing**: We test command functions directly rather than through message processing
4. **Comprehensive Coverage**: We test all command categories:
    - Game Management (startgame, endgame, etc.)
    - Player Management (kill, revive, etc.)
    - Vote Management (vote, nominate, etc.)
    - Day Phase Management (startday, endday, etc.)

With the new test fixtures, tests can be simplified to:

```python
import pytest
from unittest.mock import AsyncMock, patch
from tests.fixtures.discord_mocks import mock_discord_setup
from tests.fixtures.game_fixtures import setup_test_game
from tests.fixtures.command_testing import run_command_storyteller
from bot_impl import on_message


@pytest.mark.asyncio
async def test_some_command(mock_discord_setup, setup_test_game):
    # 1. Mock the target function
    with patch.object(setup_test_game['game'], 'some_function', new_callable=AsyncMock) as mock_func:
        # 2. Use the command testing helper to test a storyteller command
        mock_send = await run_command_storyteller(
            command="command_name",
            args="optional_args",
            st_player=setup_test_game['players']['storyteller'],
            channel=setup_test_game['players']['storyteller'].user.dm_channel,
            command_function=on_message
        )

        # 3. Verify the function was called with expected arguments
        mock_func.assert_called_once()

        # 4. Verify the correct response was sent
        mock_send.assert_called_with(
            setup_test_game['players']['storyteller'].user,
            "Expected response message"
        )
```

## Adding New Tests

When adding new tests:

1. Place the test in the appropriate subdirectory based on what you're testing
2. Import the necessary fixtures from `tests/fixtures/` directory:
   ```python
   from tests.fixtures.discord_mocks import mock_discord_setup
   from tests.fixtures.game_fixtures import setup_test_game
   from tests.fixtures.common_patches import common_patches
   from tests.fixtures.command_testing import run_command_player
   ```
3. Use the helper functions and patch sets to simplify test setup:
   ```python
   # Use patch sets for common operations
   with patch.object(setup_test_game['game'], 'some_method', new_callable=AsyncMock):
       # Use command testing helpers
       mock_send = await run_command_player(...)
   ```
4. Mock any external functions to keep tests self-contained
5. Test functions directly when possible instead of using `on_message`

## Test Coverage

Current test coverage:

- 421 passing tests (10 skipped)
- 76% overall code coverage
- Strong coverage in model and utility modules
- Areas needing improvement: character implementation (~35% coverage)

## Recent Improvements

The test suite has been significantly improved:

1. **Extracted Test Fixtures**:
    - Created a dedicated `fixtures` directory for test infrastructure
    - Extracted mock Discord objects to `discord_mocks.py`
    - Created game setup helpers in `game_fixtures.py`
    - Centralized common patches in `common_patches.py`
    - Added command testing utilities in `command_testing.py`

2. **Reorganized Test Structure**:
    - Implemented a clear, categorized directory structure
    - Organized tests by functionality into coherent groups
    - Fixed import issues with proper pathing and module structure

3. **Fixed AsyncMock Pickling Issues**:
    - Converted tests from message-based to direct function calls
    - Successfully fixed previously skipped tests
    - Added robust handling for attributes that might not exist

4. **Added New Test Files and Infrastructure**:
    - Added test helpers for common patterns
    - Fixed and unified duplicate mock implementations
    - Created factory functions for Discord mocks
    - Added test utilities for command execution

## Future Improvements

Potential areas for test improvement:

1. Migrate existing tests to use the new fixtures:
    - Convert test_bot_integration.py tests to use the new fixtures
    - Update older tests to use command_testing.py helpers

2. Increase test coverage:
    - Target character implementation code (~35% current coverage)
    - Add more integration tests for complex workflows
    - Add tests for edge cases in command handling

3. Enhance test infrastructure:
    - Add fixtures for character-specific testing
    - Create fixtures for testing complex game states
    - Add performance tests for large games

4. Advanced testing techniques:
    - Implement property-based testing for game mechanics
    - Add fuzz testing for command input validation
    - Create integration test suite for end-to-end workflows