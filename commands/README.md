# Enhanced Command Registry System

This directory contains the enhanced command registry system that extends the existing command functionality to support
structured help messages and better organization.

## Overview

The enhanced system provides:

- **Structured Help Information**: Commands can include descriptions and categorization
- **Automated User Type Validation**: Commands are automatically restricted to specific user types (storyteller, player,
  observer, public)
- **Automated Game Phase Validation**: Commands can require specific game phases (day, night, or any active game)
- **Help Section Organization**: Commands are organized into logical sections (common, progression, day, etc.)
- **Automatic Help Generation**: Dynamic help embeds generated from registered command metadata
- **Strict Type Safety**: Dictionary-based descriptions and arguments must exactly match specified user types
- **Consistent Error Messages**: Standardized permission denied messages with specific role requirements

## Core Components

### `command_enums.py`

Defines enums for organizing commands:

- `HelpSection`: Categories like COMMON, PROGRESSION, DAY, GAMESTATE, CONFIGURE, INFO, MISC, PLAYER
- `UserType`: STORYTELLER, PLAYER, OBSERVER, PUBLIC (for regular server members)
- `GamePhase`: DAY, NIGHT (for phase-specific commands)

### `registry.py`

Enhanced command registry with:

- `CommandInfo`: Stores command metadata (name, handler, description, help sections, user types, aliases, arguments,
  required phases)
- `CommandRegistry`: Manages command registration and lookup with automated validation
- Enhanced `@registry.command` decorator with validation parameters
- **Automated User Type Validation**: `validate_user_type()` automatically checks permissions with consistent error
  messages
- **Automated Game Phase Validation**: `validate_game_phase()` automatically enforces phase requirements
- **ValidationError Exception**: Standardized exception handling for validation failures
- **Strict user type validation**: Dictionary descriptions/arguments must exactly match user_types (no fallback)

### `help_commands.py`

Comprehensive help system combining both the help command and help generation functionality:

**HelpGenerator class:**

- `HelpGenerator.create_storyteller_help_embed()`: Storyteller main help menu
- `HelpGenerator.create_section_help_embed()`: Section-specific help with registry + hardcoded integration
- `HelpGenerator.create_player_help_embed()`: Player command help with integration

**help_command function:**

- Streamlined help command registered with the command registry
- Uses `HelpGenerator` for all embed creation
- **Primary help system** integrated with the command registry
- Automatically includes commands from the registry alongside existing help text

## Usage

### Registering Commands with Help Information

```python
from commands.registry import registry, CommandArgument
from commands.command_enums import HelpSection, UserType

@registry.command(
   name="startgame",
   user_types=[UserType.STORYTELLER],
   description="Starts the game",
   help_sections=[HelpSection.COMMON, HelpSection.PROGRESSION],
   required_phases=[]  # No game needed
)
async def startgame_command(message: discord.Message, argument: str):
   # Command implementation
   pass


# Example with role-specific descriptions and arguments
@registry.command(
   name="vote",
   user_types=[UserType.STORYTELLER, UserType.PLAYER],
   arguments={
      UserType.PLAYER: [CommandArgument(("yes", "no"))],
      UserType.STORYTELLER: [CommandArgument("player"), CommandArgument(("yes", "no"))],
   },
   description={
       UserType.PLAYER: "Vote yes/no on the current nomination",
       UserType.STORYTELLER: "Process votes on the current nomination",
   },
   help_sections=[HelpSection.PLAYER, HelpSection.DAY],
   required_phases=[GamePhase.DAY]  # Day only command
)
async def vote_command(message: discord.Message, argument: str):
   # Command implementation
   pass


# Example with game phase validation
@registry.command(
   name="endday",
   user_types=[UserType.STORYTELLER],
   description="End the current day and proceed to night",
   help_sections=[HelpSection.PROGRESSION],
   required_phases=[GamePhase.DAY]  # Must be day to end day
)
async def endday_command(message: discord.Message, argument: str):
   # Command implementation
   pass
```

