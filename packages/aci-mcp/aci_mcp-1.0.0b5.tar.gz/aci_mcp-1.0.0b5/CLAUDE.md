# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build/Lint/Test Commands
- Build: `python -m build`
- Lint: `ruff .`
- Type check: `pyright`
- Test: `pytest` (run a single test with `pytest path/to/test.py::test_function`)

## Code Style Guidelines
- Line length: 100 characters
- Python 3.10+ required
- Use type annotations for all functions and class attributes
- Use snake_case for functions, variables, and parameters
- Use PascalCase for classes
- Use UPPERCASE for constants
- Import order: standard library, third-party, local modules
- Docstrings: use triple double-quotes with concise descriptions
- Error handling: use explicit try/except blocks with meaningful error messages
- CLI: built with click, include help text for all options
- Return values should be typed and consistent

## Development Dependencies
- Uses ruff (0.11.0+) for linting
- Uses pyright (1.1.396+) for type checking
- Uses pytest (8.3.5+) for testing