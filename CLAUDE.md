# BOTC-Bot Development Guide

## Environment Setup
```bash
# Always use the project's virtual environment
# The venv directory is in the project root
/Users/dlorant/IdeaProjects/botc-bot/venv/bin/python -m <command>

# For convenience, you can activate the virtual environment
source /Users/dlorant/IdeaProjects/botc-bot/venv/bin/activate
# Then you can simply use python without the full path
python -m <command>
```

## Test Commands
```bash
# Run all tests
python -m pytest

# Run specific test file
python -m pytest time_utils/tests/test_time_utils.py

# Run specific test class
python -m pytest time_utils/tests/test_time_utils.py::TestParseDeadline

# Run specific test method
python -m pytest time_utils/tests/test_time_utils.py::TestParseDeadline::test_unix_timestamp

# Run with verbose output
python -m pytest -v
```

## Project Organization

### Directories
- `model/` - Core data models and game entities
  - `model/player.py` - Player class definition
  - `model/characters/` - Character classes and abilities
  - `model/settings/` - Game and global settings
  - `model/channels/` - Channel management
- `utils/` - Utility functions and helpers
- `time_utils/` - Time-related utilities
- `tests/` - Test directories within each module

### Character Structure
- All character classes are in `model/characters/`
- Base classes are in `model/characters/base.py`
- Specific character implementations are in `model/characters/specific.py`
- Character registry for str-to-class conversion is in `model/characters/registry.py`

## Code Style Guidelines

### Imports
- Group imports: standard library, third-party, local/project
- Sort imports alphabetically within groups
- Use absolute imports rather than relative
- Avoid wildcard imports (`from module import *`)

### Type Hints
- Use type annotations for function parameters and return values
- Import annotations from `typing` module (Optional, List, Dict, etc.)
- Consider using a type checker like mypy

### Naming Conventions
- Classes: PascalCase
- Functions/variables/methods: snake_case
- Constants: UPPER_SNAKE_CASE
- Private attributes/methods: prefix with underscore (_method_name)

### Error Handling
- Use specific exceptions rather than generic ones
- Log exceptions with appropriate context
- Document expected exceptions in docstrings
- Avoid bare except clauses

### Documentation
- Use descriptive docstrings (Google or NumPy style)
- Document parameters, return values, and raised exceptions
- Include examples for complex functions