"""
Test utilization and power monitoring functions (Phase 4)
"""

import pytest
from pyrsmi import rocml


class TestDeviceUtilization:
    """Test GPU utilization monitoring"""
    
    def test_utilization_range(self, rocm_session, has_gpus):
        """Test that utilization is within valid range"""
        if not has_gpus:
            pytest.skip("No GPUs available")
        
        util = rocml.smi_get_device_utilization(0)
        assert isinstance(util, int)
        assert 0 <= util <= 100, f"Utilization should be 0-100%, got {util}%"
    
    def test_utilization_all_devices(self, rocm_session, device_indices):
        """Test utilization for all devices"""
        if not device_indices:
            pytest.skip("No GPUs available")
        
        for idx in device_indices:
            util = rocml.smi_get_device_utilization(idx)
            assert isinstance(util, int)
            assert 0 <= util <= 100, f"Device {idx} utilization out of range: {util}%"


class TestDevicePower:
    """Test power consumption monitoring"""
    
    def test_power_type(self, rocm_session, has_gpus):
        """Test that power returns a float"""
        if not has_gpus:
            pytest.skip("No GPUs available")
        
        power = rocml.smi_get_device_average_power(0)
        assert isinstance(power, (int, float))
        assert power >= 0 or power == -1, "Power should be positive or -1"
    
    def test_power_all_devices(self, rocm_session, device_indices):
        """Test power for all devices"""
        if not device_indices:
            pytest.skip("No GPUs available")
        
        for idx in device_indices:
            power = rocml.smi_get_device_average_power(idx)
            assert isinstance(power, (int, float))
            assert power >= 0 or power == -1, f"Device {idx} has invalid power: {power}W"
    
    def test_power_reasonable_range(self, rocm_session, has_gpus):
        """Test that power is within reasonable range"""
        if not has_gpus:
            pytest.skip("No GPUs available")
        
        power = rocml.smi_get_device_average_power(0)
        if power > 0:
            # Reasonable power range for data center GPUs: 0-1000W
            assert 0 < power <= 1000, f"Power seems unreasonable: {power}W"


class TestDeviceFan:
    """Test fan monitoring functions"""
    
    def test_fan_rpms(self, rocm_session, has_gpus):
        """Test fan RPM retrieval"""
        if not has_gpus:
            pytest.skip("No GPUs available")
        
        rpm = rocml.smi_get_device_fan_rpms(0, 0)
        assert isinstance(rpm, int)
        # Can be -1 if not supported (liquid cooling, etc.)
        assert rpm >= -1, "Fan RPM should be positive or -1"
    
    def test_fan_speed(self, rocm_session, has_gpus):
        """Test fan speed percentage retrieval"""
        if not has_gpus:
            pytest.skip("No GPUs available")
        
        speed = rocml.smi_get_device_fan_speed(0, 0)
        assert isinstance(speed, int)
        # Can be -1 if not supported
        assert (speed == -1) or (0 <= speed <= 100), "Fan speed should be 0-100% or -1"
    
    def test_fan_speed_max(self, rocm_session, has_gpus):
        """Test max fan speed retrieval"""
        if not has_gpus:
            pytest.skip("No GPUs available")
        
        max_speed = rocml.smi_get_device_fan_speed_max(0, 0)
        assert isinstance(max_speed, int)
        # Can be -1 if not supported
        assert max_speed >= -1, "Max fan speed should be positive or -1"
    
    @pytest.mark.parametrize("sensor_idx", [0, 1, 2])
    def test_fan_multiple_sensors(self, rocm_session, has_gpus, sensor_idx):
        """Test fan monitoring for multiple sensors"""
        if not has_gpus:
            pytest.skip("No GPUs available")
        
        try:
            rpm = rocml.smi_get_device_fan_rpms(0, sensor_idx)
            assert isinstance(rpm, int)
        except:
            # Some sensors may not exist, that's okay
            pass

