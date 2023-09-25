import math
import psutil
import sys
import time
from bokeh.plotting import figure, ColumnDataSource
from bokeh.models import DataRange1d, NumeralTickFormatter, BasicTicker
from bokeh.layouts import column
from bokeh.models.mappers import LinearColorMapper
from bokeh.palettes import all_palettes

from apps.utils import format_bytes
from pyrsmi import rocml


rocml.smi_initialize()

ngpus = rocml.smi_get_device_count()
devices = list(range(ngpus))

def get_utilization():
    return [rocml.smi_get_device_utilization(d) for d in devices]

def get_mem():
    return [rocml.smi_get_device_memory_used(d) for d in devices]

def get_total():
    return rocml.smi_get_device_memory_total(devices[0])

def get_mem_list():
    return [rocml.smi_get_device_memory_total(d) / (1024 * 1024) for d in devices]

KB = 1e3
MB = KB * KB
GB = MB * KB


def gpu(doc):
    fig = figure(title='GPU Utilization', sizing_mode='stretch_both', x_range=[0, 100])

    gpu = get_utilization()
    y = list(range(len(gpu)))
    source = ColumnDataSource({'right': y, 'gpu': gpu})
    mapper = LinearColorMapper(palette=all_palettes['RdYlBu'][4], low=0, high=100)

    fig.hbar(
        source=source,
        y='right',
        right='gpu',
        height=0.8,
        color={'field': 'gpu', 'transform': mapper},
    )

    fig.toolbar_location = None

    doc.title = 'GPU Utilization [%]'
    doc.add_root(fig)

    def cb():
        # print(f'gpu util = {gpu}')
        source.data.update({'gpu': get_utilization()})

    doc.add_periodic_callback(cb, 200)


def gpu_mem(doc):
    fig = figure(
        title='GPU Memory', sizing_mode='stretch_both', x_range=[0, get_total()]
    )

    gpu = get_mem()

    y = list(range(len(gpu)))
    source = ColumnDataSource({'right': y, 'gpu': gpu})
    mapper = LinearColorMapper(
        palette=all_palettes['RdYlBu'][8], low=0, high=get_total()
    )

    fig.hbar(
        source=source,
        y='right',
        right='gpu',
        height=0.8,
        color={'field': 'gpu', 'transform': mapper},
    )
    fig.xaxis[0].formatter = NumeralTickFormatter(format='0.0 b')
    fig.xaxis.major_label_orientation = -math.pi / 12

    fig.toolbar_location = None

    doc.title = 'GPU Memory'
    doc.add_root(fig)

    def cb():
        mem = get_mem()
        source.data.update({'gpu': mem})
        fig.title.text = 'GPU Memory: {}'.format(format_bytes(sum(mem)))

    doc.add_periodic_callback(cb, 200)


def gpu_resource_timeline(doc):

    memory_list = get_mem_list()

    gpu_mem_max = max(memory_list) * (1024 * 1024)
    gpu_mem_sum = sum(memory_list)

    # Shared X Range for all plots
    x_range = DataRange1d(follow='end', follow_interval=20000, range_padding=0)
    tools = 'reset,xpan,xwheel_zoom'

    item_dict = {
        'time': [],
        'gpu-total': [],
        'memory-total': [],
        'rx-total': [],
        'tx-total': [],
    }
    for i in range(ngpus):
        item_dict['gpu-' + str(i)] = []
        item_dict['memory-' + str(i)] = []

    source = ColumnDataSource(item_dict)

    def _get_color(ind):
        color_list = [
            'blue',
            'red',
            'green',
            'black',
            'brown',
            'cyan',
            'orange',
            'pink',
            'purple',
            'gold',
        ]
        return color_list[ind % len(color_list)]

    memory_fig = figure(
        title='Memory Utilization (per Device) [B]',
        sizing_mode='stretch_both',
        x_axis_type='datetime',
        y_range=[0, gpu_mem_max],
        x_range=x_range,
        tools=tools,
    )
    for i in range(ngpus):
        memory_fig.line(
            source=source, x='time', y='memory-' + str(i), color=_get_color(i),
            line_width=3,
        )
    memory_fig.yaxis.formatter = NumeralTickFormatter(format='0.0 b')

    gpu_fig = figure(
        title='GPU Utilization (per Device) [%]',
        sizing_mode='stretch_both',
        x_axis_type='datetime',
        y_range=[0, 100],
        x_range=x_range,
        tools=tools,
    )
    for i in range(ngpus):
        gpu_fig.line(
            source=source, x='time', y='gpu-' + str(i), color=_get_color(i),
            line_width=3,
        )

    tot_fig = figure(
        title='Total Utilization [%]',
        sizing_mode='stretch_both',
        x_axis_type='datetime',
        y_range=[0, 100],
        x_range=x_range,
        tools=tools,
    )
    tot_fig.line(
        source=source, x='time', y='gpu-total', color='blue', legend_label='Total-GPU',
        line_width=3,
    )
    tot_fig.line(
        source=source, x='time', y='memory-total', color='red', legend_label='Total-Memory',
        line_width=3,
    )
    # tot_fig.legend.location = 'top_left'

    figures = [gpu_fig, memory_fig, tot_fig]
    doc.title = 'Resource Timeline'
    doc.add_root(
        column(*figures, sizing_mode='stretch_both')
    )

    last_time = time.time()

    def cb():
        nonlocal last_time
        now = time.time()
        src_dict = {'time': [now * 1000]}
        gpu_tot = 0
        mem_tot = 0
        tx_tot = 0
        rx_tot = 0
        for i in range(ngpus):
            gpu = rocml.smi_get_device_utilization(devices[i])
            mem = rocml.smi_get_device_memory_used(devices[i])
            gpu_tot += gpu
            mem_tot += mem / (1024 * 1024)
            src_dict['gpu-' + str(i)] = [gpu]
            src_dict['memory-' + str(i)] = [mem]
        src_dict['gpu-total'] = [gpu_tot / ngpus]
        src_dict['memory-total'] = [(mem_tot / gpu_mem_sum) * 100]
        src_dict['tx-total'] = [tx_tot]
        src_dict['rx-total'] = [rx_tot]

        source.stream(src_dict, 1000)

        last_time = now

    doc.add_periodic_callback(cb, 200)


