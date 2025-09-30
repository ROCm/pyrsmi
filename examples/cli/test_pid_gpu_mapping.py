# MIT License
#
# Copyright (c) 2023 Advanced Micro Devices, Inc.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from pyrsmi.rocml import smi_initialize, smi_shutdown, smi_get_process_gpu_mapping
import subprocess
import sys


def main():
    print("Testing PID-to-GPU mapping functionality...")
    print("=" * 50)

    try:
        # Initialize ROCm library
        smi_initialize()

        print("\nTesting smi_get_process_gpu_mapping() directly...")
        pid_gpu_map = smi_get_process_gpu_mapping()

        if pid_gpu_map:
            print(f"Found {len(pid_gpu_map)} process(es) using GPUs:")
            for pid, gpus in pid_gpu_map.items():
                try:
                    # Get process name using ps
                    result = subprocess.run(['ps', '-p', str(pid), '-o', 'comm='],
                                          capture_output=True, text=True)
                    proc_name = result.stdout.strip() if result.returncode == 0 else "unknown"
                except:
                    proc_name = "unknown"

                print(f"  PID {pid} ({proc_name}): using GPU(s) {gpus}")
        else:
            print("No GPU-using processes found.")

        print("\nComparing with direct rocm-smi output:")
        print("-" * 40)
        try:
            result = subprocess.run(['rocm-smi', '--showpidgpus'],
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print(result.stdout)
            else:
                print(f"rocm-smi failed: {result.stderr}")
        except subprocess.TimeoutExpired:
            print("rocm-smi command timed out")
        except Exception as e:
            print(f"Error running rocm-smi: {e}")

        # Shutdown ROCm library
        smi_shutdown()

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
