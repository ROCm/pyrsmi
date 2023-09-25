# pyrsmi
### Python Bindings for System Management Library for AMD GPUs
--------
- `pyrsmi` is a python package of rocm-smi-lib, for providing a limited features of ROCm System Management Library for assisting Python development involving AMD GPUs.
- It is based on (`rocm-smi-lib`)[https://github.com/RadeonOpenCompute/rocm_smi_lib], so its scope of support should be similar to that of the latter.

## Requirements
- `pyrsmi` runs on latest ROCm-supported Instinct MI-series GPU systems. Scope of tested systems is limited; please create tickets for any issues encountered.

## How to install from source
- Clone this repo: 
  - `git clone https://github.com/AMD-AI/pyrsmi.git`
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
- **NOTE:** Until the package becomes available at the official PyPI repo, the package is available from **test PyPI** site:
- `python -m pip install --index-url https://test.pypi.org/simple pyrsmi`
- When the release version become available at pypi.org site, the package can be installed with :
  -  `python -m pip install pyrsmi`

## How to use `pyrsmi`
- In python:
```python
from pyrsmi import rocml

rocml.smi_initialize()
print(rocml.smi_get_device_count())
rocml.smi_shutdown()
```

## Examples
- Examples directory contains a number of code snippets showing how to use the package.
- It also contains an example showing how to use pyrsmi to create a web-based system monitoring tool that displays various dashboards of system status, including memory, CPU/GPU utilization and process names. 

## List of API functions

| Function | Description | Argument | Return Type | Note |
| -------- | ----------- | -------  | ----------  | ---- |
| smi_initialize | initialize rsmi | None | None |  |
| smi_shutdown   | shut down rsmi  | None | None |  |
| smi_get_version | get version of rsmi  | None | str | 'major.minor.patch' |
| smi_get_kernel_version | get version of ROCm kernel driver  | None | str | |
| smi_get_device_count | get number of GPU devices  | None | int | num of devices |
| smi_get_device_name  | get name of GPU devices  | None | str | |
| smi_get_device_unique_id   | get unique id of GPU devices  | None | int | 64bit integer |
| smi_get_device_utilization | get device utilization in % busy | device_id | int |  |
| smi_get_device_memory_used | get device memory usage | device_id | int | in Bytes, type 'VRAM' |
| smi_get_device_memory_total | get device's total memory | device_id | int | in Bytes, type 'VRAM' |
| smi_get_device_pcie_bandwidth | get device's estimated PCIe bandwidth | device_id | float | in Bytes/sec |
| smi_get_device_compute_process | get list of pid of processes running on dev | device_id | List[int] |  |
| smi_get_device_average_power | get device's average power | device_id | float | power in Watt |
