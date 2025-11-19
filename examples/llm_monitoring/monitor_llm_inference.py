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
LLM Inference Monitoring Example

This example demonstrates how to monitor GPU metrics (utilization, memory, power)
during LLM inference using pyrsmi.

Requirements:
    pip install torch transformers pyrsmi

Usage:
    python monitor_llm_inference.py
    python monitor_llm_inference.py --device 0 --interval 0.1
    python monitor_llm_inference.py --prompt "Explain quantum computing"
"""

import time
import threading
import argparse
from collections import defaultdict
from typing import Dict, List
from pyrsmi import rocml


class GPUMonitor:
    """Monitor GPU metrics in a background thread."""
    
    def __init__(self, device_id: int = 0, interval: float = 0.1):
        """
        Initialize GPU monitor.
        
        Args:
            device_id: GPU device index to monitor
            interval: Sampling interval in seconds
        """
        self.device_id = device_id
        self.interval = interval
        self.monitoring = False
        self.thread = None
        
        # Storage for metrics
        self.metrics: Dict[str, List[float]] = defaultdict(list)
        self.timestamps: List[float] = []
        
        # Initialize rocml
        rocml.smi_initialize()
        
    def start(self):
        """Start monitoring in background thread."""
        self.monitoring = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
        print(f"Started monitoring GPU {self.device_id} (interval: {self.interval}s)")
        
    def stop(self):
        """Stop monitoring and wait for thread to finish."""
        self.monitoring = False
        if self.thread:
            self.thread.join()
        print(f"Stopped monitoring GPU {self.device_id}")
        
    def _monitor_loop(self):
        """Main monitoring loop (runs in background thread)."""
        start_time = time.time()
        
        while self.monitoring:
            timestamp = time.time() - start_time
            self.timestamps.append(timestamp)
            
            # GPU utilization (%)
            util = rocml.smi_get_device_utilization(self.device_id)
            self.metrics['utilization'].append(util if util != -1 else 0)
            
            # Memory usage (MB)
            mem_used = rocml.smi_get_device_memory_used(self.device_id) / 1e6
            self.metrics['memory_used_mb'].append(mem_used if mem_used > 0 else 0)
            
            # Memory total (MB)
            mem_total = rocml.smi_get_device_memory_total(self.device_id) / 1e6
            self.metrics['memory_total_mb'].append(mem_total if mem_total > 0 else 0)
            
            # Power consumption (W) - already in Watts, no conversion needed
            power = rocml.smi_get_device_average_power(self.device_id)
            self.metrics['power_w'].append(power if power > 0 else 0)
            
            time.sleep(self.interval)
    
    def get_summary(self) -> Dict[str, Dict[str, float]]:
        """Get summary statistics for collected metrics."""
        summary = {}
        
        for metric_name, values in self.metrics.items():
            if values:
                summary[metric_name] = {
                    'min': min(values),
                    'max': max(values),
                    'avg': sum(values) / len(values),
                    'samples': len(values)
                }
        
        return summary
    
    def print_summary(self):
        """Print a formatted summary of collected metrics."""
        if not self.timestamps:
            print("No metrics collected")
            return
        
        duration = self.timestamps[-1]
        summary = self.get_summary()
        
        print("\n" + "="*70)
        print(f"GPU Monitoring Summary (Device {self.device_id})")
        print("="*70)
        print(f"Duration: {duration:.2f} seconds")
        print(f"Samples: {len(self.timestamps)}")
        print("-"*70)
        
        # GPU Utilization
        if 'utilization' in summary:
            util = summary['utilization']
            print(f"GPU Utilization (%)")
            print(f"  Min: {util['min']:6.1f}%  |  Max: {util['max']:6.1f}%  |  Avg: {util['avg']:6.1f}%")
        
        # Memory Usage
        if 'memory_used_mb' in summary:
            mem = summary['memory_used_mb']
            total = summary['memory_total_mb']['avg']
            print(f"Memory Usage (MB)")
            print(f"  Min: {mem['min']:8.1f}  |  Max: {mem['max']:8.1f}  |  Avg: {mem['avg']:8.1f}")
            print(f"  Total Memory: {total:.1f} MB")
            print(f"  Peak Usage: {(mem['max']/total)*100:.1f}% of total")
        
        # Power Consumption
        if 'power_w' in summary:
            power = summary['power_w']
            print(f"Power Consumption (W)")
            print(f"  Min: {power['min']:6.1f}W  |  Max: {power['max']:6.1f}W  |  Avg: {power['avg']:6.1f}W")
            
            # Energy estimation
            energy_wh = power['avg'] * (duration / 3600)
            print(f"  Estimated Energy: {energy_wh:.4f} Wh")
        
        print("="*70)
    
    def print_timeseries(self, max_rows: int = 20):
        """Print time-series data in tabular format."""
        if not self.timestamps:
            print("No metrics collected")
            return
        
        print("\n" + "="*90)
        print(f"Time-Series Data (Device {self.device_id})")
        print("="*90)
        print(f"{'Time(s)':>8} | {'GPU(%)':>7} | {'Memory(MB)':>12} | {'Memory(%)':>10} | {'Power(W)':>9}")
        print("-"*90)
        
        # Sample data if too many points
        step = max(1, len(self.timestamps) // max_rows)
        
        for i in range(0, len(self.timestamps), step):
            t = self.timestamps[i]
            util = self.metrics['utilization'][i]
            mem_used = self.metrics['memory_used_mb'][i]
            mem_total = self.metrics['memory_total_mb'][i]
            mem_pct = (mem_used / mem_total * 100) if mem_total > 0 else 0
            power = self.metrics['power_w'][i]
            
            print(f"{t:8.2f} | {util:7.1f} | {mem_used:12.1f} | {mem_pct:10.1f} | {power:9.1f}")
        
        print("="*90)
    
    def shutdown(self):
        """Shutdown rocml."""
        rocml.smi_shutdown()


def run_llm_inference(prompt: str, max_length: int = 100):
    """
    Run LLM inference (requires torch and transformers).
    
    Args:
        prompt: Input prompt for the LLM
        max_length: Maximum length of generated text
    
    Returns:
        Generated text
    """
    try:
        import torch
        from transformers import AutoTokenizer, AutoModelForCausalLM
        
        print("Loading model...")
        # Using a small model for demonstration (download ~500MB on first run)
        model_name = "gpt2"  # You can change to larger models like "meta-llama/Llama-2-7b-hf"
        
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            dtype=torch.float16,
            device_map="auto"
        )
        
        print(f"Model loaded: {model_name}")
        print(f"Prompt: {prompt}")
        print("-" * 70)
        
        # Tokenize input
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        
        # Generate
        print("Generating...")
        outputs = model.generate(
            **inputs,
            max_length=max_length,
            num_return_sequences=1,
            temperature=0.7,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id
        )
        
        # Decode output
        generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        print("\nGenerated Text:")
        print("="*70)
        print(generated_text)
        print("="*70)
        
        return generated_text
        
    except ImportError:
        print("ERROR: torch and transformers are required for LLM inference")
        print("Install with: pip install torch transformers")
        print("\nRunning dummy workload instead...")
        
        # Dummy workload for testing monitoring without LLM
        import torch
        if torch.cuda.is_available():
            device = torch.device("cuda")
            # Create some GPU activity
            for _ in range(10):
                x = torch.randn(5000, 5000, device=device)
                y = torch.matmul(x, x.T)
                torch.cuda.synchronize()
                time.sleep(0.5)
        else:
            print("No GPU available, sleeping for 5 seconds...")
            time.sleep(5)
        
        return "Dummy workload completed"


def main():
    parser = argparse.ArgumentParser(
        description="Monitor GPU metrics during LLM inference"
    )
    parser.add_argument(
        '--device', 
        type=int, 
        default=0,
        help='GPU device ID to monitor (default: 0)'
    )
    parser.add_argument(
        '--interval',
        type=float,
        default=0.1,
        help='Monitoring interval in seconds (default: 0.1)'
    )
    parser.add_argument(
        '--prompt',
        type=str,
        default="Once upon a time in a distant galaxy",
        help='Input prompt for LLM'
    )
    parser.add_argument(
        '--max-length',
        type=int,
        default=100,
        help='Maximum length of generated text (default: 100)'
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
        # Start monitoring
        monitor.start()
        
        # Run LLM inference
        run_llm_inference(args.prompt, args.max_length)
        
        # Small delay to capture post-inference metrics
        time.sleep(1.0)
        
        # Stop monitoring
        monitor.stop()
        
        # Print results
        monitor.print_summary()
        
        if args.show_timeseries:
            monitor.print_timeseries()
        
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

