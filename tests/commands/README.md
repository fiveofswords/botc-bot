# Command Tests

Tests for bot commands:

- **test_player_commands.py** - Player-specific command tests (vote, hand actions, etc.)
- **test_storyteller_commands.py** - Storyteller command tests (game management, player actions)
- **test_settings_functionality.py** - Settings and configuration command tests
- **test_help_system.py** - Enhanced command registry and help system tests
- **test_integrated_help.py** - Integration tests for the new help command
- **test_info_commands_registry.py** - Tests for registry-based commands

## Command System Testing

The command system now includes two approaches:

1. **Legacy Commands**: Tested in existing files (test_player_commands.py, test_storyteller_commands.py)
2. **Registry Commands**: Tested in new files (test_help_system.py, test_integrated_help.py,
   test_info_commands_registry.py)

The registry system provides enhanced help integration and better command organization.

Uses fixtures from `tests/fixtures/` for consistent testing setup.