### Querying Commands by Category

```python
from commands.registry import registry
from commands.command_enums import HelpSection, UserType

# Get all commands in the COMMON section for storytellers
common_commands = registry.get_commands_by_section(HelpSection.COMMON)

# Get all commands available to players
player_commands = registry.get_commands_by_user_type(UserType.PLAYER)
```

## Automated Validation System

The registry provides automatic validation for user permissions and game phases:

### User Type Validation

Commands are automatically restricted to specified user types. When a user lacks permission:

```python
# User tries to use storyteller-only command
# System automatically responds: "You do not have permission to use the startgame command. Allowed role(s): Storyteller."
```

**User Types:**

- `STORYTELLER`: Users with gamemaster role
- `PLAYER`: Users currently in the game's seating order
- `OBSERVER`: Users with observer role
- `PUBLIC`: Regular server members (not storyteller/player/observer)

### Game Phase Validation

Commands can require specific game phases. Invalid phase usage triggers automatic error messages:

```python
# Example: Using day-only command at night
# System automatically responds: "It's not day right now."

# Example: Using command when no game exists  
# System automatically responds: "There's no game right now."
```

**Game Phases:**

- `[]` (empty): No game required
- `[GamePhase.DAY]`: Day phase only
- `[GamePhase.NIGHT]`: Night phase only
- `[GamePhase.DAY, GamePhase.NIGHT]`: Any active game phase

### Validation Parameters

```python
@registry.command(
    name="execute",
    user_types=[UserType.STORYTELLER],          # Who can use it
    required_phases=[GamePhase.DAY],             # When it can be used
    description="Execute a player",
    help_sections=[HelpSection.PROGRESSION]
)
async def execute_command(message: discord.Message, argument: str):
    # No manual permission checking needed - registry handles it automatically
    pass
```

### Error Messages

The system provides consistent error messages:

- **Permission Denied**: `"You do not have permission to use the {command} command. Allowed role(s): {roles}."`
- **Wrong Phase**: `"It's not day right now."` / `"It's not night right now."`
- **No Game**: `"There's no game right now."`

### Generating Help Embeds

```python
from commands.help_commands import HelpGenerator
from commands.command_enums import HelpSection, UserType

# Create main help menu for storytellers
help_embed = HelpGenerator.create_storyteller_help_embed()

# Create section-specific help
section_embed = HelpGenerator.create_section_help_embed(
   HelpSection.COMMON,
   UserType.STORYTELLER
)
```

## Integrated Help System

The help command has been extracted from `bot_impl.py` and integrated with the registry system:

### Features

- **Automatic Integration**: Registry commands automatically appear in help output
- **Hybrid Approach**: Combines new registry commands with existing hardcoded help text
- **Seamless Experience**: Users see a unified help system regardless of implementation
- **No Duplication**: Registry commands take precedence, preventing duplicate help entries

### How It Works

1. **Registry Commands First**: Each help section checks the registry for relevant commands
2. **Hardcoded Integration**: Existing commands are mapped to sections in `HelpGenerator`
3. **Deduplication**: Commands only appear once, with registry taking precedence over hardcoded
4. **Role-Based Filtering**: Shows appropriate commands based on user's storyteller/player role
5. **Centralized Logic**: All embed generation happens in `HelpGenerator` to eliminate duplication

## Migration Strategy: Skeleton Registration

The enhanced system uses a **skeleton registration strategy** for safe gradual migration:

1. **Complete Skeleton Registration**: All bot commands registered with `implemented=False`
2. **Safe Fallback**: Registry checks `implemented` flag, falls back to `bot_impl.py` for actual execution
3. **Zero Risk Migration**: Bot functionality unchanged while structure is established
4. **Gradual Implementation**: Individual commands migrated by setting `implemented=True`
5. **Complete Metadata**: All commands have help sections, user types, and arguments defined

### Current State (Skeleton Registration)

