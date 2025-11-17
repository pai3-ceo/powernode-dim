# DIM Test Suite

Comprehensive test suite for the DIM (Decentralized Inference Machine) module.

## Quick Start

### Install Test Dependencies

```bash
cd powernode/dim
pip install -r tests/requirements.txt
```

### Run All Tests

```bash
# From powernode/dim directory
pytest tests/
```

### Run Specific Test Categories

```bash
# Unit tests only (fast)
pytest tests/unit/ -m unit

# Integration tests
pytest tests/integration/ -m integration

# End-to-end tests
pytest tests/e2e/ -m e2e

# Performance tests
pytest tests/performance/ -m performance

# Security tests
pytest tests/security/ -m security
```

### Run with Coverage

```bash
pytest tests/ --cov=powernode.dim --cov-report=html
```

Coverage report will be in `htmlcov/index.html`

## Test Structure

```
tests/
├── unit/              # Unit tests (fast, isolated)
├── integration/       # Integration tests (component interactions)
├── e2e/              # End-to-end tests (complete workflows)
├── performance/      # Performance and load tests
├── security/         # Security tests (TLS, rate limiting)
└── fixtures/         # Test fixtures and mocks
```

## Test Categories

### Unit Tests
- Individual component testing
- Mocked dependencies
- Fast execution (< 5 minutes)
- Target coverage: 80%+

### Integration Tests
- Component interaction testing
- Real IPFS (test instance)
- Medium execution time (< 15 minutes)

### End-to-End Tests
- Complete workflow testing
- All three patterns
- Real services (local)
- Longer execution time (< 30 minutes)

### Performance Tests
- Load testing
- Stress testing
- Resource usage validation
- Benchmarking

### Security Tests
- TLS verification
- Rate limiting validation
- Input validation
- Authentication (when implemented)

## Writing Tests

### Example Unit Test

```python
import pytest
from unittest.mock import Mock, AsyncMock

@pytest.mark.asyncio
async def test_my_component(test_config):
    """Test description"""
    # Arrange
    component = MyComponent(test_config)
    
    # Act
    result = await component.do_something()
    
    # Assert
    assert result is not None
```

### Example Integration Test

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_component_integration(test_config):
    """Test component integration"""
    # Test with real dependencies
    pass
```

## Test Fixtures

Available fixtures (see `conftest.py`):
- `test_config`: Test configuration
- `sample_job_spec_collaborative`: Sample collaborative job
- `sample_job_spec_comparative`: Sample comparative job
- `sample_job_spec_chained`: Sample chained job
- `sample_node_info`: Sample node information
- `mock_ipfs_client`: Mock IPFS client
- `mock_model_cache`: Mock model cache

## Continuous Integration

Tests should be run:
- **On every commit**: Unit tests
- **On pull requests**: Unit + Integration tests
- **Nightly**: All tests including E2E
- **On releases**: Full test suite + Performance tests

## Test Coverage Goals

- **Overall**: ≥ 70%
- **Critical components**: ≥ 80%
- **Core logic**: ≥ 90%

## Troubleshooting

### Tests Failing

1. Check IPFS is running (for integration tests)
2. Verify test configuration
3. Check for port conflicts
4. Review test logs

### Coverage Issues

1. Run with `--cov-report=term-missing` to see missing lines
2. Add tests for uncovered code paths
3. Review coverage report in `htmlcov/`

## Best Practices

1. **Isolation**: Each test should be independent
2. **Mocking**: Mock external dependencies
3. **Naming**: Use descriptive test names
4. **Documentation**: Document complex test scenarios
5. **Performance**: Keep unit tests fast (< 1 second each)

