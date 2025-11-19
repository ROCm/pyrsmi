# pyrsmi Test Suite

Unit tests for pyrsmi functionality with amdsmi backend.

## Requirements

- pytest >= 7.0
- pyrsmi with amdsmi backend
- ROCm 6.0+ with `libamd_smi.so`
- AMD GPU(s) for full test coverage
- pytest-cov (optional, for coverage reports)

## Running Tests

```bash
# Run all tests
pytest tests/

# Run with verbose output
pytest tests/ -v

# Run specific test file
pytest tests/test_memory.py

# Run with coverage (requires: pip install pytest-cov)
pytest tests/ --cov=pyrsmi --cov-report=html
```

## Test Organization

| File | Focus | Tests |
|------|-------|-------|
| `test_initialization.py` | Core infrastructure | 9 |
| `test_device_info.py` | Device enumeration | 13 |
| `test_memory.py` | Memory monitoring | 14 |
| `test_utilization.py` | Utilization & power | 11 |
| `test_pcie.py` | PCIe & topology | 15 |
| `test_uuid.py` | UUID & identification | 12 |

**Total: 74 tests**

## Test Fixtures

Key fixtures in `conftest.py`:
- `rocm_session` - Session-wide ROCm initialization
- `device_count` - Number of available GPUs
- `has_gpus` - Boolean for GPU presence
- `device_indices` - List of valid device indices

## Test Behavior

- Tests requiring GPUs are **skipped** if unavailable
- Tests for unsupported features handle gracefully
- All tests are non-destructive and read-only

## Continuous Integration

Example usage:

```yaml
# .github/workflows/test.yml
- name: Run tests
  run: pytest tests/ -v --junit-xml=test-results.xml
```

## Contributing

When adding features:
1. Add tests to appropriate file
2. Follow naming convention: `test_*`
3. Use existing fixtures
4. Ensure tests pass locally

