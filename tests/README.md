# pyrsmi Test Suite

Unit tests for pyrsmi functionality with amdsmi backend.

## Requirements

- pytest >= 7.0
- pyrsmi with amdsmi backend
- ROCm 6.0+ with `libamd_smi.so`
- AMD GPU(s) for full test coverage
- pytest-cov (optional, for coverage reports)
- **amdsmi Python package (strongly recommended)**

### Installing amdsmi Package

For complete test coverage and correct device detection:

```bash
# Option 1: Install from ROCm (recommended)
cp -r /opt/rocm/share/amd_smi /tmp/amd_smi_install
pip install /tmp/amd_smi_install/
rm -rf /tmp/amd_smi_install

# Option 2: Install from PyPI
pip install amdsmi
```

> **Note:** Without the `amdsmi` package, some tests may skip or show warnings about generic device names.

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

# Run only amdsmi integration tests
pytest tests/test_initialization.py -k "amdsmi" -v
```

## Test Organization

| File | Focus | Tests |
|------|-------|-------|
| `test_initialization.py` | Core infrastructure & amdsmi integration | 12 |
| `test_device_info.py` | Device enumeration | 14 |
| `test_memory.py` | Memory monitoring | 14 |
| `test_utilization.py` | Utilization & power | 11 |
| `test_pcie.py` | PCIe & topology | 15 |
| `test_uuid.py` | UUID & identification | 12 |

**Total: 78 tests**

## Test Fixtures

Key fixtures in `conftest.py`:
- `rocm_session` - Session-wide ROCm initialization
- `device_count` - Number of available GPUs
- `has_gpus` - Boolean for GPU presence
- `device_indices` - List of valid device indices
- `amdsmi_available` - Check if amdsmi Python package is installed
- `using_amdsmi_package` - Check if pyrsmi is using amdsmi package backend

## Test Behavior

- Tests requiring GPUs are **skipped** if unavailable
- Tests for unsupported features handle gracefully
- All tests are non-destructive and read-only
- Tests verify amdsmi package integration when available

## Backend Detection

The tests automatically detect which backend pyrsmi is using:

| Condition | Backend Used | Device Name Quality |
|-----------|--------------|---------------------|
| amdsmi package installed | amdsmi Python package | ✅ Correct (e.g., "AMD Instinct MI350X") |
| amdsmi not installed | ctypes to libamd_smi.so | ⚠️ May be generic |

## Continuous Integration

Example usage:

```yaml
# .github/workflows/test.yml
- name: Install amdsmi package
  run: |
    cp -r /opt/rocm/share/amd_smi /tmp/amd_smi_install
    pip install /tmp/amd_smi_install/
    rm -rf /tmp/amd_smi_install

- name: Run tests
  run: pytest tests/ -v --junit-xml=test-results.xml
```

## Contributing

When adding features:
1. Add tests to appropriate file
2. Follow naming convention: `test_*`
3. Use existing fixtures
4. Handle both amdsmi package and ctypes backends
5. Ensure tests pass locally

