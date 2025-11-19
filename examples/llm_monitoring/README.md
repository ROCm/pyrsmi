# LLM Inference Monitoring Example

This example demonstrates how to use `pyrsmi` to monitor GPU metrics during LLM inference workloads.

## Examples Included

1. **`monitor_llm_inference.py`** - Monitor GPU during LLM inference (requires transformers)
2. **`simple_workload_monitor.py`** - Quick test with simple GPU workload (no LLM needed)

## Features

- **Real-time monitoring** of GPU utilization, memory usage, and power consumption
- **Background thread** for non-intrusive metric collection
- **Time-series data** collection at configurable intervals
- **Summary statistics** (min, max, average)
- **Energy estimation** based on power consumption
- Works with any PyTorch-based LLM

## Requirements

⚠️ **For AMD GPUs**: Standard pip installation of PyTorch installs CUDA (NVIDIA) version by default. For AMD ROCm systems, use one of the methods below.

### Method 1: ROCm PyTorch Container (Recommended)

The easiest way to run these examples on AMD GPUs:

```bash
# Pull ROCm PyTorch container
docker pull rocm/pytorch:latest

# Run container with GPU access
docker run -it --rm \
  --privileged --network=host --ipc=host \
  --device=/dev/kfd --device=/dev/dri \
  --group-add video --cap-add=SYS_PTRACE \
  --security-opt seccomp=unconfined \
  -v $(pwd):/workspace -w /workspace \
  rocm/pytorch:latest

# Inside container, install dependencies
pip install transformers accelerate pyrsmi
```

### Method 2: Install ROCm PyTorch via pip

```bash
# Install ROCm-compatible PyTorch
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/rocm6.1

# Then install other dependencies
pip install transformers accelerate pyrsmi
```

### For Testing Only (Simple Workload)

If you just want to test monitoring without GPU workload:

```bash
pip install pyrsmi  # Monitoring works without PyTorch
```

## Quick Start

### Test Monitoring Without GPU Workload

```bash
# This works without PyTorch - just monitors the GPU
python simple_workload_monitor.py --duration 5
```

### Test with Simple GPU Workload

```bash
# Requires ROCm PyTorch (see installation above)
python simple_workload_monitor.py --duration 10 --show-timeseries
```

This runs a simple matrix multiplication workload to demonstrate monitoring capabilities.

## Usage

### Basic LLM Monitoring

**Using ROCm Container (Recommended):**

```bash
# Start container with current directory mounted
docker run -it --rm \
  --privileged \
  --network=host \
  --ipc=host \
  --device=/dev/kfd --device=/dev/dri \
  --group-add video \
  --cap-add=SYS_PTRACE \
  --security-opt seccomp=unconfined \
  -v $(pwd):/workspace -w /workspace \
  rocm/pytorch:latest bash

# Inside container:
pip install transformers accelerate pyrsmi
python monitor_llm_inference.py
```

**If you have ROCm PyTorch installed locally:**

```bash
python monitor_llm_inference.py
```

### Custom Prompt

```bash
python monitor_llm_inference.py --prompt "Explain quantum computing in simple terms"
```

### Specific GPU Device

```bash
python monitor_llm_inference.py --device 1
```

### High-Resolution Monitoring

```bash
python monitor_llm_inference.py --interval 0.05  # Sample every 50ms
```

### Show Detailed Time-Series

```bash
python monitor_llm_inference.py --show-timeseries
```

### Full Example

```bash
python monitor_llm_inference.py \
    --device 0 \
    --interval 0.1 \
    --prompt "Write a poem about artificial intelligence" \
    --max-length 150 \
    --show-timeseries
```

## Example Output

```
Started monitoring GPU 0 (interval: 0.1s)
Loading model...
Model loaded: gpt2
Prompt: Once upon a time in a distant galaxy
----------------------------------------------------------------------
Generating...

Generated Text:
======================================================================
Once upon a time in a distant galaxy, there lived a young warrior...
======================================================================
Stopped monitoring GPU 0

======================================================================
GPU Monitoring Summary (Device 0)
======================================================================
Duration: 5.43 seconds
Samples: 54
----------------------------------------------------------------------
GPU Utilization (%)
  Min:    0.0%  |  Max:  100.0%  |  Avg:   67.3%
Memory Usage (MB)
  Min:   2341.5  |  Max:  3876.2  |  Avg:  3512.8
  Total Memory: 65536.0 MB
  Peak Usage: 5.9% of total
Power Consumption (W)
  Min:  145.3W  |  Max:  387.6W  |  Avg:  312.4W
  Estimated Energy: 0.4711 Wh
======================================================================
```

