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

- None! Tests automatically handle missing configuration files with fallback defaults.

The codebase uses lazy loading for `token.txt` and graceful fallback for `config.py`, so tests run without requiring any
additional setup files.

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
- `commands/` - Enhanced command registry system with help integration
- `global_vars.py` - Centralized global state management
- `bot_configs/` - Environment-specific configurations
- `tests/` - Test directory with comprehensive fixtures and mocks

### Core Modules

- `bot.py` - Main bot entry point
- `bot_impl.py` - Core bot implementation and legacy command handling
- `bot_client.py` - Discord client wrapper
- `global_vars.py` - Global state management for server, channels, roles

### Command System

- `commands/registry.py` - Enhanced command registry with help metadata support and skeleton fallback
- `commands/command_enums.py` - Enums for command categorization (sections, user types, game phases)
- `commands/help_commands.py` - Integrated help system with command registration and dynamic generation
- `commands/loader.py` - Command module loader for all command files
- `commands/information_commands.py` - 18 skeleton commands for game information
- `commands/game_management_commands.py` - 13 skeleton commands for game state management
- `commands/player_management_commands.py` - 17 skeleton commands for player state management
- `commands/voting_commands.py` - 12 skeleton commands for voting and nominations
- `commands/communication_commands.py` - 8 skeleton commands for PM and communication control
- `commands/utility_commands.py` - Utility commands (makealias, etc.)
- `commands/debug_commands.py` - Example registry-based commands

**Skeleton Registration Strategy**: All 61 commands are registered with `implemented=False`, providing complete metadata
while falling back to `bot_impl.py` for execution. Individual commands can be migrated by setting `implemented=True`.

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
  - `discord_mocks.py` - Mock Discord objects with automatic client behavior
  - `game_fixtures.py` - Game setup fixtures and helpers
  - `common_patches.py` - Reusable patch collections with ExitStack support
  - `command_testing.py` - Command testing utilities
- Organized test structure by functionality (core, discord, game, model, utils)
- Async test support with pytest-asyncio
- Mock-based testing to prevent side effects
- Automatic configuration fallback for missing files
- Enhanced MockClient with built-in guild and channel lookup

## Code Style Guidelines

### Import Organization

**Follow this exact three-group structure:**

```python
from __future__ import annotations  # Use for forward references

# Standard library imports (alphabetically sorted)
import asyncio
import math
from datetime import datetime, timezone

# Third-party imports (alphabetically sorted)
import discord

# Local imports (sorted by specificity, absolute imports only)
import bot_client
import global_vars
import model.channels
from model.characters import Character
from utils import message_utils, player_utils
```

**Rules:**

- Include `from __future__ import annotations` in files with forward references
- Three distinct groups with blank lines between them
- Alphabetical sorting within each group
- **Always use absolute imports** - never relative imports
- Prefer module imports over direct function imports for clarity
- **Never use wildcard imports** (`from module import *`)

### Type Hints

**Comprehensive type annotation is required:**

```python
# Function parameters and return types always annotated
def find_player_by_nick(nick: str) -> model.player.Player | None:
  """Find a player by display name."""


# Class attributes with type hints
class Player:
  character: Character
  alignment: str
  user: discord.Member
  st_channel: discord.TextChannel | None
  position: int | None
  is_ghost: bool


# Complex function signatures
async def safe_send(
        channel: discord.abc.Messageable | discord.Member | discord.User,
        content: str | None = None,
        **kwargs
) -> discord.Message | None:


# TypedDict for structured dictionaries
class MessageDict(TypedDict):
  from_player: 'Player'
  to_player: 'Player'
  content: str
  day: int
```

**Type hint patterns:**

- Use modern Python 3.10+ union syntax: `str | None` not `Optional[str]`
- Use built-in generics: `list[str]` not `List[str]`, `dict[str, int]` not `Dict[str, int]`
- Forward references with string quotes: `'Player'` when needed
- TypedDict for complex dictionary structures
- Generic type variables when needed: `T = TypeVar('T')`

### Naming Conventions

**Strict adherence to PEP 8:**

- **Classes:** `PascalCase` (Player, CommandRegistry, ValidationError)
- **Functions/Variables:** `snake_case` (find_player_by_nick, is_ghost, dead_votes)
- **Constants:** `UPPER_SNAKE_CASE` (STORYTELLER_ALIGNMENT, NULL_GAME)
- **Private attributes:** Single underscore prefix (`_is_poisoned`, `_vote_lock`)
- **Module names:** `snake_case` (player_utils, message_utils, time_utils)

