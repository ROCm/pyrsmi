# pyrsmi
### Python Bindings for AMD System Management Interface (AMD SMI)
--------
- `pyrsmi` is a Python package providing system management functionality for AMD GPUs.
- **Version 1.0+** uses the new **AMD SMI Library (`amdsmi`)**, replacing the deprecated `rocm-smi-lib`.
- It provides comprehensive monitoring and management capabilities for AMD Instinct™ MI-series GPUs.

## Requirements
- **ROCm 6.0 or later** with AMD SMI Library (`libamd_smi.so`)
- Python 3.9 or later
- AMD Instinct™ MI-series GPU (tested on MI300X, MI250X, MI210)
- Linux operating system

## What's New in Version 1.0

**Major Update: Migration to AMD SMI Backend**

Version 1.0 represents a significant upgrade with full migration from the deprecated `rocm-smi-lib` to the modern `amdsmi` library:

✅ **Enhanced Performance:** 10-50x faster UUID retrieval through native API  
✅ **Improved Reliability:** Direct library integration eliminates external command dependencies  
✅ **100% Backward Compatible:** All existing APIs maintain their original signatures  
✅ **Richer Data:** Access to new PCIe metrics, topology information, and extended GPU telemetry  
✅ **Future-Proof:** Based on AMD's unified management interface for all compute products

**For detailed migration information, see [MIGRATION.md](MIGRATION.md)**

## How to install from source
- Clone this repo: 
  - `git clone https://github.com/ROCm/pyrsmi`
  - cd pyrsmi
- `python -m pip install -e .`
- `pyrsmi` can be installed as PyPA-compatible Python package.

## How to install Python packages
- Install `build` package:
  - `pip install build`
- At the top directory (where setup.py is), run: `python -m build`
- Then by default packages (both sdist and wheel) will be built under `dist` directory.
- The packages can be either installed with `pip install`, or be uploaded to PyPI (release or test) repo, or an artifactory of your choice. The latter can be installed liked beflow.

## How to install from PyPI
- **NOTE:** Release versions are available at pypi.org, and the package can be installed with :
  -  `python -m pip install pyrsmi`

## How to install from GitHub
- Install the latest development version directly from GitHub:
  ```bash
  pip install git+https://github.com/ROCm/pyrsmi.git
  ```
- Or install a specific branch or tag:
  ```bash
  # Install from a specific branch
  pip install git+https://github.com/ROCm/pyrsmi.git@branch-name
  
  # Install a specific release tag
  pip install git+https://github.com/ROCm/pyrsmi.git@v1.0.0
  ```

## How to use `pyrsmi`

### Environment Setup

`pyrsmi` searches for the AMD SMI library (`libamd_smi.so`) using the `ROCM_PATH` environment variable. For standard ROCm installations, the library is automatically detected at `/opt/rocm/lib/libamd_smi.so`.

If your ROCm installation is in a non-standard location:
```bash
export ROCM_PATH=/path/to/your/rocm
```

### Quick Start

```python
from pyrsmi import rocml

# Initialize the library
rocml.smi_initialize()

# Get device count
num_gpus = rocml.smi_get_device_count()
print(f"Found {num_gpus} GPU(s)")

# Get device information
for i in range(num_gpus):
    name = rocml.smi_get_device_name(i)
    memory = rocml.smi_get_device_memory_total(i) / (1024**3)  # Convert to GB
    util = rocml.smi_get_device_utilization(i)
    power = rocml.smi_get_device_average_power(i)
    
    print(f"GPU {i}: {name}")
    print(f"  Memory: {memory:.1f} GB")
    print(f"  Utilization: {util}%")
    print(f"  Power: {power:.1f} W")

# Shutdown the library
rocml.smi_shutdown()
```

### Key Points

- **Always call `smi_initialize()`** before using any other functions
- **Always call `smi_shutdown()`** when finished to release resources
- Device indices are **zero-based** (0, 1, 2, ...)
- All functions return **-1 or empty string** on error (check return values!)
- Functions are **thread-safe** when properly initialized

## Examples
- Examples directory contains a number of code snippets showing how to use the package.
- It also contains an example showing how to use pyrsmi to create a web-based system monitoring tool that displays various dashboards of system status, including memory, CPU/GPU utilization and process names. 

## API Reference

### Core Functions

| Function | Description | Arguments | Return Type | Notes |
| -------- | ----------- | --------- | ----------- | ----- |
| `smi_initialize()` | Initialize AMD SMI library | None | None | **Required** before any other calls |
| `smi_shutdown()` | Shut down AMD SMI library | None | None | Release resources when finished |

