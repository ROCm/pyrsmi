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

from pyrsmi import rocml


def main():
    rocml.smi_initialize()

    ngpus = rocml.smi_get_device_count()

    device_names = [rocml.smi_get_device_name(d) for d in range(ngpus)]

    mem_total = [rocml.smi_get_device_memory_total(d) * 1e-9 for d in range(ngpus)]

    mem_used = [rocml.smi_get_device_memory_used(d) * 1e-6 for d in range(ngpus)]

    print(f'no. of devices = {ngpus}\n')
    print('device id\tdevice name\t\t\ttotal memory(GB)  used memory(MB)')
    print('-' * 80)
    for i, d in enumerate(range(ngpus)):
        print(f'{i:6}    {device_names[i]}\t\t{mem_total[i]:.2f}\t\t{mem_used[i]:.2f}')

    rocml.smi_shutdown()


if __name__ == '__main__':
    main()
