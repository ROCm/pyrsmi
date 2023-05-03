# Examples of using `pyrsmi` package

## `cli` Directory

- Displays selected info of the available devices
  - `python device_info.py`
  - Output:

```
no. of devices = 2

device id       device name                     total memory(GB)  used memory(MB)
--------------------------------------------------------------------------------
     0    AMD INSTINCT MI250 (MCM) OAM AC MBA           68.70           11.24
     1    AMD INSTINCT MI250 (MCM) OAM AC MBA           68.70           11.24

```

----------

## `system_dashboard` Directory
- Web-based dashboards that shows sytem status of CPU, GPU, memory and network. It uses [Bokeh server](https://docs.bokeh.org/en/latest/docs/user_guide/server.html) for real-time processing of system data along with pyrsmi (GPU) and psutil (CPU).

### Setup
- Get a ROCm-enabled AMD GPU system
- Create Python virtual environment (tested on Python 3.9.13):<br>
  `python -m venv [virt env name]`
- Activate the virtual environment: <br>
  `source [virt env name]/bin/activate`
- Install `pyrsmi` package (from PyPI)
- Check ROCm availability by running cli app (optional):<br>
  `python ../cli/device_info.py`
- Install required packages:<br>
  `python -m pip install -r requirements.txt`
- Start the server:<br>
  `python server.py [port]`
- Set up port forwarding for remote view (default port: 5006)
- Open the browser: https://localhost:[port | 5006]

### Results
- System dashboard front page:
  ![system dashboard fron page](imgs/system_dashboard_root.JPG "Front Page")
- System Resources sample (CPU + GPU):
  ![System Resource page](imgs/system_dashboard_system_resources.JPG "Resources CPU + GPU")
- GPU Utilization sample:
  ![GPU utilization page](imgs/system_dashboard_gpu_util.JPG "GPU Utilization")
- CPU Utilization sample:
  ![CPU utilization page](imgs/system_dashboard_cpu_util.JPG "CPU Utilization")

  