# Contributing to UIR Framework

Thank you for your interest in contributing to the Universal Information Retrieval (UIR) Framework! This guide will help you get started with contributing code, documentation, and ideas to make UIR better for everyone.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Contributing Guidelines](#contributing-guidelines)
- [Pull Request Process](#pull-request-process)
- [Issue Guidelines](#issue-guidelines)
- [Development Standards](#development-standards)
- [Testing Requirements](#testing-requirements)
- [Documentation](#documentation)
- [Community](#community)

## Code of Conduct

This project adheres to a code of conduct adapted from the [Contributor Covenant](https://www.contributor-covenant.org/). By participating, you are expected to uphold this code. Please report unacceptable behavior to [conduct@uir-framework.com](mailto:conduct@uir-framework.com).

### Our Pledge

We pledge to make participation in our project a harassment-free experience for everyone, regardless of age, body size, visible or invisible disability, ethnicity, sex characteristics, gender identity and expression, level of experience, education, socio-economic status, nationality, personal appearance, race, religion, or sexual identity and orientation.

## Getting Started

### Ways to Contribute

- **Bug Reports**: Help us identify and fix issues
- **Feature Requests**: Suggest new features or improvements
- **Code Contributions**: Submit bug fixes and new features
- **Documentation**: Improve documentation, examples, and tutorials
- **Testing**: Help expand test coverage and find edge cases
- **Provider Integrations**: Add support for new search providers
- **Performance**: Optimize performance and scalability

### Prerequisites

Before contributing, make sure you have:
- Python 3.9 or higher
- Git
- Docker (for integration testing)
- A GitHub account

## Development Setup

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then clone your fork
git clone https://github.com/your-username/uir-framework.git
cd uir-framework

# Add upstream remote
git remote add upstream https://github.com/uir-framework/uir-framework.git
```

### 2. Set Up Development Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Install the package in development mode
pip install -e .
```

### 3. Environment Configuration

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your configuration
# For development, you can use mock mode:
echo "MOCK_MODE=true" >> .env
```

### 4. Run Tests

```bash
# Run all tests
pytest tests/ -v

# Run tests with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test categories
pytest tests/test_providers/ -v
pytest tests/test_core/ -v

# Run with mocks (no external dependencies)
python test_with_mocks.py
```

### 5. Start Development Server

```bash
# Start the API server
uvicorn src.uir.api.main:app --reload --host 0.0.0.0 --port 8000

# Or use Docker Compose for full stack
docker-compose -f docker-compose.dev.yml up -d
```

## Contributing Guidelines

### Branch Strategy

We use a modified Git Flow strategy:

- **main**: Production-ready code
- **develop**: Integration branch for features
- **feature/\***: New features and enhancements
- **bugfix/\***: Bug fixes
- **hotfix/\***: Critical production fixes
- **docs/\***: Documentation updates

### Naming Conventions

#### Branch Names
- `feature/add-provider-openai`
- `bugfix/fix-rate-limiting-edge-case`
- `docs/update-api-examples`
- `hotfix/security-vulnerability-fix`

#### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
type(scope): description

[optional body]

[optional footer(s)]
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples**:
```
feat(providers): add OpenAI provider integration

- Add OpenAI provider adapter with chat completions support
- Implement rate limiting and error handling
- Add comprehensive tests and documentation

Closes #123
```

```
fix(auth): resolve JWT token expiration issue

The token expiration check was using incorrect timezone
causing premature token invalidation.

Fixes #456
```

## Pull Request Process

### Before Submitting

1. **Sync with upstream**:
   ```bash
   git fetch upstream
   git checkout develop
   git merge upstream/develop
   ```

2. **Create feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**:
   - Write clean, documented code
   - Add tests for new functionality
   - Update documentation as needed
   - Ensure all tests pass

4. **Commit your changes**:
   ```bash
   git add .
   git commit -m "feat(scope): your descriptive message"
   ```

5. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

### Pull Request Template

When creating a PR, please use this template:

```markdown
## Description
Brief description of the changes and why they're needed.

## Type of Change
- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to change)
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing performed
- [ ] All tests pass

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Code is documented
- [ ] Breaking changes are documented
- [ ] Tests added for new functionality

## Screenshots (if applicable)
Add screenshots for UI changes or visual features.

## Related Issues
Closes #(issue_number)
```

### Review Process

1. **Automated Checks**: CI/CD pipeline runs automatically
2. **Code Review**: Maintainers review your code
3. **Discussion**: Address feedback and questions
4. **Approval**: PR approved by maintainers
5. **Merge**: PR merged to develop branch

## Issue Guidelines

### Before Opening an Issue

1. **Search existing issues** to avoid duplicates
2. **Check documentation** for known solutions
3. **Test with latest version** to ensure issue still exists

### Bug Reports

Use the bug report template:

```markdown
## Bug Description
A clear description of what the bug is.

## Steps to Reproduce
1. Go to '...'
2. Click on '...'
3. Scroll down to '...'
4. See error

## Expected Behavior
What you expected to happen.

## Actual Behavior
What actually happened.

## Environment
- OS: [e.g., Ubuntu 20.04]
- Python version: [e.g., 3.9.7]
- UIR Framework version: [e.g., 1.0.0]
- Provider: [e.g., Google, Pinecone]

## Additional Context
Add any other context about the problem.
```

### Feature Requests

Use the feature request template:

```markdown
## Feature Description
A clear description of the feature you'd like to see.

## Use Case
Describe your use case and how this feature would help.

## Proposed Solution
If you have ideas for implementation, describe them here.

## Alternatives Considered
Other solutions you've considered.

## Additional Context
Any additional context or screenshots.
```

## Development Standards

### Code Style

We follow PEP 8 with some modifications:

```python
# Use type hints
def search_provider(
    provider: str, 
    query: str, 
    options: Optional[Dict[str, Any]] = None
) -> List[SearchResult]:
    """Search using specified provider."""
    pass

# Use docstrings for all public functions
def process_query(query: str) -> ProcessedQuery:
    """
    Process and enhance user query.
    
    Args:
        query: Raw user query string
        
    Returns:
        ProcessedQuery with enhancements
        
    Raises:
        ValidationError: If query is invalid
    """
    pass

# Use descriptive variable names
search_results = []
provider_config = get_provider_config(provider_name)
```

### Code Quality Tools

We use several tools to maintain code quality:

```bash
# Auto-formatting
black src/ tests/
isort src/ tests/

# Linting
flake8 src/ tests/
pylint src/

# Type checking
mypy src/

# Security scanning
bandit -r src/

# All checks (run by pre-commit)
pre-commit run --all-files
```

### Architecture Guidelines

#### Adding New Providers

1. **Create Provider Adapter**:
   ```python
   # src/uir/providers/new_provider.py
   from uir.core.adapter import ProviderAdapter
   
   class NewProviderAdapter(ProviderAdapter):
       """Adapter for NewProvider API"""
       
       async def search(self, query: str, options: Dict) -> List[SearchResult]:
           """Implement search functionality"""
           pass
   ```

2. **Register Provider**:
   ```python
   # src/uir/providers/__init__.py
   from .new_provider import NewProviderAdapter
   
   __all__ = [..., "NewProviderAdapter"]
   ```

3. **Add Configuration**:
   ```yaml
   # config/providers.yaml
   new_provider:
     enabled: true
     type: "search_engine"
     auth_method: "api_key"
     # ... configuration
   ```

4. **Write Tests**:
   ```python
   # tests/test_providers/test_new_provider.py
   class TestNewProviderAdapter:
       def test_search_basic(self):
           """Test basic search functionality"""
           pass
   ```

#### Component Design Principles

1. **Single Responsibility**: Each component has one clear purpose
2. **Dependency Injection**: Inject dependencies for testability
3. **Interface Segregation**: Use specific interfaces, not fat ones
4. **Error Handling**: Graceful error handling with proper logging
5. **Async/Await**: Use async patterns for I/O operations

## Testing Requirements

### Test Categories

1. **Unit Tests**: Test individual components in isolation
2. **Integration Tests**: Test component interactions
3. **End-to-End Tests**: Test complete workflows
4. **Performance Tests**: Test scalability and performance
5. **Security Tests**: Test security vulnerabilities

### Writing Tests

```python
# Unit test example
import pytest
from unittest.mock import AsyncMock, MagicMock

class TestQueryProcessor:
    @pytest.fixture
    def query_processor(self):
        """Create query processor with mocked dependencies"""
        return QueryProcessor(
            embedding_service=AsyncMock(),
            spell_checker=MagicMock(),
            entity_extractor=MagicMock()
        )
    
    @pytest.mark.asyncio
    async def test_process_basic_query(self, query_processor):
        """Test basic query processing"""
        result = await query_processor.process("machine learning")
        
        assert result.original == "machine learning"
        assert result.corrected is not None
        assert len(result.keywords) > 0
```

### Test Coverage Requirements

- **Minimum Coverage**: 80% overall
- **New Code Coverage**: 90% for new features
- **Critical Paths**: 95% for security and core functionality

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html --cov-report=term

# Run specific test file
pytest tests/test_providers/test_google.py -v

# Run tests matching pattern
pytest tests/ -k "test_search" -v

# Run tests with markers
pytest tests/ -m "integration" -v

# Run tests in parallel
pytest tests/ -n auto
```

## Documentation

### Documentation Standards

1. **Code Documentation**: All public APIs must have docstrings
2. **Architecture Documentation**: Keep architecture docs updated
3. **API Documentation**: OpenAPI/Swagger specs must be current
4. **Examples**: Provide working examples for features
5. **Changelog**: Document all changes in CHANGELOG.md

### Writing Documentation

```python
def search_multiple_providers(
    providers: List[str],
    query: str,
    fusion_method: str = "reciprocal_rank"
) -> SearchResponse:
    """
    Search across multiple providers and fuse results.
    
    This function executes searches across multiple providers in parallel
    and combines the results using the specified fusion method.
    
    Args:
        providers: List of provider names to search
        query: Search query string
        fusion_method: Method to combine results ("reciprocal_rank", 
                      "weighted_sum", or "max_score")
    
    Returns:
        SearchResponse containing fused results from all providers
        
    Raises:
        ValueError: If fusion_method is not supported
        ProviderError: If all providers fail
        
    Example:
        >>> response = search_multiple_providers(
        ...     providers=["google", "bing"],
        ...     query="machine learning",
        ...     fusion_method="reciprocal_rank"
        ... )
        >>> print(f"Found {len(response.results)} results")
        Found 15 results
    """
    pass
```

### Building Documentation

```bash
# Install documentation dependencies
pip install -r docs/requirements.txt

# Build documentation
cd docs/
make html

# Serve documentation locally
make serve

# Check for broken links
make linkcheck
```

## Community

### Communication Channels

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and discussions
- **Discord**: Real-time chat and community support
- **Email**: [community@uir-framework.com](mailto:community@uir-framework.com)

### Getting Help

1. **Documentation**: Check the [official documentation](https://docs.uir-framework.com)
2. **Examples**: Browse the [examples repository](https://github.com/uir-framework/examples)
3. **Stack Overflow**: Tag questions with `uir-framework`
4. **Community Forum**: Post in [GitHub Discussions](https://github.com/uir-framework/uir/discussions)

### Recognition

We recognize contributors in several ways:

- **Contributors Page**: Listed on the project website
- **Changelog**: Credited for significant contributions
- **Hall of Fame**: Special recognition for major contributions
- **Swag**: UIR Framework swag for active contributors

## Release Process

### Versioning

We follow [Semantic Versioning](https://semver.org/):

- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Workflow

1. **Feature Freeze**: No new features for release candidate
2. **Testing**: Comprehensive testing across environments
3. **Documentation**: Update docs and changelog
4. **Release Candidate**: Deploy to staging for final testing
5. **Release**: Tag and deploy to production
6. **Announcement**: Announce release to community

## Security

### Reporting Security Vulnerabilities

Please report security vulnerabilities to [security@uir-framework.com](mailto:security@uir-framework.com). Do not create public issues for security vulnerabilities.

### Security Guidelines

1. **Input Validation**: Validate all inputs
2. **Output Encoding**: Encode outputs to prevent XSS
3. **Authentication**: Use secure authentication methods
4. **Authorization**: Implement proper access controls
5. **Logging**: Log security-relevant events
6. **Dependencies**: Keep dependencies updated

## License

By contributing to the UIR Framework, you agree that your contributions will be licensed under the project's [MIT License](LICENSE).

---

Thank you for contributing to the UIR Framework! Your contributions help make information retrieval accessible and powerful for developers worldwide. 🚀