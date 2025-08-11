# UIR Framework Scripts

This directory contains utility scripts for development, testing, and operations.

## Available Scripts

### `test_runner.py`
Comprehensive test runner with detailed reporting and configuration options.

```bash
python scripts/test_runner.py
```

Features:
- Runs full test suite with coverage reporting
- Generates HTML coverage reports
- Supports test filtering and parallel execution
- Includes performance benchmarks

### `test_with_mocks.py`
Test runner specifically designed for mock-based testing without external dependencies.

```bash
python scripts/test_with_mocks.py
```

Features:
- Runs tests using comprehensive mock implementations
- No external API keys or services required
- Ideal for CI/CD environments
- Fast execution with deterministic results

## Usage in Development

These scripts are designed to be run from the project root directory:

```bash
# Run comprehensive tests
python scripts/test_runner.py

# Run mock-only tests (no external dependencies)
python scripts/test_with_mocks.py

# Run specific test categories
python scripts/test_runner.py --category unit
python scripts/test_runner.py --category integration
```

## CI/CD Integration

For automated testing in CI/CD pipelines, use the mock-based test runner:

```yaml
# Example GitHub Actions workflow
- name: Run tests
  run: python scripts/test_with_mocks.py
```