### Code Formatting

**Line length and structure:**

- Maximum line length: **100-110 characters**
- Break long parameter lists across multiple lines with proper indentation
- Break complex expressions for readability

```python
# Good: Long parameter lists broken across lines
@registry.command(
  name="kill",
  description="Kill a player (make them a ghost)",
  help_sections=[HelpSection.COMMON],
  user_types=[UserType.STORYTELLER],
  arguments=[CommandArgument("player")],
  required_phases=[GamePhase.DAY, GamePhase.NIGHT]
)

# Good: Long function calls with proper indentation


announcement = await message_utils.safe_send(
  global_vars.channel,
  f"{player.user.mention} has died."
)
```

### Error Handling

**Use specific exceptions with meaningful context:**

```python
try:
  choice = await bot_client.client.wait_for(
    "message",
    check=(lambda x: x.author == user and x.channel == msg.channel),
    timeout=200,
  )
except asyncio.TimeoutError:
  await message_utils.safe_send(user, "Message timed out!")
  return
except discord.HTTPException as e:
  bot_client.logger.error(f"Failed to send message: {e}")
  return None
```

**Patterns:**

- Catch **specific exception types**, never bare `except:`
- Provide **user-friendly error messages**
- Include **appropriate logging** with context for debugging
- Use **graceful degradation** with appropriate return values
- Document expected exceptions in docstrings

### Documentation

**Use Google-style docstrings consistently:**

```python
def kill(self, suppress: bool = False, force: bool = False) -> bool:
  """Kill the player.
  
  Args:
      suppress: Whether to suppress death announcement
      force: Whether to force the kill even if death modifiers would prevent it
      
  Returns:
      Whether the player dies
      
  Raises:
      ValidationError: If player cannot be killed
  """
```

**Required sections:**

- One-line summary
- `Args:` section with parameter descriptions
- `Returns:` section describing return value
- `Raises:` section for exceptions (when applicable)
- `Example:` section for complex functions (when helpful)

### Comments

**Use strategic inline and block comments:**

```python
self.dead_votes = 0  # Number of dead votes the player has
await self.user.add_roles(global_vars.ghost_role, global_vars.dead_vote_role)

# Cancel if user chooses to abort
if choice.content.lower() == "cancel":
  await message_utils.safe_send(user, "Action cancelled!")
  return

# Complex logic requires block comment explanation
# Check for vote modifiers in seating order - order matters for multiple modifiers
for person in global_vars.game.seatingOrder:
  if isinstance(person.character, model.characters.VoteModifier):
    dies, tie = person.character.on_vote_conclusion(dies, tie)
```

### Function and Class Organization

**Organize methods in logical order:**

```python
class Player:
  # 1. Constructor
  def __init__(self, character_class: type, alignment: str, ...):

  # 2. Special methods (serialization, etc.)
  def __getstate__(self) -> dict[str, Any]:

    def __setstate__(self, state: dict[str, Any]) -> None:

  # 3. Core public methods (main functionality)
  async def morning(self) -> None:

    async def kill(self, suppress: bool = False, force: bool = False) -> bool:

    async def execute(self, user: discord.Member, force: bool = False) -> None:

  # 4. Utility/helper methods
  def update_last_active(self) -> None:

    async def add_dead_vote(self) -> None:

  # 5. Private methods last
  def _some_private_method(self) -> None:
```

### Async/Await Patterns

**Consistent async patterns throughout:**

```python
# Always use async def for coroutines
async def kill(self, suppress: bool = False, force: bool = False) -> bool:


# Await async calls properly
announcement = await message_utils.safe_send(
  global_vars.channel,
  f"{self.user.mention} has died."
)

# Use asyncio.create_task() for fire-and-forget operations
asyncio.create_task(global_vars.game.update_seating_order_message())

# Handle async in exception contexts
try:
  await some_async_operation()
except SomeException:
  await cleanup_operation()
```

## Message Sending

- **Never import `safe_send` directly.**  
  Always use `message_utils.safe_send` when calling or importing this function.  
  This ensures that patching `safe_send` in tests (e.g., with `patch('utils.message_utils.safe_send')`) works
  consistently across the codebase.