**Registry Registration** (in command files):
```python
@registry.command(
    name="startgame",
   description="Start a new game",
   help_sections=[HelpSection.COMMON],
   user_types=[UserType.STORYTELLER],
   required_phases=[],  # No game needed
   implemented=False  # Falls back to bot_impl.py
)
async def startgame_command(message: discord.Message, argument: str):
   """Start a new game."""
   raise NotImplementedError("Registry implementation not ready - using bot_impl")
```

**Implementation** (still in `bot_impl.py`):

```python
elif command == "startgame":
    # Actual implementation remains here until migrated
    pass
```

### Future Migration Example

To migrate a command, simply:

1. Copy implementation from `bot_impl.py` to registry command file
2. Change `implemented=False` to `implemented=True`
3. Remove the `raise NotImplementedError` line
4. Test thoroughly

## Help System Integration

The enhanced system provides structured data that can replace the hard-coded help text in `bot_impl.py`:

**Current Help System**: Hard-coded strings in if/elif blocks
**Enhanced Help System**: Dynamic generation from command metadata

### Help Categories Mapping

The system maps to the existing help categories:

- **help common** → `HelpSection.COMMON`
- **help progression** → `HelpSection.PROGRESSION`
- **help day** → `HelpSection.DAY`
- **help gamestate** → `HelpSection.GAMESTATE`
- **help configure** → `HelpSection.CONFIGURE`
- **help info** → `HelpSection.INFO`
- **help misc** → `HelpSection.MISC`
- **help player** → `HelpSection.PLAYER`

## Testing

The system includes comprehensive tests:

- `test_help_system.py`: Enum validation, command registration, help embed generation
- `test_registry_user_types.py`: **Strict user type validation enforcement**
- `test_enum_enforcement.py`: **Automated validation testing for user types and game phases**
- `test_integrated_help.py`: Integration testing of help command
- `test_debug_commands_registry.py`: Registry-based command testing

**Validation Testing**: The system includes thorough testing of the automated validation:

- **User Type Validation**: Tests permission enforcement and error messages for all user types
- **Game Phase Validation**: Tests phase restrictions and appropriate error responses
- **Error Message Consistency**: Validates standardized error message format
- **Permission Partitioning**: Ensures user types (storyteller/player/observer/public) are mutually exclusive

**Type Safety Testing**: The system enforces strict user type consistency:

- Dictionary descriptions must contain exactly the same user types as `user_types`
- Dictionary arguments must contain exactly the same user types as `user_types`
- No fallback behavior exists - missing user types raise KeyError

Run tests with:

```bash
python -m pytest tests/commands/ -v
```

## Future Enhancements
 
- **Interactive Help**: Reaction-based help navigation

## File Structure

```
commands/
├── __init__.py
├── README.md                        # This file
├── COMMAND_OVERVIEW.md              # Complete command documentation
├── EXTRACTION_PLAN.md               # Migration strategy documentation
├── command_enums.py                 # Enums for command registry (HelpSection, UserType, GamePhase)
├── registry.py                      # Enhanced command registry with implemented flag
├── help_commands.py                 # Integrated help system (command + generation)
├── loader.py                        # Command module loader (imports all command files)
├── debug_commands.py                # Sample commands with help metadata
├── utility_commands.py              # Utility and miscellaneous commands
├── information_commands.py          # Game status and player information commands
├── game_management_commands.py      # Game state and configuration commands
├── player_management_commands.py    # Player state management commands
├── voting_commands.py               # Voting and nomination commands
└── communication_commands.py        # PM and communication control commands
```

## Usage in Production

The integrated help system is now active. To use it:

1. **For New Commands**: Use the registry system with help metadata:
   ```python
   @registry.command(
       name="mycommand",
       description="Does something useful",
       help_sections=[HelpSection.MISC],
       user_types=[UserType.STORYTELLER]
   )
   async def my_command(message, argument):
       pass
   ```

2. **Help Command**: The `@help` command automatically includes registry commands alongside existing help text.

3. **Testing**: All functionality is tested in `tests/commands/test_integrated_help.py`.