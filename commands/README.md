# Enhanced Command Registry System

This directory contains the enhanced command registry system that extends the existing command functionality to support
structured help messages and better organization.

## Overview

The enhanced system provides:

- **Structured Help Information**: Commands can include descriptions and categorization
- **User Type Filtering**: Commands can be restricted to specific user types (storyteller, player, all)
- **Help Section Organization**: Commands are organized into logical sections (common, progression, day, etc.)
- **Automatic Help Generation**: Dynamic help embeds generated from registered command metadata

## Core Components

### `command_enums.py`

Defines enums for organizing commands:

- `HelpSection`: Categories like COMMON, PROGRESSION, DAY, GAMESTATE, CONFIGURE, INFO, MISC, PLAYER
- `UserType`: STORYTELLER, PLAYER, ALL

### `registry.py`

Enhanced command registry with:

- `CommandInfo`: Stores command metadata (name, handler, description, help sections, user types, aliases)
- `CommandRegistry`: Manages command registration and lookup with help support
- Enhanced `@registry.command` decorator with help parameters

### `help_commands.py`

Comprehensive help system combining both the help command and help generation functionality:

**HelpGenerator class:**

- `HelpGenerator.create_storyteller_help_embed()`: Storyteller main help menu
- `HelpGenerator.create_section_help_embed()`: Section-specific help with registry + hardcoded integration
- `HelpGenerator.create_player_help_embed()`: Player command help with integration
- `HelpGenerator._get_hardcoded_commands_for_section()`: Maps hardcoded commands to sections

**help_command function:**

- Streamlined help command registered with the command registry
- Uses `HelpGenerator` for all embed creation
- **Primary help system** integrated with the command registry
- Automatically includes commands from the registry alongside existing help text

### `help_command_example.py`

Example implementation showing how the existing help command in `bot_impl.py` could be refactored to use the new system.

## Usage

### Registering Commands with Help Information

```python
from commands.registry import registry
from commands.command_enums import HelpSection, UserType


@registry.command(
   name="startgame",
   description="Starts the game",
   help_sections=[HelpSection.COMMON, HelpSection.PROGRESSION],
   user_types=[UserType.STORYTELLER]
)
async def startgame_command(message: discord.Message, argument: str):
   # Command implementation
   pass


# Example with role-specific descriptions
@registry.command(
   name="vote",
   description={
       UserType.PLAYER: "Vote yes/no on the current nomination",
       UserType.STORYTELLER: "Process votes on the current nomination",
   },
   help_sections=[HelpSection.PLAYER, HelpSection.DAY],
   user_types=[UserType.STORYTELLER, UserType.PLAYER],
   aliases=["v"]
)
async def vote_command(message: discord.Message, argument: str):
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
2. **Hardcoded Integration**: Existing commands are mapped to sections in
   `HelpGenerator._get_hardcoded_commands_for_section()`
3. **Deduplication**: Commands only appear once, with registry taking precedence over hardcoded
4. **Role-Based Filtering**: Shows appropriate commands based on user's storyteller/player role
5. **Centralized Logic**: All embed generation happens in `HelpGenerator` to eliminate duplication

## Migration Path

The enhanced system is designed to work immediately with existing commands:

1. **✅ Complete Integration**: Registry-based help system is now the primary implementation
2. **Gradual Migration**: Commands can be moved from `bot_impl.py` to the registry system incrementally
3. **Backward Compatibility**: Existing hardcoded commands continue to show in help until migrated
4. **Help Integration**: Once commands are registered, the help system automatically includes them

### Example Migration

**Before** (in `bot_impl.py`):

```python
elif command == "startgame":
# Command implementation
pass
```

**After** (in a commands module):

```python
@registry.command(
    name="startgame",
    description="Starts the game",
    help_sections=[HelpSection.COMMON, HelpSection.PROGRESSION],
    user_types=[UserType.STORYTELLER]
)
async def startgame_command(message: discord.Message, argument: str):
    # Same command implementation
    pass
```

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

The system includes comprehensive tests in `test_help_system.py`:

- Enum value validation
- Command registration with help metadata
- Help embed generation
- Section and user type filtering

Run tests with:

```bash
python -m pytest tests/commands/test_help_system.py -v
```

## Future Enhancements

- **Command Aliases**: Support for command aliases with help display
- **Permission Integration**: Integration with Discord permission system
- **Interactive Help**: Reaction-based help navigation
- **Command Usage Stats**: Track command usage for analytics
- **Localization**: Multi-language help support

## File Structure

```
commands/
├── __init__.py
├── README.md              # This file
├── command_enums.py       # Enums for command registry
├── registry.py            # Enhanced command registry
├── help_commands.py       # Integrated help system (command + generation)
├── help_command_example.py # Example help command implementation  
├── debug_commands.py       # Sample commands with help metadata
└── loader.py              # Command module loader
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