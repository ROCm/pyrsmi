"""
Pytest configuration and fixtures for pyrsmi tests
"""

import pytest
from pyrsmi import rocml


@pytest.fixture(scope="session")
def rocm_session():
    """Session-wide fixture to initialize and shutdown ROCm once for all tests"""
    rocml.smi_initialize()
    yield
    rocml.smi_shutdown()


@pytest.fixture(scope="function")
def rocm():
    """Function-level fixture for tests that need fresh initialization"""
    rocml.smi_initialize()
    yield
    rocml.smi_shutdown()


@pytest.fixture(scope="session")
def device_count(rocm_session):
    """Get the number of available GPU devices"""
    count = rocml.smi_get_device_count()
    return count


@pytest.fixture(scope="session")
def has_gpus(device_count):
    """Check if system has GPUs"""
    return device_count > 0


@pytest.fixture(scope="session")
def device_indices(device_count):
    """Get list of valid device indices"""
    return list(range(device_count))


@pytest.fixture(scope="session", params=range(8))
def device_id(request, device_count):
    """Parametrized fixture to test each device"""
    if request.param < device_count:
        return request.param
    pytest.skip(f"Device {request.param} not available (only {device_count} GPUs present)")

