"""
Test UUID and device identification functions (Phase 6)
"""

import pytest
from pyrsmi import rocml


class TestUUID:
    """Test UUID retrieval"""
    
    @pytest.mark.parametrize("format", ['roc', 'raw', 'nv'])
    def test_uuid_formats(self, rocm_session, has_gpus, format):
        """Test UUID retrieval in different formats"""
        if not has_gpus:
            pytest.skip("No GPUs available")
        
        uuid = rocml.smi_get_device_uuid(0, format=format)
        assert isinstance(uuid, str)
        assert len(uuid) > 0, f"UUID in {format} format is empty"
        
        if format == 'roc':
            assert uuid.startswith('GPU-'), "ROCm format should start with 'GPU-'"
        elif format == 'raw':
            assert not uuid.startswith('GPU-'), "Raw format should not have 'GPU-' prefix"
    
    def test_uuid_consistency(self, rocm_session, has_gpus):
        """Test that UUID is consistent across calls"""
        if not has_gpus:
            pytest.skip("No GPUs available")
        
        uuid1 = rocml.smi_get_device_uuid(0, format='roc')
        uuid2 = rocml.smi_get_device_uuid(0, format='roc')
        
        assert uuid1 == uuid2, "UUID should be consistent across calls"
    
    def test_uuid_uniqueness(self, rocm_session, device_indices):
        """Test that all devices have unique UUIDs"""
        if len(device_indices) < 2:
            pytest.skip("Need at least 2 GPUs for uniqueness test")
        
        uuids = [rocml.smi_get_device_uuid(idx, format='roc') for idx in device_indices]
        assert len(uuids) == len(set(uuids)), "All UUIDs should be unique"
    
    def test_uuid_format_conversion(self, rocm_session, has_gpus):
        """Test that different formats represent the same UUID"""
        if not has_gpus:
            pytest.skip("No GPUs available")
        
        uuid_roc = rocml.smi_get_device_uuid(0, format='roc')
        uuid_raw = rocml.smi_get_device_uuid(0, format='raw')
        
        # ROCm format should be raw format with 'GPU-' prefix
        assert uuid_roc == f'GPU-{uuid_raw}', "ROCm and raw formats should be related"
    
    def test_uuid_invalid_format(self, rocm_session, has_gpus):
        """Test UUID with invalid format"""
        if not has_gpus:
            pytest.skip("No GPUs available")
        
        # Function handles errors gracefully, returning empty string
        try:
            uuid = rocml.smi_get_device_uuid(0, format='invalid')
            # Should return empty string or raise ValueError
            assert uuid == "" or uuid is None
        except ValueError:
            # ValueError is also acceptable
            pass
    
    def test_uuid_all_devices(self, rocm_session, device_indices):
        """Test UUID for all devices"""
        if not device_indices:
            pytest.skip("No GPUs available")
        
        for idx in device_indices:
            uuid = rocml.smi_get_device_uuid(idx, format='roc')
            assert isinstance(uuid, str)
            assert len(uuid) > 0, f"Device {idx} has empty UUID"
            assert uuid.startswith('GPU-'), f"Device {idx} UUID should start with 'GPU-'"


class TestUniqueID:
    """Test unique ID (BDF) consistency"""
    
    def test_unique_id_consistency_with_pci(self, rocm_session, has_gpus):
        """Test that unique ID matches PCI ID"""
        if not has_gpus:
            pytest.skip("No GPUs available")
        
        unique_id = rocml.smi_get_device_unique_id(0)
        pci_id = rocml.smi_get_device_pci_id(0)
        
        # Both should return the same BDF value
        assert unique_id == pci_id, "Unique ID and PCI ID should match"
    
    def test_unique_id_repeated_calls(self, rocm_session, has_gpus):
        """Test that unique ID is stable across repeated calls"""
        if not has_gpus:
            pytest.skip("No GPUs available")
        
        uid1 = rocml.smi_get_device_unique_id(0)
        uid2 = rocml.smi_get_device_unique_id(0)
        
        assert uid1 == uid2, "Unique ID should be stable"


class TestDeviceIdentification:
    """Test combined device identification"""
    
    def test_device_identification_complete(self, rocm_session, has_gpus):
        """Test that all device identification methods work together"""
        if not has_gpus:
            pytest.skip("No GPUs available")
        
        # Get all identification info
        name = rocml.smi_get_device_name(0)
        dev_id = rocml.smi_get_device_id(0)
        unique_id = rocml.smi_get_device_unique_id(0)
        uuid = rocml.smi_get_device_uuid(0, format='roc')
        
        # All should be valid
        assert name and len(name) > 0
        assert dev_id != -1
        assert unique_id != -1
        assert uuid and len(uuid) > 0
    
    def test_multiple_device_identification(self, rocm_session, device_indices):
        """Test identification for all devices"""
        if not device_indices:
            pytest.skip("No GPUs available")
        
        device_info = []
        for idx in device_indices:
            info = {
                'index': idx,
                'name': rocml.smi_get_device_name(idx),
                'device_id': rocml.smi_get_device_id(idx),
                'unique_id': rocml.smi_get_device_unique_id(idx),
                'uuid': rocml.smi_get_device_uuid(idx, format='roc')
            }
            device_info.append(info)
        
        # Check all devices have complete info
        for info in device_info:
            assert info['name'] and len(info['name']) > 0
            assert info['device_id'] != -1
            assert info['unique_id'] != -1
            assert info['uuid'] and len(info['uuid']) > 0
        
        # Check uniqueness of identifiers
        unique_ids = [info['unique_id'] for info in device_info]
        uuids = [info['uuid'] for info in device_info]
        
        assert len(unique_ids) == len(set(unique_ids)), "Unique IDs should be unique"
        assert len(uuids) == len(set(uuids)), "UUIDs should be unique"

