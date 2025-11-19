"""
Test device enumeration and information functions (Phase 2)
"""

import pytest
from pyrsmi import rocml


class TestDeviceCount:
    """Test device counting"""
    
    def test_device_count_returns_int(self, rocm_session):
        """Test that device count returns an integer"""
        count = rocml.smi_get_device_count()
        assert isinstance(count, int)
        assert count >= 0
    
    def test_device_count_consistent(self, rocm_session):
        """Test that device count is consistent across calls"""
        count1 = rocml.smi_get_device_count()
        count2 = rocml.smi_get_device_count()
        assert count1 == count2


class TestDeviceName:
    """Test device name retrieval"""
    
    def test_device_name_type(self, rocm_session, has_gpus):
        """Test that device name returns a string"""
        if not has_gpus:
            pytest.skip("No GPUs available")
        
        name = rocml.smi_get_device_name(0)
        assert isinstance(name, str)
        assert len(name) > 0
    
    def test_device_name_all_devices(self, rocm_session, device_indices):
        """Test device names for all devices"""
        if not device_indices:
            pytest.skip("No GPUs available")
        
        for idx in device_indices:
            name = rocml.smi_get_device_name(idx)
            assert isinstance(name, str)
            assert len(name) > 0, f"Device {idx} has empty name"
    
    def test_device_name_invalid_index(self, rocm_session, device_count):
        """Test device name with invalid index"""
        # Functions handle errors gracefully, returning empty string or -1
        # They don't raise exceptions directly
        try:
            name = rocml.smi_get_device_name(device_count + 10)
            # Should return empty string on error
            assert name == "" or name is None
        except (ValueError, IndexError):
            # Some implementations might raise, which is also acceptable
            pass


class TestDeviceID:
    """Test device ID retrieval"""
    
    def test_device_id_type(self, rocm_session, has_gpus):
        """Test that device ID returns an integer"""
        if not has_gpus:
            pytest.skip("No GPUs available")
        
        dev_id = rocml.smi_get_device_id(0)
        assert isinstance(dev_id, int)
        assert dev_id != -1
    
    def test_device_id_all_devices(self, rocm_session, device_indices):
        """Test device IDs for all devices"""
        if not device_indices:
            pytest.skip("No GPUs available")
        
        for idx in device_indices:
            dev_id = rocml.smi_get_device_id(idx)
            assert isinstance(dev_id, int)
            assert dev_id != -1, f"Device {idx} has invalid ID"


class TestDeviceRevision:
    """Test device revision retrieval"""
    
    def test_device_revision_type(self, rocm_session, has_gpus):
        """Test that device revision returns an integer"""
        if not has_gpus:
            pytest.skip("No GPUs available")
        
        revision = rocml.smi_get_device_revision(0)
        assert isinstance(revision, int)
        assert revision != -1
    
    def test_device_revision_all_devices(self, rocm_session, device_indices):
        """Test device revisions for all devices"""
        if not device_indices:
            pytest.skip("No GPUs available")
        
        for idx in device_indices:
            revision = rocml.smi_get_device_revision(idx)
            assert isinstance(revision, int)
            assert revision != -1, f"Device {idx} has invalid revision"


class TestDeviceUniqueID:
    """Test device unique ID (BDF) retrieval"""
    
    def test_unique_id_type(self, rocm_session, has_gpus):
        """Test that unique ID returns an integer"""
        if not has_gpus:
            pytest.skip("No GPUs available")
        
        uid = rocml.smi_get_device_unique_id(0)
        assert isinstance(uid, int)
        assert uid != -1
    
    def test_unique_id_all_devices(self, rocm_session, device_indices):
        """Test unique IDs for all devices"""
        if not device_indices:
            pytest.skip("No GPUs available")
        
        unique_ids = []
        for idx in device_indices:
            uid = rocml.smi_get_device_unique_id(idx)
            assert isinstance(uid, int)
            assert uid != -1, f"Device {idx} has invalid unique ID"
            unique_ids.append(uid)
        
        # Check uniqueness
        assert len(unique_ids) == len(set(unique_ids)), "Some device unique IDs are not unique"
    
    def test_unique_id_bdf_format(self, rocm_session, has_gpus):
        """Test that unique ID can be decoded as BDF"""
        if not has_gpus:
            pytest.skip("No GPUs available")
        
        uid = rocml.smi_get_device_unique_id(0)
        
        # Decode BDF components
        domain = (uid >> 32) & 0xFFFFFFFF
        bus = (uid >> 8) & 0xFF
        device = (uid >> 3) & 0x1F
        function = uid & 0x7
        
        # Basic sanity checks
        assert 0 <= bus <= 255
        assert 0 <= device <= 31
        assert 0 <= function <= 7


class TestDeviceInfo:
    """Test device information summary"""
    
    def test_all_info_consistent(self, rocm_session, has_gpus):
        """Test that all device info functions work together"""
        if not has_gpus:
            pytest.skip("No GPUs available")
        
        name = rocml.smi_get_device_name(0)
        dev_id = rocml.smi_get_device_id(0)
        revision = rocml.smi_get_device_revision(0)
        uid = rocml.smi_get_device_unique_id(0)
        
        assert all([
            isinstance(name, str) and len(name) > 0,
            isinstance(dev_id, int) and dev_id != -1,
            isinstance(revision, int) and revision != -1,
            isinstance(uid, int) and uid != -1
        ])

