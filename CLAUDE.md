# BOTC-Bot Development Guide

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