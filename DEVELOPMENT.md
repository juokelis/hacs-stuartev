# Development Guide

## Setting Up Development Environment

### Prerequisites
- Python 3.14
- Git

### Installation

1. Clone the repository:
```bash
git clone https://github.com/juokelis/hacs-stuartev.git
cd hacs-stuartev
```

2. Install development dependencies:
```bash
python3 -m pip install -r requirements_dev.txt
```

Or use the setup script:
```bash
./scripts/setup
```

## Requirements Files

### `requirements.txt`
This file is **empty** (with comments only) because this integration has no external dependencies. All required libraries (aiohttp, voluptuous, etc.) are already provided by Home Assistant core.

**Note:** Per Home Assistant best practices, you should NOT list dependencies that are already included in Home Assistant core. Since this integration only uses:
- `homeassistant.helpers.aiohttp_client` (HA's built-in aiohttp wrapper)
- `voluptuous` (HA core dependency)
- Standard Python libraries

...there are no external dependencies to declare.

### `requirements_dev.txt`
Contains dependencies needed for **local development and testing only**:
- `homeassistant` - For local testing
- `ruff` - For code linting and formatting
- `colorlog` - For colored console output during development

### `requirements_test.txt`
Contains dependencies for running tests:
- Inherits from `requirements_dev.txt`
- `pytest` - Testing framework
- `aioresponses` - For mocking async HTTP responses

## Linting

Run linting checks:
```bash
python3 -m ruff check .
```

Auto-fix issues:
```bash
python3 -m ruff check . --fix
```

Check formatting:
```bash
python3 -m ruff format . --check
```

Format code:
```bash
python3 -m ruff format .
```

## Testing

Run tests:
```bash
pytest
```

## Python Version

This project uses **Python 3.14** as configured in:
- `.ruff.toml` - `target-version = "py314"`
- `.github/workflows/lint.yml` - `python-version: "3.14"`
