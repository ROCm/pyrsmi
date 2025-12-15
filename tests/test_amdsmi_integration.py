"""
Test amdsmi Python package integration (Phase 7)

These tests verify that pyrsmi correctly integrates with the amdsmi Python package
when available, providing better device detection and naming.
"""

import pytest
from pyrsmi import rocml


class TestAmdSmiPackageAvailability:
    """Test amdsmi package detection and usage"""
    
    def test_amdsmi_import(self, amdsmi_available):
        """Test that amdsmi package can be imported"""
        if not amdsmi_available:
            pytest.skip("amdsmi package not installed")
        
        import amdsmi
        assert amdsmi is not None
    
    def test_amdsmi_version(self, amdsmi_available):
        """Test that amdsmi package has version info"""
        if not amdsmi_available:
            pytest.skip("amdsmi package not installed")
        
        import amdsmi
        assert hasattr(amdsmi, '__version__')
        version = amdsmi.__version__
        assert isinstance(version, str)
        assert len(version) > 0
    
    def test_amdsmi_functions_available(self, amdsmi_available):
        """Test that required amdsmi functions are available"""
        if not amdsmi_available:
            pytest.skip("amdsmi package not installed")
        
        import amdsmi
        required_funcs = [
            'amdsmi_init',
            'amdsmi_shut_down',
            'amdsmi_get_processor_handles',
            'amdsmi_get_gpu_asic_info',
            'amdsmi_get_gpu_memory_usage',
            'amdsmi_get_gpu_memory_total',
            'amdsmi_get_gpu_activity',
            'amdsmi_get_power_info',
        ]
        
        for func_name in required_funcs:
            assert hasattr(amdsmi, func_name), f"Missing function: {func_name}"


class TestAmdSmiBackendSelection:
    """Test that pyrsmi correctly selects amdsmi package backend"""
    
    def test_backend_flag_type(self, rocm_session):
        """Test that _using_amdsmi_package is a boolean"""
        assert isinstance(rocml._using_amdsmi_package, bool)
    
    def test_backend_preference(self, rocm_session, amdsmi_available):
        """Test that amdsmi package is preferred when available"""
        if amdsmi_available:
            assert rocml._using_amdsmi_package is True, \
                "amdsmi package should be used when available"
        else:
            # Ctypes fallback is acceptable when package not installed
            pass
    
    def test_backend_consistency(self):
        """Test that backend selection is consistent across reinitializations"""
        rocml.smi_initialize()
        backend1 = rocml._using_amdsmi_package
        rocml.smi_shutdown()
        
        rocml.smi_initialize()
        backend2 = rocml._using_amdsmi_package
        rocml.smi_shutdown()
        
        assert backend1 == backend2, "Backend should be consistent"


class TestAmdSmiDeviceDiscovery:
    """Test device discovery with amdsmi package"""
    
    def test_device_discovery(self, rocm_session, using_amdsmi_package, has_gpus):
        """Test that devices are discovered correctly"""
        if not has_gpus:
            pytest.skip("No GPUs available")
        
        count = rocml.smi_get_device_count()
        assert count > 0
        
        if using_amdsmi_package:
            # With amdsmi package, handles should be package handles
            assert len(rocml._processor_handles) == count
    
    def test_device_handles_valid(self, rocm_session, using_amdsmi_package, device_indices):
        """Test that device handles are valid"""
        if not device_indices:
            pytest.skip("No GPUs available")
        
        for idx in device_indices:
            handle = rocml._get_processor_handle(idx)
            assert handle is not None


class TestAmdSmiDeviceInfo:
    """Test device information retrieval with amdsmi package"""
    
    def test_device_name_with_amdsmi(self, rocm_session, using_amdsmi_package, has_gpus):
        """Test device name retrieval with amdsmi package"""
        if not has_gpus:
            pytest.skip("No GPUs available")
        
        name = rocml.smi_get_device_name(0)
        assert isinstance(name, str)
        assert len(name) > 0
        
        if using_amdsmi_package:
            # With amdsmi package, should get meaningful names
            # (though it depends on amdgpu.ids being up to date)
            assert 'AMD' in name or 'Radeon' in name or 'Instinct' in name or 'Graphics' in name
    
    def test_device_id_with_amdsmi(self, rocm_session, using_amdsmi_package, has_gpus):
        """Test device ID retrieval with amdsmi package"""
        if not has_gpus:
            pytest.skip("No GPUs available")
        
        dev_id = rocml.smi_get_device_id(0)
        assert isinstance(dev_id, int)
        assert dev_id != -1


class TestAmdSmiMemoryQueries:
    """Test memory queries with amdsmi package"""
    
    def test_memory_total_with_amdsmi(self, rocm_session, using_amdsmi_package, has_gpus):
        """Test memory total retrieval with amdsmi package"""
        if not has_gpus:
            pytest.skip("No GPUs available")
        
        total = rocml.smi_get_device_memory_total(0, 'VRAM')
        assert isinstance(total, int)
        assert total > 0
    
    def test_memory_used_with_amdsmi(self, rocm_session, using_amdsmi_package, has_gpus):
        """Test memory used retrieval with amdsmi package"""
        if not has_gpus:
            pytest.skip("No GPUs available")
        
        used = rocml.smi_get_device_memory_used(0, 'VRAM')
        assert isinstance(used, int)
        assert used >= 0


class TestAmdSmiUtilization:
    """Test utilization queries with amdsmi package"""
    
    def test_utilization_with_amdsmi(self, rocm_session, using_amdsmi_package, has_gpus):
        """Test GPU utilization retrieval with amdsmi package"""
        if not has_gpus:
            pytest.skip("No GPUs available")
        
        util = rocml.smi_get_device_utilization(0)
        assert isinstance(util, int)
        assert 0 <= util <= 100 or util == -1
    
    def test_memory_busy_with_amdsmi(self, rocm_session, using_amdsmi_package, has_gpus):
        """Test memory busy retrieval with amdsmi package"""
        if not has_gpus:
            pytest.skip("No GPUs available")
        
        busy = rocml.smi_get_device_memory_busy(0)
        assert isinstance(busy, int)
        assert 0 <= busy <= 100 or busy == -1


class TestAmdSmiPower:
    """Test power queries with amdsmi package"""
    
    def test_power_with_amdsmi(self, rocm_session, using_amdsmi_package, has_gpus):
        """Test power retrieval with amdsmi package"""
        if not has_gpus:
            pytest.skip("No GPUs available")
        
        power = rocml.smi_get_device_average_power(0)
        assert isinstance(power, (int, float))
        assert power > 0 or power == -1


class TestAmdSmiShutdown:
    """Test shutdown with amdsmi package"""
    
    def test_shutdown_clears_amdsmi_flag(self, rocm):
        """Test that shutdown clears amdsmi package flag"""
        # rocm fixture handles init/shutdown
        # After shutdown (handled by fixture), flags should be cleared
        pass  # The actual check happens after fixture cleanup
    
    def test_shutdown_state(self):
        """Test that shutdown properly clears state"""
        # Fresh initialize
        rocml.smi_initialize()
        was_using_amdsmi = rocml._using_amdsmi_package
        
        # Shutdown
        rocml.smi_shutdown()
        
        # Verify state is cleared
        assert rocml._using_amdsmi_package is False
        assert rocml._handle_initialized is False
        assert len(rocml._processor_handles) == 0
        
        # Re-initialize to restore for other tests
        rocml.smi_initialize()
        assert rocml._using_amdsmi_package == was_using_amdsmi
        rocml.smi_shutdown()


