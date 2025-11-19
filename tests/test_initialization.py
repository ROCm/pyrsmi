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
    
    def test_library_loaded(self, rocm_session):
        """Test that the library is loaded"""
        assert rocml.rocm_lib is not None
    
    def test_required_functions_exist(self, rocm_session):
        """Test that all required amdsmi functions are available"""
        required_funcs = [
            'amdsmi_init',
            'amdsmi_shut_down',
            'amdsmi_get_socket_handles',
            'amdsmi_get_processor_handles',
            'amdsmi_status_code_to_string'
        ]
        
        for func_name in required_funcs:
            assert hasattr(rocml.rocm_lib, func_name), f"Missing function: {func_name}"


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
        rocml.smi_shutdown()
        
        rocml.smi_initialize()
        count2 = len(rocml._processor_handles)
        rocml.smi_shutdown()
        
        assert count1 == count2


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

