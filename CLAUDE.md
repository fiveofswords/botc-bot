# BOTC-Bot Development Guide

## Environment Setup
```bash
# Activate the virtual environment
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

## Test Commands
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

## Project Structure

- `model/` - Core game entities (player, characters, settings, channels)
- `utils/` - Utility functions and helpers
- `time_utils/` - Time-related utilities
- `tests/` - Test directory with subdirectories by module

### Character System

- Base classes: `model/characters/base.py`
- Specific implementations: `model/characters/specific.py`
- Character registry: `model/characters/registry.py`

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