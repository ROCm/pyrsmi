"""
Test memory monitoring functions (Phase 3)
"""

import pytest
from pyrsmi import rocml


class TestMemoryTotal:
    """Test total memory retrieval"""
    
    @pytest.mark.parametrize("mem_type", ['VRAM', 'VIS_VRAM', 'GTT'])
    def test_memory_total_types(self, rocm_session, has_gpus, mem_type):
        """Test memory total for different memory types"""
        if not has_gpus:
            pytest.skip("No GPUs available")
        
        total = rocml.smi_get_device_memory_total(0, mem_type)
        assert isinstance(total, int)
        # VRAM should always have a value, others might be 0 or -1
        if mem_type == 'VRAM':
            assert total > 0, "VRAM total should be positive"
    
    def test_memory_total_all_devices(self, rocm_session, device_indices):
        """Test memory total for all devices"""
        if not device_indices:
            pytest.skip("No GPUs available")
        
        for idx in device_indices:
            total = rocml.smi_get_device_memory_total(idx, 'VRAM')
            assert isinstance(total, int)
            assert total > 0, f"Device {idx} has invalid total memory"
    
    def test_memory_total_invalid_type(self, rocm_session, has_gpus):
        """Test memory total with invalid type"""
        if not has_gpus:
            pytest.skip("No GPUs available")
        
        # Functions handle errors gracefully, returning -1
        try:
            total = rocml.smi_get_device_memory_total(0, 'INVALID_TYPE')
            # Should return -1 or raise ValueError
            assert total == -1
        except ValueError:
            # ValueError is also acceptable
            pass


class TestMemoryUsed:
    """Test used memory retrieval"""
    
    def test_memory_used_type(self, rocm_session, has_gpus):
        """Test that memory used returns an integer"""
        if not has_gpus:
            pytest.skip("No GPUs available")
        
        used = rocml.smi_get_device_memory_used(0, 'VRAM')
        assert isinstance(used, int)
        assert used >= 0
    
    def test_memory_used_all_devices(self, rocm_session, device_indices):
        """Test memory used for all devices"""
        if not device_indices:
            pytest.skip("No GPUs available")
        
        for idx in device_indices:
            used = rocml.smi_get_device_memory_used(idx, 'VRAM')
            assert isinstance(used, int)
            assert used >= 0, f"Device {idx} has invalid used memory"
    
    def test_memory_used_less_than_total(self, rocm_session, has_gpus):
        """Test that used memory is less than or equal to total memory"""
        if not has_gpus:
            pytest.skip("No GPUs available")
        
        total = rocml.smi_get_device_memory_total(0, 'VRAM')
        used = rocml.smi_get_device_memory_used(0, 'VRAM')
        
        assert used <= total, "Used memory should not exceed total memory"


class TestMemoryBusy:
    """Test memory busy percentage"""
    
    def test_memory_busy_range(self, rocm_session, has_gpus):
        """Test that memory busy is within valid range"""
        if not has_gpus:
            pytest.skip("No GPUs available")
        
        busy = rocml.smi_get_device_memory_busy(0)
        assert isinstance(busy, int)
        # Can be -1 if not supported, or 0-100 if supported
        assert (busy == -1) or (0 <= busy <= 100)
    
    def test_memory_busy_all_devices(self, rocm_session, device_indices):
        """Test memory busy for all devices"""
        if not device_indices:
            pytest.skip("No GPUs available")
        
        for idx in device_indices:
            busy = rocml.smi_get_device_memory_busy(idx)
            assert isinstance(busy, int)
            assert (busy == -1) or (0 <= busy <= 100)


class TestMemoryReservedPages:
    """Test reserved/retired memory pages"""
    
    def test_reserved_pages_type(self, rocm_session, has_gpus):
        """Test that reserved pages returns correct type"""
        if not has_gpus:
            pytest.skip("No GPUs available")
        
        result = rocml.smi_get_device_memory_reserved_pages(0)
        # Should return tuple (num_pages, records) or -1
        assert result != -1 or isinstance(result, tuple)
        
        if result != -1:
            num_pages, records = result
            assert isinstance(num_pages, int)
            assert num_pages >= 0
    
    def test_reserved_pages_all_devices(self, rocm_session, device_indices):
        """Test reserved pages for all devices"""
        if not device_indices:
            pytest.skip("No GPUs available")
        
        for idx in device_indices:
            result = rocml.smi_get_device_memory_reserved_pages(idx)
            # Function should not raise exception
            assert result is not None


class TestMemoryUsagePercentage:
    """Test memory usage calculations"""
    
    def test_memory_usage_percentage(self, rocm_session, has_gpus):
        """Test memory usage percentage calculation"""
        if not has_gpus:
            pytest.skip("No GPUs available")
        
        total = rocml.smi_get_device_memory_total(0, 'VRAM')
        used = rocml.smi_get_device_memory_used(0, 'VRAM')
        
        if total > 0:
            usage_pct = (used / total) * 100
            assert 0 <= usage_pct <= 100

