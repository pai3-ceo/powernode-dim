# DIM Testing Guide

Complete guide for running and writing tests for the DIM module.

## Quick Start

### Setup Test Environment

```bash
cd powernode/dim
./tests/scripts/setup-test-env.sh
```

### Run Tests

```bash
# All tests
./tests/scripts/run-tests.sh all

# Specific category
./tests/scripts/run-tests.sh unit
./tests/scripts/run-tests.sh integration
./tests/scripts/run-tests.sh e2e
```

## Test Organization

### Unit Tests (`tests/unit/`)
- Fast, isolated component tests
- Mocked dependencies
- Target: < 5 minutes total

### Integration Tests (`tests/integration/`)
- Component interaction tests
- Real IPFS (test instance)
- Target: < 15 minutes total

### End-to-End Tests (`tests/e2e/`)
- Complete workflow tests
- Real services (local)
- Target: < 30 minutes total

### Performance Tests (`tests/performance/`)
- Load and stress tests
- Benchmarking
- Target: Validate performance requirements

### Security Tests (`tests/security/`)
- TLS, rate limiting, validation
- Target: Security feature validation

## Writing Tests

### Test Structure

```python
import pytest
from unittest.mock import Mock, AsyncMock

@pytest.mark.asyncio
async def test_my_feature(test_config):
    """Test description"""
    # Arrange
    component = MyComponent(test_config)
    
    # Act
    result = await component.do_something()
    
    # Assert
    assert result is not None
```

### Using Fixtures

```python
@pytest.mark.asyncio
async def test_with_fixtures(test_config, sample_job_spec_collaborative):
    """Test using fixtures"""
    spec = JobSpec(**sample_job_spec_collaborative)
    # Use spec in test
```

### Mocking

```python
with patch.object(component, 'method', new_callable=AsyncMock) as mock_method:
    mock_method.return_value = 'expected_result'
    result = await component.call_method()
    mock_method.assert_called_once()
```

## Test Markers

Use markers to categorize tests:

- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.e2e` - End-to-end tests
- `@pytest.mark.performance` - Performance tests
- `@pytest.mark.security` - Security tests
- `@pytest.mark.slow` - Slow running tests

## Coverage

### Running Coverage

```bash
pytest tests/ --cov=powernode.dim --cov-report=html
```

### Coverage Goals

- Overall: ≥ 70%
- Critical components: ≥ 80%
- Core logic: ≥ 90%

## Continuous Integration

Tests run automatically:
- **On commit**: Unit tests
- **On PR**: Unit + Integration
- **Nightly**: All tests
- **On release**: Full suite + Performance

## Troubleshooting

### Common Issues

1. **Import errors**: Check PYTHONPATH
2. **IPFS errors**: Ensure IPFS test instance running
3. **Port conflicts**: Use different ports in test config
4. **Async errors**: Use `pytest.mark.asyncio`

### Debug Mode

```bash
pytest tests/ -v -s  # Verbose with output
pytest tests/ --pdb  # Drop into debugger on failure
```

## Best Practices

1. **Isolation**: Each test independent
2. **Speed**: Keep unit tests fast
3. **Clarity**: Use descriptive names
4. **Coverage**: Test edge cases
5. **Documentation**: Document complex scenarios

