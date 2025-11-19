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

"""
Simple GPU Workload Monitor

A lightweight example that monitors GPU metrics during a simple PyTorch workload.
No LLM models required - just demonstrates the monitoring capabilities.

Requirements:
    pip install torch pyrsmi

Usage:
    python simple_workload_monitor.py
    python simple_workload_monitor.py --device 0 --duration 10
"""

import time
import argparse
from monitor_llm_inference import GPUMonitor


def run_simple_workload(duration: float = 5.0, device: int = 0):
    """
    Run a simple GPU workload for demonstration.
    
    Args:
        duration: How long to run the workload (seconds)
        device: GPU device index
    """
    try:
        import torch
        
        if not torch.cuda.is_available():
            print("ERROR: No GPU available")
            print("Falling back to sleep mode...")
            time.sleep(duration)
            return
        
        device_obj = torch.device(f"cuda:{device}")
        print(f"Running GPU workload on device {device} for {duration} seconds...")
        print("Performing matrix multiplications...\n")
        
        start_time = time.time()
        iteration = 0
        
        while time.time() - start_time < duration:
            # Create random matrices and perform operations
            size = 4000
            a = torch.randn(size, size, device=device_obj, dtype=torch.float32)
            b = torch.randn(size, size, device=device_obj, dtype=torch.float32)
            
            # Matrix multiplication (GPU intensive)
            c = torch.matmul(a, b)
            
            # Add some memory operations
            d = c * 2.0 + torch.sin(a)
            
            # Ensure operations complete
            torch.cuda.synchronize()
            
            iteration += 1
            
            # Brief pause between iterations
            time.sleep(0.1)
        
        elapsed = time.time() - start_time
        print(f"Completed {iteration} iterations in {elapsed:.2f} seconds")
        print(f"Average iteration time: {elapsed/iteration*1000:.1f} ms\n")
        
    except ImportError:
        print("ERROR: PyTorch is required")
        print("Install with: pip install torch")
        print("\nFalling back to sleep mode...")
        time.sleep(duration)
    except Exception as e:
        print(f"Error during workload: {e}")
        time.sleep(duration)


def main():
    parser = argparse.ArgumentParser(
        description="Monitor GPU metrics during a simple workload"
    )
    parser.add_argument(
        '--device', 
        type=int, 
        default=0,
        help='GPU device ID to monitor (default: 0)'
    )
    parser.add_argument(
        '--duration',
        type=float,
        default=5.0,
        help='Workload duration in seconds (default: 5.0)'
    )
    parser.add_argument(
        '--interval',
        type=float,
        default=0.1,
        help='Monitoring interval in seconds (default: 0.1)'
    )
    parser.add_argument(
        '--show-timeseries',
        action='store_true',
        help='Show detailed time-series data'
    )
    
    args = parser.parse_args()
    
    # Initialize monitor
    monitor = GPUMonitor(device_id=args.device, interval=args.interval)
    
    try:
        print("="*70)
        print("GPU Workload Monitoring Example")
        print("="*70)
        print(f"Device: {args.device}")
        print(f"Duration: {args.duration} seconds")
        print(f"Monitoring interval: {args.interval} seconds")
        print("="*70)
        print()
        
        # Start monitoring
        monitor.start()
        
        # Run workload
        run_simple_workload(duration=args.duration, device=args.device)
        
        # Small delay to capture final metrics
        time.sleep(0.5)
        
        # Stop monitoring
        monitor.stop()
        
        # Print results
        monitor.print_summary()
        
        if args.show_timeseries:
            monitor.print_timeseries()
        
        print("\n💡 TIP: Try running with --show-timeseries to see detailed metrics")
        
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        monitor.stop()
    except Exception as e:
        print(f"Error: {e}")
        monitor.stop()
    finally:
        monitor.shutdown()


if __name__ == '__main__':
    main()

