# MTG MCP Server Tests

This directory contains unit tests for the MTG MCP Server.

## Test Structure

- `test_utils.py` - Tests for utility functions (rate limiting, caching, API fetching)
- `test_context.py` - Tests for MTG context tools
- `test_rules.py` - Tests for rules tools
- `test_cardtypes.py` - Tests for card types tools
- `test_ruling.py` - Tests for ruling search tools
- `test_combos.py` - Tests for combo search tools
- `test_commander.py` - Tests for commander tools (recommendations, brackets, export format)
- `test_archidekt.py` - Tests for Archidekt deck fetching

## Running Tests

### Install test dependencies

```bash
pip install .[test]
```

### Run all tests

```bash
pytest tests/ -v
```

### Run specific test file

```bash
pytest tests/test_utils.py -v
```

### Run tests with coverage

```bash
pytest tests/ --cov=src --cov-report=html
```

### Run tests for a specific function

```bash
pytest tests/test_utils.py::TestRateLimiting::test_rate_limit_first_call -v
```

## Test Configuration

Tests are configured via `pytest.ini` in the project root. Key settings:

- Tests are automatically discovered in the `tests/` directory
- Async tests are automatically handled via `pytest-asyncio`
- Coverage reports include the `mtg_mcp/` directory

## Writing New Tests

When adding new functionality:

1. Create a test file following the naming convention `test_<module>.py`
2. Organize tests into classes (e.g., `TestMyFeature`)
3. Use descriptive test function names starting with `test_`
4. Mock external API calls and dependencies
5. Use `@pytest.mark.asyncio` decorator for async tests

Example:

```python
import pytest
from unittest.mock import AsyncMock, patch
from src.tools.mymodule import my_function

class TestMyFeature:
    @pytest.mark.asyncio
    async def test_my_function_success(self):
        """Test successful function execution"""
        with patch('src.tools.mymodule.external_api') as mock_api:
            mock_api.return_value = {"result": "success"}
            
            result = await my_function()
            
            assert result["status"] == "success"
```

## CI/CD

Tests are automatically run on:
- Pull requests to `main` branch
- Pushes to `main` branch

See `.github/workflows/test.yml` for the complete CI configuration.