## Use Cases

### 1. Performance Profiling

Monitor GPU efficiency during different inference configurations:

```bash
# Test different batch sizes
python monitor_llm_inference.py --max-length 50
python monitor_llm_inference.py --max-length 200
python monitor_llm_inference.py --max-length 500
```

### 2. Energy Efficiency Analysis

Compare energy consumption across different models:

```bash
# Small model
python monitor_llm_inference.py  # GPT-2

# Larger model (modify script to use different model)
# Edit model_name in run_llm_inference() function
```

### 3. Multi-GPU Monitoring

Monitor different GPUs in separate terminals:

```bash
# Terminal 1
python monitor_llm_inference.py --device 0

# Terminal 2
python monitor_llm_inference.py --device 1
```

### 4. Continuous Monitoring

For long-running inference workloads, use high-frequency sampling:

```bash
python monitor_llm_inference.py --interval 0.05 --max-length 1000
```

## Integration with Your Code

You can easily integrate the `GPUMonitor` class into your own LLM applications:

```python
from monitor_llm_inference import GPUMonitor

# Initialize monitor
monitor = GPUMonitor(device_id=0, interval=0.1)

# Start monitoring
monitor.start()

# Your LLM inference code here
# ...

# Stop monitoring
monitor.stop()

# Get results
summary = monitor.get_summary()
print(f"Average GPU utilization: {summary['utilization']['avg']:.1f}%")
print(f"Peak memory usage: {summary['memory_used_mb']['max']:.1f} MB")

# Cleanup
monitor.shutdown()
```

## Tips

1. **Sampling Interval**: Use 0.1s for general monitoring, 0.05s for high-resolution profiling
2. **Device Selection**: Check available devices with `rocm-smi` first
3. **Model Selection**: Modify `model_name` in the script to use different models
4. **Memory**: Ensure your GPU has enough memory for the model (GPT-2 needs ~500MB)

**Note on Power Monitoring:** Power monitoring uses `amdsmi_get_power_info()` which returns current socket power in Watts. This works on most AMD GPUs including MI350X series.

## Troubleshooting

**Issue**: "No GPU available" or PyTorch not detecting AMD GPUs
- **Solution**: You likely installed CUDA PyTorch. Use ROCm PyTorch container or install ROCm PyTorch:
  ```bash
  pip install torch --index-url https://download.pytorch.org/whl/rocm6.1
  ```
- **Verify**: `python -c "import torch; print(torch.cuda.is_available())"`
- **Check GPUs**: `rocm-smi` should list your GPUs

**Issue**: "torch and transformers are required" or "accelerate is required"
- **Solution**: `pip install transformers accelerate`

**Issue**: Model download is slow
- **Solution**: First run downloads model from HuggingFace (~500MB), subsequent runs use cached model

**Issue**: High memory usage
- **Solution**: Use smaller models or reduce `max_length`

**Issue**: Power consumption shows 0.0W (Fixed in v1.0.0)
- **Previous Issue**: Earlier versions had a unit conversion bug
- **Now Fixed**: Power monitoring works correctly with `amdsmi_get_power_info()`
- **Verify**: Compare with `rocm-smi --showpower` to confirm readings

**Issue**: Docker permission errors
- **Solution**: Add your user to the `video` and `render` groups:
  ```bash
  sudo usermod -a -G video,render $USER
  newgrp video
  ```

## Advanced Usage

### Custom Models

Edit the script to use any HuggingFace model:

```python
model_name = "meta-llama/Llama-2-7b-hf"  # Requires ~14GB GPU memory
# or
model_name = "facebook/opt-350m"  # Smaller alternative
```

### Export Metrics

Save time-series data to CSV:

```python
import csv

# After monitoring
with open('gpu_metrics.csv', 'w') as f:
    writer = csv.writer(f)
    writer.writerow(['Time', 'Utilization', 'Memory', 'Power'])
    for i in range(len(monitor.timestamps)):
        writer.writerow([
            monitor.timestamps[i],
            monitor.metrics['utilization'][i],
            monitor.metrics['memory_used_mb'][i],
            monitor.metrics['power_w'][i]
        ])
```

## Related Examples

- `../cli/device_info.py` - Basic device information
- `../system_dashboard/` - System-wide monitoring dashboard

