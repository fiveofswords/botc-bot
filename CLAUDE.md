# BOTC-Bot Development Guide

## Environment Setup
```bash
# Activate the virtual environment
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

## Configuration

The bot uses environment-specific configurations in the `bot_configs/` directory:

- Production configs: `George.py`, `Leo.py`, `Quinn.py`, `TipToe.py`
- Testing configs: `bot_configs/testing/atreys.py`, `bot_configs/testing/dlorant.py`

Each config defines server IDs, channel IDs, role names, and bot-specific settings. See `config.py` for the main
configuration template.

## Test Commands

**Prerequisites for running tests:**

- `token.txt` file in root directory (can contain dummy content for testing)
- `config.py` file in root directory (see Configuration section above)

These files are required for imports to work, but tests use comprehensive mocking so actual values don't matter.

```bash
# Run all tests
python -m pytest

# Run tests with coverage
python -m pytest --cov=. --cov-report=term

# Run specific test file
python -m pytest tests/time_utils/test_time_utils.py

# Run specific test class or method
python -m pytest tests/time_utils/test_time_utils.py::TestParseDeadline
python -m pytest tests/time_utils/test_time_utils.py::TestParseDeadline::test_unix_timestamp

# Run with verbose output or show stdout/stderr
python -m pytest -v
python -m pytest -s
```

## Docker Deployment

```bash
# Build the docker image
docker build -t botc .

# Run with specific bot configuration
docker run -v $(dirname $(pwd))/preferences.json:/preferences.json -v $(pwd):/app -v $(pwd)/bot_configs/${BOT_NAME}.py:/app/config.py -d --name ${BOT_NAME} botc

# Enter shell for debugging
docker exec -it ${BOT_NAME} /bin/bash
```

## Project Structure

- `model/` - Core game entities (player, characters, settings, channels)
- `utils/` - Utility functions and helpers
- `time_utils/` - Time-related utilities
- `global_vars.py` - Centralized global state management
- `bot_configs/` - Environment-specific configurations
- `tests/` - Test directory with comprehensive fixtures and mocks

### Core Modules

- `bot.py` - Main bot entry point
- `bot_impl.py` - Core bot implementation and command handling
- `bot_client.py` - Discord client wrapper
- `global_vars.py` - Global state management for server, channels, roles

### Model Structure

- `model/player.py` - Player class and management
- `model/characters/` - Character system (base classes, implementations, registry)
- `model/game/` - Game mechanics (day, vote, script, whisper mode, traveler voting)
- `model/channels/` - Channel management and utilities
- `model/settings/` - Game and global settings

### Utility Modules

- `utils/character_utils.py` - Character ability and interaction utilities
- `utils/game_utils.py` - Game state management and Discord presence updates
- `utils/message_utils.py` - Safe message sending with error handling and text splitting
- `utils/player_utils.py` - Player management and search utilities
- `time_utils/time_utils.py` - Time parsing and deadline management

### Character System

- Base classes: `model/characters/base.py`
- Specific implementations: `model/characters/specific.py`
- Character registry: `model/characters/registry.py`

### Testing Infrastructure

- `tests/fixtures/` - Comprehensive test fixtures and mocks
  - `discord_mocks.py` - Mock Discord objects (channels, members, messages)
  - `game_fixtures.py` - Game setup fixtures and helpers
  - `common_patches.py` - Reusable patch collections
  - `command_testing.py` - Command testing utilities
- Organized test structure by functionality (core, discord, game, model, utils)
- Async test support with pytest-asyncio
- Mock-based testing to prevent side effects

## Code Style Guidelines

### Imports
- Group imports: standard library, third-party, local/project
- Sort alphabetically within groups
- Use absolute imports instead of relative
- Avoid wildcard imports

### Type Hints

- Use annotations for parameters and return values
- Import from typing module (Optional, List, Dict, etc.)
- Place TypedDict definitions at module level

### Naming and Formatting
- Classes: PascalCase
- Functions/variables: snake_case
- Constants: UPPER_SNAKE_CASE
- Private attributes: prefix with underscore (_var_name)
- Line length: 100 characters maximum

### Error Handling
- Use specific exceptions rather than generic ones
- Log exceptions with appropriate context
- Avoid bare except clauses
- Document expected exceptions in docstrings

### Documentation

- Use Google-style docstrings
- Document parameters, return values, and exceptions
- Include examples for complex functions