### Device Information

| Function | Description | Arguments | Return Type | Notes |
| -------- | ----------- | --------- | ----------- | ----- |
| `smi_get_device_count()` | Get number of GPU devices | None | int | Total GPUs in system |
| `smi_get_device_name(dev)` | Get GPU market name | device_id | str | e.g., "AMD Instinct MI300X" |
| `smi_get_device_id(dev)` | Get device ID | device_id | int | PCI device ID |
| `smi_get_device_revision(dev)` | Get device revision | device_id | int | ASIC revision |
| `smi_get_device_unique_id(dev)` | Get unique device ID (BDF) | device_id | int | 64-bit BDF identifier |
| `smi_get_device_uuid(dev, format)` | Get device UUID | device_id, format | str | format: 'roc', 'raw', or 'nv' |

### Memory Functions

| Function | Description | Arguments | Return Type | Notes |
| -------- | ----------- | --------- | ----------- | ----- |
| `smi_get_device_memory_total(dev, type)` | Get total memory | device_id, type | int | Bytes; type: 'VRAM', 'VIS_VRAM', 'GTT' |
| `smi_get_device_memory_used(dev, type)` | Get used memory | device_id, type | int | Bytes; type: 'VRAM', 'VIS_VRAM', 'GTT' |
| `smi_get_device_memory_busy(dev)` | Get memory busy percentage | device_id | int | % time accessing memory |
| `smi_get_device_memory_reserved_pages(dev)` | Get reserved pages info | device_id | tuple | (num_pages, records) |

### Utilization and Power

| Function | Description | Arguments | Return Type | Notes |
| -------- | ----------- | --------- | ----------- | ----- |
| `smi_get_device_utilization(dev)` | Get GPU utilization | device_id | int | % busy (GFX activity) |
| `smi_get_device_average_power(dev)` | Get average power | device_id | float | Watts |
| `smi_get_device_fan_rpms(dev, index)` | Get fan RPM | device_id, sensor | int | RPM (may not be supported) |
| `smi_get_device_fan_speed(dev, index)` | Get fan speed | device_id, sensor | int | % of max |
| `smi_get_device_fan_speed_max(dev, index)` | Get max fan speed | device_id, sensor | int | Maximum RPM |

### PCIe and Topology

| Function | Description | Arguments | Return Type | Notes |
| -------- | ----------- | --------- | ----------- | ----- |
| `smi_get_device_pcie_bandwidth(dev)` | Get PCIe bandwidth info | device_id | pcie_info_t | Complete PCIe structure |
| `smi_get_device_pci_id(dev)` | Get PCI BDF ID | device_id | int | 64-bit BDF |
| `smi_get_device_pcie_throughput(dev)` | Get PCIe throughput | device_id | int | Bytes/sec |
| `smi_get_device_pci_replay_counter(dev)` | Get PCIe replay count | device_id | int | Link errors |
| `smi_get_device_topo_numa_affinity(dev)` | Get NUMA node | device_id | int | NUMA affinity |
| `smi_get_device_topo_link_weight(src, dst)` | Get link weight | src_id, dst_id | int | Topology distance |
| `smi_get_device_link_type(src, dst)` | Get link type and hops | src_id, dst_id | tuple | (hops, link_type) |
| `smi_is_device_p2p_accessible(src, dst)` | Check P2P accessibility | src_id, dst_id | bool | DMA supported? |
| `smi_get_device_minmax_bandwidth(src, dst)` | Get min/max bandwidth | src_id, dst_id | tuple | (min, max) in bytes/sec |

### Compute Partitioning

| Function | Description | Arguments | Return Type | Notes |
| -------- | ----------- | --------- | ----------- | ----- |
| `smi_get_device_compute_partition(dev)` | Get compute partition | device_id | str | e.g., 'SPX', 'CPX' |
| `smi_get_device_memory_partition(dev)` | Get memory partition | device_id | str | e.g., 'NPS1', 'NPS4' |

### Process Management

| Function | Description | Arguments | Return Type | Notes |
| -------- | ----------- | --------- | ----------- | ----- |
| `smi_get_device_compute_process()` | Get compute processes | None | List[int] | PIDs of GPU processes |

### XGMI

| Function | Description | Arguments | Return Type | Notes |
| -------- | ----------- | --------- | ----------- | ----- |
| `smi_get_device_xgmi_error_status(dev)` | Get XGMI error status | device_id | int | Error count |
| `smi_reset_device_xgmi_error(dev)` | Reset XGMI errors | device_id | bool | Success status |

**Note:** This list covers the main functions. For complete API documentation, see the source code or inline docstrings.
