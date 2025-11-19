"""
Test PCIe and topology functions (Phase 5)
"""

import pytest
from pyrsmi import rocml


class TestPCIeBandwidth:
    """Test PCIe bandwidth information"""
    
    def test_pcie_info_type(self, rocm_session, has_gpus):
        """Test that PCIe info returns correct type"""
        if not has_gpus:
            pytest.skip("No GPUs available")
        
        pcie_info = rocml.smi_get_device_pcie_bandwidth(0)
        # Should return amdsmi_pcie_info_t structure or -1
        assert pcie_info != -1, "PCIe bandwidth query failed"
    
    def test_pcie_static_info(self, rocm_session, has_gpus):
        """Test PCIe static information"""
        if not has_gpus:
            pytest.skip("No GPUs available")
        
        pcie_info = rocml.smi_get_device_pcie_bandwidth(0)
        if pcie_info != -1:
            assert hasattr(pcie_info, 'pcie_static')
            assert hasattr(pcie_info.pcie_static, 'max_pcie_width')
            assert hasattr(pcie_info.pcie_static, 'max_pcie_speed')
            assert pcie_info.pcie_static.max_pcie_width > 0
    
    def test_pcie_metric_info(self, rocm_session, has_gpus):
        """Test PCIe metric information"""
        if not has_gpus:
            pytest.skip("No GPUs available")
        
        pcie_info = rocml.smi_get_device_pcie_bandwidth(0)
        if pcie_info != -1:
            assert hasattr(pcie_info, 'pcie_metric')
            assert hasattr(pcie_info.pcie_metric, 'pcie_width')
            assert hasattr(pcie_info.pcie_metric, 'pcie_speed')
            assert hasattr(pcie_info.pcie_metric, 'pcie_replay_count')


class TestPCIeID:
    """Test PCI ID (BDF) retrieval"""
    
    def test_pci_id_type(self, rocm_session, has_gpus):
        """Test that PCI ID returns an integer"""
        if not has_gpus:
            pytest.skip("No GPUs available")
        
        pci_id = rocml.smi_get_device_pci_id(0)
        assert isinstance(pci_id, int)
        assert pci_id != -1
    
    def test_pci_id_unique(self, rocm_session, device_indices):
        """Test that PCI IDs are unique"""
        if len(device_indices) < 2:
            pytest.skip("Need at least 2 GPUs")
        
        pci_ids = [rocml.smi_get_device_pci_id(idx) for idx in device_indices]
        assert len(pci_ids) == len(set(pci_ids)), "PCI IDs should be unique"


class TestPCIeThroughput:
    """Test PCIe throughput monitoring"""
    
    def test_throughput_type(self, rocm_session, has_gpus):
        """Test that throughput returns an integer"""
        if not has_gpus:
            pytest.skip("No GPUs available")
        
        throughput = rocml.smi_get_device_pcie_throughput(0)
        assert isinstance(throughput, int)
        assert throughput >= -1, "Throughput should be non-negative or -1"


class TestPCIeReplayCounter:
    """Test PCIe replay counter"""
    
    def test_replay_counter_type(self, rocm_session, has_gpus):
        """Test that replay counter returns an integer"""
        if not has_gpus:
            pytest.skip("No GPUs available")
        
        counter = rocml.smi_get_device_pci_replay_counter(0)
        assert isinstance(counter, int)
        assert counter >= -1, "Replay counter should be non-negative or -1"
    
    def test_replay_counter_healthy(self, rocm_session, has_gpus):
        """Test that replay counter is typically low for healthy systems"""
        if not has_gpus:
            pytest.skip("No GPUs available")
        
        counter = rocml.smi_get_device_pci_replay_counter(0)
        if counter > 0:
            # High replay count might indicate issues, but not a test failure
            pytest.skip(f"Replay count is {counter}, may indicate PCIe issues")


class TestNUMAffinity:
    """Test NUMA affinity"""
    
    def test_numa_affinity_type(self, rocm_session, has_gpus):
        """Test that NUMA affinity returns an integer"""
        if not has_gpus:
            pytest.skip("No GPUs available")
        
        numa = rocml.smi_get_device_topo_numa_affinity(0)
        assert isinstance(numa, int)
        assert numa >= -1, "NUMA node should be non-negative or -1"
    
    def test_numa_node_number(self, rocm_session, has_gpus):
        """Test NUMA node number retrieval"""
        if not has_gpus:
            pytest.skip("No GPUs available")
        
        numa = rocml.smi_get_device_topo_numa_node_number(0)
        assert isinstance(numa, int)
        assert numa >= -1, "NUMA node should be non-negative or -1"
    
    def test_numa_consistency(self, rocm_session, has_gpus):
        """Test that both NUMA functions return consistent results"""
        if not has_gpus:
            pytest.skip("No GPUs available")
        
        affinity = rocml.smi_get_device_topo_numa_affinity(0)
        node_num = rocml.smi_get_device_topo_numa_node_number(0)
        
        # Both should return same value or both -1
        if affinity != -1 and node_num != -1:
            assert affinity == node_num, "NUMA affinity and node number should match"


class TestTopology:
    """Test GPU topology functions"""
    
    def test_link_weight(self, rocm_session, device_count):
        """Test link weight between devices"""
        if device_count < 2:
            pytest.skip("Need at least 2 GPUs for topology tests")
        
        weight = rocml.smi_get_device_topo_link_weight(0, 1)
        assert isinstance(weight, int)
        assert weight >= -1
    
    def test_link_type(self, rocm_session, device_count):
        """Test link type between devices"""
        if device_count < 2:
            pytest.skip("Need at least 2 GPUs for topology tests")
        
        result = rocml.smi_get_device_link_type(0, 1)
        if result != -1:
            hops, link_type = result
            assert isinstance(hops, int)
            assert isinstance(link_type, int)
            assert hops >= 0
            assert 0 <= link_type <= 4  # Valid amdsmi_link_type_t values
    
    def test_p2p_accessible(self, rocm_session, device_count):
        """Test P2P accessibility between devices"""
        if device_count < 2:
            pytest.skip("Need at least 2 GPUs for topology tests")
        
        accessible = rocml.smi_is_device_p2p_accessible(0, 1)
        assert isinstance(accessible, (bool, int))
        # Can be True, False, or -1 (error)
        assert accessible in [True, False, -1]
    
    def test_minmax_bandwidth(self, rocm_session, device_count):
        """Test min/max bandwidth between devices"""
        if device_count < 2:
            pytest.skip("Need at least 2 GPUs for topology tests")
        
        result = rocml.smi_get_device_minmax_bandwidth(0, 1)
        if result != -1:
            min_bw, max_bw = result
            assert isinstance(min_bw, int)
            assert isinstance(max_bw, int)
            assert min_bw >= 0
            assert max_bw >= min_bw, "Max bandwidth should be >= min bandwidth"


class TestTopologyMatrix:
    """Test topology relationships across all GPU pairs"""
    
    def test_topology_all_pairs(self, rocm_session, device_indices):
        """Test topology for all device pairs"""
        if len(device_indices) < 2:
            pytest.skip("Need at least 2 GPUs")
        
        for i in device_indices:
            for j in device_indices:
                if i == j:
                    continue
                
                # All topology queries should not raise exceptions
                try:
                    rocml.smi_get_device_topo_link_weight(i, j)
                    rocml.smi_get_device_link_type(i, j)
                    rocml.smi_is_device_p2p_accessible(i, j)
                except Exception as e:
                    pytest.fail(f"Topology query failed for pair ({i},{j}): {e}")