def system_resource_timeline(doc):

    memory_list = get_mem_list()

    gpu_mem_max = max(memory_list) * (1024 * 1024)
    gpu_mem_sum = sum(memory_list)

    # Shared X Range for all plots
    x_range = DataRange1d(follow='end', follow_interval=20000, range_padding=0)
    tools = 'reset,xpan,xwheel_zoom'

    item_dict = {
        'time': [],
        'cpu': [],
        'net-read': [],
        'net-sent': [],
        'gpu-total': [],
        'memory-total': [],
    }
    for i in range(ngpus):
        item_dict['gpu-' + str(i)] = []
        item_dict['memory-' + str(i)] = []

    source = ColumnDataSource(item_dict)

    cpu_fig = figure(
        title='CPU',
        sizing_mode='stretch_both',
        x_axis_type='datetime',
        y_range=[0, 100],
        x_range=x_range,
        tools=tools,
    )
    cpu_fig.line(source=source, x='time', y='cpu', line_width=3)

    net_fig = figure(
        title='Network I/O Bandwidth',
        sizing_mode='stretch_both',
        x_axis_type='datetime',
        x_range=x_range,
        tools=tools,
    )
    net_fig.line(source=source, x='time', y='net-read', color='blue', line_width=3, legend_label='Recv')
    net_fig.line(source=source, x='time', y='net-sent', color='orange', line_width=3, legend_label='Send')
    net_fig.yaxis.formatter = NumeralTickFormatter(format='0.0b')

    def _get_color(ind):
        color_list = [
            'blue',
            'red',
            'green',
            'black',
            'brown',
            'cyan',
            'orange',
            'pink',
            'purple',
            'gold',
        ]
        return color_list[ind % len(color_list)]

    gpu_fig = figure(
        title='GPU Utilization (per Device) [%]',
        sizing_mode='stretch_both',
        x_axis_type='datetime',
        y_range=[0, 100],
        x_range=x_range,
        tools=tools,
    )
    for i in range(ngpus):
        gpu_fig.line(
            source=source, x='time', y='gpu-' + str(i), color=_get_color(i),
            line_width=3,
        )

    gpu_memory_fig = figure(
        title='GPU Memory Utilization (per Device) [B]',
        sizing_mode='stretch_both',
        x_axis_type='datetime',
        y_range=[0, gpu_mem_max],
        x_range=x_range,
        tools=tools,
    )
    for i in range(ngpus):
        gpu_memory_fig.line(
            source=source, x='time', y='memory-' + str(i), color=_get_color(i),
            line_width=3,
        )
    gpu_memory_fig.yaxis.formatter = NumeralTickFormatter(format='0.0 b')
    figures = [cpu_fig, net_fig, gpu_fig, gpu_memory_fig]

    doc.title = 'System Resource Timeline'
    doc.add_root(
        column(*figures, sizing_mode='stretch_both')
    )

    last_time = time.time()
    last_net_recv = psutil.net_io_counters().bytes_recv
    last_net_sent = psutil.net_io_counters().bytes_sent

    def cb():
        nonlocal last_time, last_net_recv, last_net_sent

        now = time.time()
        cpu = psutil.cpu_percent()
        net = psutil.net_io_counters()
        net_read = net.bytes_recv
        net_sent = net.bytes_sent

        src_dict = {'time': [now * 1000]}
        gpu_tot = 0
        mem_tot = 0
        tx_tot = 0
        rx_tot = 0

        for i in range(ngpus):
            gpu = rocml.smi_get_device_utilization(devices[i])
            mem = rocml.smi_get_device_memory_used(devices[i])
            gpu_tot += gpu
            mem_tot += mem / (1024 * 1024)
            src_dict['gpu-' + str(i)] = [gpu]
            src_dict['memory-' + str(i)] = [mem]
        
        src_dict['cpu'] = [cpu]
        src_dict['net-read'] = [(net_read - last_net_recv) / (now - last_time)]
        src_dict['net-sent'] = [(net_sent - last_net_sent) / (now - last_time)]
        src_dict['gpu-total'] = [gpu_tot / ngpus]
        src_dict['memory-total'] = [(mem_tot / gpu_mem_sum) * 100]

        source.stream(src_dict, 1000)

        last_net_recv = net_read
        last_net_sent = net_sent
        last_time = now

    doc.add_periodic_callback(cb, 200)
