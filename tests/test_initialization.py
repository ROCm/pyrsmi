"""
Test core initialization and shutdown functionality (Phase 1)
"""

import pytest
from pyrsmi import rocml


class TestLibraryLoading:
    """Test library loading and function availability"""
    
    def test_library_name(self):
        """Test that the correct library name is set"""
        assert rocml.LIBROCM_NAME == 'libamd_smi.so'
    
    def test_library_or_package_available(self):
        """Test that either amdsmi package or library is available"""
        # Fresh initialization to get correct state
        rocml.smi_initialize()
        try:
            if rocml._using_amdsmi_package:
                # Using amdsmi package, rocm_lib might not be loaded
                import amdsmi
                assert amdsmi is not None
            else:
                # Using ctypes, library should be loaded
                assert rocml.rocm_lib is not None
        finally:
            rocml.smi_shutdown()
    
    def test_required_functions_exist(self):
        """Test that all required amdsmi functions are available"""
        # Fresh initialization to get correct state
        rocml.smi_initialize()
        try:
            if rocml._using_amdsmi_package:
                # When using amdsmi package, check package functions
                import amdsmi
                required_funcs = [
                    'amdsmi_init',
                    'amdsmi_shut_down',
                    'amdsmi_get_processor_handles',
                    'amdsmi_get_gpu_asic_info'
                ]
                for func_name in required_funcs:
                    assert hasattr(amdsmi, func_name), f"Missing amdsmi package function: {func_name}"
            else:
                # When using ctypes, check library functions
                required_funcs = [
                    'amdsmi_init',
                    'amdsmi_shut_down',
                    'amdsmi_get_socket_handles',
                    'amdsmi_get_processor_handles',
                    'amdsmi_status_code_to_string'
                ]
                for func_name in required_funcs:
                    assert hasattr(rocml.rocm_lib, func_name), f"Missing library function: {func_name}"
        finally:
            rocml.smi_shutdown()


class TestAmdSmiPackageIntegration:
    """Test amdsmi Python package integration"""
    
    def test_amdsmi_package_check(self, amdsmi_available):
        """Test amdsmi package availability detection"""
        # This test documents whether amdsmi package is installed
        if amdsmi_available:
            import amdsmi
            assert hasattr(amdsmi, '__version__')
        else:
            pytest.skip("amdsmi package not installed - install for best results")
    
    def test_using_amdsmi_package_flag(self):
        """Test that _using_amdsmi_package flag is set correctly"""
        rocml.smi_initialize()
        try:
            assert isinstance(rocml._using_amdsmi_package, bool)
        finally:
            rocml.smi_shutdown()
    
    def test_amdsmi_preferred_when_available(self, amdsmi_available):
        """Test that amdsmi package is used when available"""
        # Fresh initialization to get correct state
        rocml.smi_initialize()
        try:
            if amdsmi_available:
                # amdsmi package should be preferred when available
                assert rocml._using_amdsmi_package is True, \
                    "amdsmi package is available but not being used"
            # If not available, ctypes fallback is fine
        finally:
            rocml.smi_shutdown()


class TestInitialization:
    """Test initialization and shutdown"""
    
    def test_initialize(self, rocm):
        """Test that initialization works"""
        # Already initialized by fixture
        assert rocml._handle_initialized is True
        assert len(rocml._processor_handles) >= 0
    
    def test_processor_handles(self, rocm):
        """Test that processor handles are initialized"""
        assert rocml._handle_initialized is True
        assert isinstance(rocml._processor_handles, list)
    
    def test_reinitialize(self):
        """Test that re-initialization works"""
        rocml.smi_initialize()
        count1 = len(rocml._processor_handles)
        using_package1 = rocml._using_amdsmi_package
        rocml.smi_shutdown()
        
        rocml.smi_initialize()
        count2 = len(rocml._processor_handles)
        using_package2 = rocml._using_amdsmi_package
        rocml.smi_shutdown()
        
        assert count1 == count2
        assert using_package1 == using_package2, "Backend should be consistent"


class TestHandleAccess:
    """Test processor handle access"""
    
    def test_get_handle_valid_index(self, rocm_session, device_count):
        """Test getting handle for valid device index"""
        if device_count > 0:
            handle = rocml._get_processor_handle(0)
            assert handle is not None
        else:
            pytest.skip("No GPUs available")
    
    def test_get_handle_invalid_index(self, rocm_session, device_count):
        """Test getting handle for invalid device index"""
        with pytest.raises((IndexError, ValueError)):
            rocml._get_processor_handle(device_count + 10)


class TestShutdown:
    """Test shutdown functionality"""
    
    def test_shutdown(self):
        """Test that shutdown clears handles"""
        rocml.smi_initialize()
        rocml.smi_shutdown()
        
        assert rocml._handle_initialized is False
        assert len(rocml._processor_handles) == 0
        assert rocml._using_amdsmi_package is False

