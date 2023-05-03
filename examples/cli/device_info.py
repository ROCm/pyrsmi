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
