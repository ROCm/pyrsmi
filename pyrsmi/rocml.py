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

# Python bindings for AMD SMI library (amdsmi)
# Migrated from deprecated rocm-smi to amdsmi
from ctypes import *
from os.path import join, realpath, isfile
import os
import logging
import subprocess
import sys
import threading
from enum import IntEnum, auto

## Error checking
class ROCMLError_NotSupported(Exception):
    pass


class ROCMLError_FunctionNotFound(Exception):
    pass


class ROCMLError_LibraryNotFound(Exception):
    pass


class ROCMLError_DriverNotLoaded(Exception):
    pass


class ROCMLError_Unknown(Exception):
    pass


class ROCMLError_Uninitialized(Exception):
    pass


class ROCMLState(IntEnum):
    UNINITIALIZED = auto()
    """No attempt yet made to initialize PyROCML"""
    INITIALIZED = auto()
    """PyROCML was successfully initialized"""
    DISABLED_PYROCML_NOT_AVAILABLE = auto()
    """PyROCML not installed"""
    DISABLED_CONFIG = auto()
    """PyROCML diagnostics disabled by ``distributed.diagnostics.rocml`` config setting"""
    DISABLED_LIBRARY_NOT_FOUND = auto()
    """PyROCML available, but ROCML not installed"""


LIBROCM_NAME = 'libamd_smi.so'  # Updated from librocm_smi64.so to libamd_smi.so
RSMI_MAX_BUFFER_LENGTH = 256

# Policy enums
RSMI_MAX_NUM_FREQUENCIES = 32

# amdsmi constants
AMDSMI_MAX_DEVICES = 32
AMDSMI_MAX_NUM_XCP = 8
AMDSMI_MAX_STRING_LENGTH = 256

# Processor handle management - amdsmi uses opaque handles instead of device indices
_processor_handles = []
_handle_initialized = False
amdsmi_processor_handle = c_void_p  # opaque pointer type
amdsmi_socket_handle = c_void_p  # opaque pointer type


# amdsmi data structures
class amdsmi_bdf_t(Union):
    """BDF (Bus/Device/Function) identifier structure for amdsmi"""
    class _Fields(Structure):
        _fields_ = [
            ('function_number', c_uint64, 3),
            ('device_number', c_uint64, 5),
            ('bus_number', c_uint64, 8),
            ('domain_number', c_uint64, 48)
        ]
    
    _fields_ = [
        ('fields', _Fields),
        ('as_uint', c_uint64)
    ]


class amdsmi_asic_info_t(Structure):
    """ASIC information structure for amdsmi"""
    _fields_ = [
        ('market_name', c_char * AMDSMI_MAX_STRING_LENGTH),
        ('vendor_id', c_uint32),
        ('vendor_name', c_char * AMDSMI_MAX_STRING_LENGTH),
        ('subvendor_id', c_uint32),
        ('device_id', c_uint64),
        ('rev_id', c_uint32),
        ('asic_serial', c_char * AMDSMI_MAX_STRING_LENGTH),
        ('oam_id', c_uint32),
        ('num_of_compute_units', c_uint32),
        ('target_graphics_version', c_uint64),
        ('subsystem_id', c_uint32),
        ('reserved', c_uint32 * 21)
    ]


class amdsmi_engine_usage_t(Structure):
    """GPU engine usage structure for amdsmi"""
    _fields_ = [
        ('gfx_activity', c_uint32),    # Graphics activity in %
        ('umc_activity', c_uint32),    # Memory controller activity in %
        ('mm_activity', c_uint32),     # Multimedia activity in %
        ('reserved', c_uint32 * 13)
    ]


class amdsmi_power_info_t(Structure):
    """Power information structure for amdsmi"""
    _fields_ = [
        ('socket_power', c_uint64),          # Socket power in W
        ('current_socket_power', c_uint32),  # Current socket power in W (MI300+)
        ('average_socket_power', c_uint32),  # Average socket power in W (Navi + MI200 and earlier)
        ('gfx_voltage', c_uint64),           # GFX voltage in mV
        ('soc_voltage', c_uint64),           # SOC voltage in mV
        ('mem_voltage', c_uint64),           # MEM voltage in mV
        ('power_limit', c_uint32),           # Power limit in W
        ('reserved', c_uint64 * 18)
    ]


class amdsmi_retired_page_record_t(Structure):
    """Retired/reserved memory page record for amdsmi"""
    _fields_ = [
        ('page_address', c_uint64),
        ('page_size', c_uint64),
        ('status', c_int)  # amdsmi_memory_page_status_t
    ]


# amdsmi status codes (new)
class amdsmi_status_t(c_int):
    AMDSMI_STATUS_SUCCESS = 0
    AMDSMI_STATUS_INVAL = 1
    AMDSMI_STATUS_NOT_SUPPORTED = 2
    AMDSMI_STATUS_NOT_YET_IMPLEMENTED = 3
    AMDSMI_STATUS_FAIL_LOAD_MODULE = 4
    AMDSMI_STATUS_FAIL_LOAD_SYMBOL = 5
    AMDSMI_STATUS_DRM_ERROR = 6
    AMDSMI_STATUS_API_FAILED = 7
    AMDSMI_STATUS_TIMEOUT = 8
    AMDSMI_STATUS_RETRY = 9
    AMDSMI_STATUS_NO_PERM = 10
    AMDSMI_STATUS_INTERRUPT = 11
    AMDSMI_STATUS_IO = 12
    AMDSMI_STATUS_ADDRESS_FAULT = 13
    AMDSMI_STATUS_FILE_ERROR = 14
    AMDSMI_STATUS_OUT_OF_RESOURCES = 15
    AMDSMI_STATUS_INTERNAL_EXCEPTION = 16
    AMDSMI_STATUS_INPUT_OUT_OF_BOUNDS = 17
    AMDSMI_STATUS_INIT_ERROR = 18
    AMDSMI_STATUS_REFCOUNT_OVERFLOW = 19
    AMDSMI_STATUS_DIRECTORY_NOT_FOUND = 20
    AMDSMI_STATUS_BUSY = 30
    AMDSMI_STATUS_NOT_FOUND = 31
    AMDSMI_STATUS_NOT_INIT = 32
    AMDSMI_STATUS_NO_SLOT = 33
    AMDSMI_STATUS_DRIVER_NOT_LOADED = 34
    AMDSMI_STATUS_MORE_DATA = 39
    AMDSMI_STATUS_NO_DATA = 40
    AMDSMI_STATUS_INSUFFICIENT_SIZE = 41
    AMDSMI_STATUS_UNEXPECTED_SIZE = 42


# rsmi status codes (legacy, kept for compatibility)
class rsmi_status_t(c_int):
    RSMI_STATUS_SUCCESS = 0x0
    RSMI_STATUS_INVALID_ARGS = 0x1
    RSMI_STATUS_NOT_SUPPORTED = 0x2
    RSMI_STATUS_FILE_ERROR = 0x3
    RSMI_STATUS_PERMISSION = 0x4
    RSMI_STATUS_OUT_OF_RESOURCES = 0x5
    RSMI_STATUS_INTERNAL_EXCEPTION = 0x6
    RSMI_STATUS_INPUT_OUT_OF_BOUNDS = 0x7
    RSMI_STATUS_INIT_ERROR = 0x8
    RSMI_INITIALIZATION_ERROR = RSMI_STATUS_INIT_ERROR
    RSMI_STATUS_NOT_YET_IMPLEMENTED = 0x9
    RSMI_STATUS_NOT_FOUND = 0xA
    RSMI_STATUS_INSUFFICIENT_SIZE = 0xB
    RSMI_STATUS_INTERRUPT = 0xC
    RSMI_STATUS_UNEXPECTED_SIZE = 0xD
    RSMI_STATUS_NO_DATA = 0xE
    RSMI_STATUS_UNKNOWN_ERROR = 0xFFFFFFFF


# Dictionary of amdsmi ret codes and verbose output
amdsmi_status_verbose_err_out = {
    amdsmi_status_t.AMDSMI_STATUS_SUCCESS: 'Operation was successful',
    amdsmi_status_t.AMDSMI_STATUS_INVAL: 'Invalid parameters',
    amdsmi_status_t.AMDSMI_STATUS_NOT_SUPPORTED: 'Command not supported',
    amdsmi_status_t.AMDSMI_STATUS_NOT_YET_IMPLEMENTED: 'Not implemented yet',
    amdsmi_status_t.AMDSMI_STATUS_FAIL_LOAD_MODULE: 'Failed to load library module',
    amdsmi_status_t.AMDSMI_STATUS_FAIL_LOAD_SYMBOL: 'Failed to load symbol',
    amdsmi_status_t.AMDSMI_STATUS_DRM_ERROR: 'Error when calling libdrm',
    amdsmi_status_t.AMDSMI_STATUS_API_FAILED: 'API call failed',
    amdsmi_status_t.AMDSMI_STATUS_TIMEOUT: 'Timeout in API call',
    amdsmi_status_t.AMDSMI_STATUS_RETRY: 'Retry operation',
    amdsmi_status_t.AMDSMI_STATUS_NO_PERM: 'Permission denied',
    amdsmi_status_t.AMDSMI_STATUS_INTERRUPT: 'Interrupt occurred during execution',
    amdsmi_status_t.AMDSMI_STATUS_IO: 'I/O Error',
    amdsmi_status_t.AMDSMI_STATUS_ADDRESS_FAULT: 'Bad address',
    amdsmi_status_t.AMDSMI_STATUS_FILE_ERROR: 'Problem accessing a file',
    amdsmi_status_t.AMDSMI_STATUS_OUT_OF_RESOURCES: 'Not enough memory',
    amdsmi_status_t.AMDSMI_STATUS_INTERNAL_EXCEPTION: 'Internal exception was caught',
    amdsmi_status_t.AMDSMI_STATUS_INPUT_OUT_OF_BOUNDS: 'Input is out of allowable or safe range',
    amdsmi_status_t.AMDSMI_STATUS_INIT_ERROR: 'Error occurred during initialization',
    amdsmi_status_t.AMDSMI_STATUS_REFCOUNT_OVERFLOW: 'Internal reference counter exceeded INT32_MAX',
    amdsmi_status_t.AMDSMI_STATUS_DIRECTORY_NOT_FOUND: 'Directory not found',
    amdsmi_status_t.AMDSMI_STATUS_BUSY: 'Processor busy',
    amdsmi_status_t.AMDSMI_STATUS_NOT_FOUND: 'Processor not found',
    amdsmi_status_t.AMDSMI_STATUS_NOT_INIT: 'Processor not initialized',
    amdsmi_status_t.AMDSMI_STATUS_NO_SLOT: 'No more free slot',
    amdsmi_status_t.AMDSMI_STATUS_DRIVER_NOT_LOADED: 'Processor driver not loaded',
    amdsmi_status_t.AMDSMI_STATUS_MORE_DATA: 'More data than buffer size',
    amdsmi_status_t.AMDSMI_STATUS_NO_DATA: 'No data found for input',
    amdsmi_status_t.AMDSMI_STATUS_INSUFFICIENT_SIZE: 'Insufficient resources available',
    amdsmi_status_t.AMDSMI_STATUS_UNEXPECTED_SIZE: 'Unexpected amount of data read'
}


# Dictionary of rsmi ret codes and verbose output (legacy)
rsmi_status_verbose_err_out = {
    rsmi_status_t.RSMI_STATUS_SUCCESS: 'Operation was successful',
    rsmi_status_t.RSMI_STATUS_INVALID_ARGS: 'Invalid arguments provided',
    rsmi_status_t.RSMI_STATUS_NOT_SUPPORTED: 'Not supported on the given system',
    rsmi_status_t.RSMI_STATUS_FILE_ERROR: 'Problem accessing a file',
    rsmi_status_t.RSMI_STATUS_PERMISSION: 'Permission denied',
    rsmi_status_t.RSMI_STATUS_OUT_OF_RESOURCES: 'Unable to acquire memory or other resource',
    rsmi_status_t.RSMI_STATUS_INTERNAL_EXCEPTION: 'An internal exception was caught',
    rsmi_status_t.RSMI_STATUS_INPUT_OUT_OF_BOUNDS: 'Provided input is out of allowable or safe range',
    rsmi_status_t.RSMI_INITIALIZATION_ERROR: 'Error occured during rsmi initialization',
    rsmi_status_t.RSMI_STATUS_NOT_YET_IMPLEMENTED: 'Requested function is not implemented on this setup',
    rsmi_status_t.RSMI_STATUS_NOT_FOUND: 'Item searched for but not found',
    rsmi_status_t.RSMI_STATUS_INSUFFICIENT_SIZE: 'Insufficient resources available',
    rsmi_status_t.RSMI_STATUS_INTERRUPT: 'Interrupt occured during execution',
    rsmi_status_t.RSMI_STATUS_UNEXPECTED_SIZE: 'Unexpected amount of data read',
    rsmi_status_t.RSMI_STATUS_NO_DATA: 'No data found for the given input',
    rsmi_status_t.RSMI_STATUS_UNKNOWN_ERROR: 'Unknown error occured'
}


# amdsmi initialization flags (new)
class amdsmi_init_flags_t(c_uint64):
    AMDSMI_INIT_ALL_PROCESSORS = 0xFFFFFFFF
    AMDSMI_INIT_AMD_CPUS = (1 << 0)
    AMDSMI_INIT_AMD_GPUS = (1 << 1)
    AMDSMI_INIT_NON_AMD_CPUS = (1 << 2)
    AMDSMI_INIT_NON_AMD_GPUS = (1 << 3)
    AMDSMI_INIT_AMD_APUS = (AMDSMI_INIT_AMD_CPUS | AMDSMI_INIT_AMD_GPUS)


# rsmi initialization flags (legacy)
class rsmi_init_flags_t(c_int):
    RSMI_INIT_FLAG_ALL_GPUS = 0x1


# amdsmi memory types (new)
class amdsmi_memory_type_t(c_int):
    AMDSMI_MEM_TYPE_FIRST = 0
    AMDSMI_MEM_TYPE_VRAM = AMDSMI_MEM_TYPE_FIRST
    AMDSMI_MEM_TYPE_VIS_VRAM = 1
    AMDSMI_MEM_TYPE_GTT = 2
    AMDSMI_MEM_TYPE_LAST = AMDSMI_MEM_TYPE_GTT


# amdsmi memory page status
class amdsmi_memory_page_status_t(c_int):
    AMDSMI_MEM_PAGE_STATUS_RESERVED = 0
    AMDSMI_MEM_PAGE_STATUS_PENDING = 1
    AMDSMI_MEM_PAGE_STATUS_UNRESERVABLE = 2


# amdsmi link types (new)
class amdsmi_link_type_t(c_int):
    AMDSMI_LINK_TYPE_INTERNAL = 0
    AMDSMI_LINK_TYPE_PCIE = 1
    AMDSMI_LINK_TYPE_XGMI = 2
    AMDSMI_LINK_TYPE_NOT_APPLICABLE = 3
    AMDSMI_LINK_TYPE_UNKNOWN = 4


# amdsmi card form factors
class amdsmi_card_form_factor_t(c_int):
    AMDSMI_CARD_FORM_FACTOR_PCIE = 0
    AMDSMI_CARD_FORM_FACTOR_OAM = 1
    AMDSMI_CARD_FORM_FACTOR_CEM = 2
    AMDSMI_CARD_FORM_FACTOR_UNKNOWN = 3


# amdsmi P2P capability structure
class amdsmi_p2p_capability_t(Structure):
    """P2P capability structure for amdsmi"""
    _fields_ = [
        ('is_iolink_coherent', c_uint8),
        ('is_iolink_atomics_32bit', c_uint8),
        ('is_iolink_atomics_64bit', c_uint8),
        ('is_iolink_dma', c_uint8),
        ('is_iolink_bi_directional', c_uint8)
    ]


# amdsmi PCIe info structure
class amdsmi_pcie_static_t(Structure):
    """PCIe static information"""
    _fields_ = [
        ('max_pcie_width', c_uint16),
        ('max_pcie_speed', c_uint32),
        ('pcie_interface_version', c_uint32),
        ('slot_type', c_int),  # amdsmi_card_form_factor_t
        ('max_pcie_interface_version', c_uint32),
        ('reserved', c_uint64 * 9)
    ]


class amdsmi_pcie_metric_t(Structure):
    """PCIe metric information"""
    _fields_ = [
        ('pcie_width', c_uint16),
        ('pcie_speed', c_uint32),
        ('pcie_bandwidth', c_uint32),
        ('pcie_replay_count', c_uint64),
        ('pcie_l0_to_recovery_count', c_uint64),
        ('pcie_replay_roll_over_count', c_uint64),
        ('pcie_nak_sent_count', c_uint64),
        ('pcie_nak_received_count', c_uint64),
        ('pcie_lc_perf_other_end_recovery_count', c_uint32),
        ('reserved', c_uint64 * 12)
    ]


class amdsmi_pcie_info_t(Structure):
    """Complete PCIe information structure"""
    _fields_ = [
        ('pcie_static', amdsmi_pcie_static_t),
        ('pcie_metric', amdsmi_pcie_metric_t),
        ('reserved', c_uint64 * 32)
    ]


# rsmi memory types (legacy)
class rsmi_memory_type_t(c_int):
    RSMI_MEM_TYPE_FIRST = 0
    RSMI_MEM_TYPE_VRAM = RSMI_MEM_TYPE_FIRST
    RSMI_MEM_TYPE_VIS_VRAM = 1
    RSMI_MEM_TYPE_GTT = 2
    RSMI_MEM_TYPE_LAST = RSMI_MEM_TYPE_GTT


# memory_type_l includes names for with rsmi_memory_type_t
# Usage example to get corresponding names:
# memory_type_l[rsmi_memory_type_t.RSMI_MEM_TYPE_VRAM] will return string 'vram'
memory_type_l = ['VRAM', 'VIS_VRAM', 'GTT']


class rsmi_retired_page_record_t(Structure):
    _fields_ = [('page_address', c_uint64),
                ('page_size', c_uint64),
                ('status', c_int)]


class rsmi_sw_component_t(c_int):
    RSMI_SW_COMP_FIRST = 0x0
    RSMI_SW_COMP_DRIVER = RSMI_SW_COMP_FIRST
    RSMI_SW_COMP_LAST = RSMI_SW_COMP_DRIVER


class rsmi_frequencies_t(Structure):
    _fields_ = [('num_supported', c_int32),
                ('current', c_uint32),
                ('frequency', c_uint64 * RSMI_MAX_NUM_FREQUENCIES)]


class rsmi_pcie_bandwidth_t(Structure):
    _fields_ = [('transfer_rate', rsmi_frequencies_t),
                ('lanes', c_uint32 * RSMI_MAX_NUM_FREQUENCIES)]


class rsmi_process_info_t(Structure):
    _fields_ = [('process_id', c_uint32),
                ('pasid', c_uint32),         # PSA: Power Spectrum Analysis ?
                ('vram_usage', c_uint64),
                ('sdma_usage', c_uint64),    # SDMA: System Direct Memory Access
                ('cu_occupancy', c_uint32)]


class rsmi_xgmi_status_t(c_int):
    RSMI_XGMI_STATUS_NO_ERRORS = 0
    RSMI_XGMI_STATUS_ERROR = 1
    RSMI_XGMI_STATUS_MULTIPLE_ERRORS = 2


class rsmi_io_link_type(c_int):
    RSMI_IOLINK_TYPE_UNDEFINED      = 0
    RSMI_IOLINK_TYPE_HYPERTRANSPORT = 1
    RSMI_IOLINK_TYPE_PCIEXPRESS     = 2
    RSMI_IOLINK_TYPE_AMBA           = 3
    RSMI_IOLINK_TYPE_MIPI           = 4
    RSMI_IOLINK_TYPE_QPI_1_1        = 5
    RSMI_IOLINK_TYPE_RESERVED1      = 6
    RSMI_IOLINK_TYPE_RESERVED2      = 7
    RSMI_IOLINK_TYPE_RAPID_IO       = 8
    RSMI_IOLINK_TYPE_INFINIBAND     = 9
    RSMI_IOLINK_TYPE_RESERVED3      = 10
    RSMI_IOLINK_TYPE_XGMI           = 11
    RSMI_IOLINK_TYPE_XGOP           = 12
    RSMI_IOLINK_TYPE_GZ             = 13
    RSMI_IOLINK_TYPE_ETHERNET_RDMA  = 14
    RSMI_IOLINK_TYPE_RDMA_OTHER     = 15
    RSMI_IOLINK_TYPE_OTHER          = 16
    RSMI_IOLINK_TYPE_NUMIOLINKTYPES = 17
    RSMI_IOLINK_TYPE_SIZE           = 0xFFFFFFFF


## Library loading
rocm_lib = None
lib_load_lock = threading.Lock()
_rocm_lib_refcount = 0


## Function access, to prevent lib_load_lock deadlock
_rocml_get_function_ptr_cache = dict()

def _rocml_get_function_ptr(name):
    global rocm_lib

    if name in _rocml_get_function_ptr_cache:
        return _rocml_get_function_ptr_cache[name]

    lib_load_lock.acquire()
    try:
        # ensure library was loaded
        if rocm_lib == None:
            raise ROCMLError_Uninitialized
        try:
            _rocml_get_function_ptr_cache[name] = getattr(rocm_lib, name)
            return _rocml_get_function_ptr_cache[name]
        except AttributeError:
            raise ROCMLError_FunctionNotFound
    finally:
        # lock is always freed
        lib_load_lock.release()


def _load_rocm_library():
    """Load AMD SMI library (amdsmi) if not already loaded"""
    global rocm_lib

    if rocm_lib == None:

        lib_load_lock.acquire()

        try:
            if rocm_lib == None:
                try:
                    if sys.platform[:3] == 'win':
                        raise ROCMLError_NotSupported('Windows platform is not supported yet')
                    else:
                        # assume linux
                        path_librocm = _find_lib_rocm()
                        if not path_librocm:
                            raise ROCMLError_LibraryNotFound(
                                f'AMD SMI library ({LIBROCM_NAME}) not found. '
                                'Please ensure ROCm is installed and ROCM_PATH is set correctly.'
                            )
                        cdll.LoadLibrary(path_librocm)
                        rocm_lib = CDLL(path_librocm)
                except OSError as e:
                    raise ROCMLError_LibraryNotFound(f'AMD SMI library not found: {e}')
                if rocm_lib == None:
                    raise ROCMLError_LibraryNotFound('AMD SMI library not found')
        finally:
            lib_load_lock.release()


def _find_lib_rocm():
    """search for amdsmi library and returns path
    Searches in both lib and lib64 directories
    if search fails, returns empty string
    """
    rocm_path = os.environ.get('ROCM_PATH', '/opt/rocm')
    
    # Try lib directory first (most common for amdsmi)
    rocm_lib_path = join(rocm_path, f'lib/{LIBROCM_NAME}')
    if isfile(rocm_lib_path):
        return rocm_lib_path
    
    # Try lib64 directory as fallback
    rocm_lib64_path = join(rocm_path, f'lib64/{LIBROCM_NAME}')
    if isfile(rocm_lib64_path):
        return rocm_lib64_path
    
    return ''


def _driver_initialized():
    """ Returns true if amdgpu is found in the list of initialized modules
    """
    initialized = ''
    try:
        initialized = str(subprocess.check_output("cat /sys/module/amdgpu/initstate |grep live", shell=True))
    except subprocess.CalledProcessError:
        pass
    return len(initialized) > 0


def _init_processor_handles():
    """Initialize processor handles after amdsmi_init is called.
    
    This function discovers all AMD GPU processors and stores their handles
    for use by the rest of the API. It maintains backward compatibility by
    allowing device indices to be used, which are mapped to handles internally.
    """
    global _processor_handles, _handle_initialized
    
    if _handle_initialized:
        return
    
    _processor_handles = []
    
    try:
        # Get socket count first
        socket_count = c_uint32(0)
        ret = rocm_lib.amdsmi_get_socket_handles(byref(socket_count), None)
        
        if not amdsmi_ret_ok(ret):
            logging.warning('Failed to get socket count')
            return
        
        if socket_count.value == 0:
            logging.warning('No sockets found')
            return
        
        # Allocate socket handles array
        socket_handles = (amdsmi_socket_handle * socket_count.value)()
        ret = rocm_lib.amdsmi_get_socket_handles(byref(socket_count), socket_handles)
        
        if not amdsmi_ret_ok(ret):
            logging.error('Failed to get socket handles')
            return
        
        # For each socket, get processor handles
        for i in range(socket_count.value):
            processor_count = c_uint32(0)
            
            # First call to get count (pass NULL for processor_handles)
            ret = rocm_lib.amdsmi_get_processor_handles(
                socket_handles[i], 
                byref(processor_count), 
                None
            )
            
            if not amdsmi_ret_ok(ret):
                logging.warning(f'Failed to get processor count for socket {i}')
                continue
            
            if processor_count.value == 0:
                logging.warning(f'No processors found on socket {i}')
                continue
            
            # Allocate processor handles array
            proc_handles = (amdsmi_processor_handle * processor_count.value)()
            
            # Second call to get actual handles
            ret = rocm_lib.amdsmi_get_processor_handles(
                socket_handles[i], 
                byref(processor_count),
                proc_handles
            )
            
            if amdsmi_ret_ok(ret):
                # Add GPU handles to our list
                for j in range(processor_count.value):
                    _processor_handles.append(proc_handles[j])
                logging.info(f'Socket {i}: Found {processor_count.value} processors')
            else:
                logging.warning(f'Failed to get processor handles for socket {i}')
        
        _handle_initialized = True
        logging.info(f'Initialized {len(_processor_handles)} total processor handles')
        
    except Exception as e:
        logging.error(f'Exception during processor handle initialization: {e}')
        import traceback
        traceback.print_exc()
        _processor_handles = []


def _get_processor_handle(device_index):
    """Convert device index to processor handle.
    
    Maintains backward compatibility by allowing the use of device indices
    (0, 1, 2, ...) which are mapped to amdsmi processor handles.
    
    @param device_index: Integer device index (0-based)
    @return: amdsmi_processor_handle for the device
    """
    if not _handle_initialized:
        _init_processor_handles()
    
    if device_index < 0 or device_index >= len(_processor_handles):
        raise ValueError(f'Invalid device index: {device_index}. Valid range: 0-{len(_processor_handles)-1}')
    
    return _processor_handles[device_index]


def smi_initialize():
    """Initialize AMD SMI library (amdsmi).
    
    This function initializes the amdsmi library and discovers all AMD GPU
    processors in the system. After initialization, GPU devices can be accessed
    using device indices (0, 1, 2, ...) as before.
    """
    _load_rocm_library()

    if not _driver_initialized():
        raise RuntimeError('AMD GPU driver not initialized. Please ensure amdgpu driver is loaded.')

    # Initialize amdsmi with AMD GPU flag
    ret_init = rocm_lib.amdsmi_init(amdsmi_init_flags_t.AMDSMI_INIT_AMD_GPUS)
    
    if ret_init != amdsmi_status_t.AMDSMI_STATUS_SUCCESS:
        err_msg = amdsmi_status_verbose_err_out.get(ret_init, f'Unknown error: {ret_init}')
        logging.error(f'AMD SMI initialization failed: {err_msg}')
        raise RuntimeError(f'AMD SMI initialization failed: {err_msg}')
    
    # Initialize processor handles
    _init_processor_handles()
    
    if len(_processor_handles) == 0:
        logging.warning('No AMD GPU processors found')

    # Update reference count
    global _rocm_lib_refcount
    lib_load_lock.acquire()
    _rocm_lib_refcount += 1
    lib_load_lock.release()


def amdsmi_ret_ok(my_ret):
    """ Returns true if AMDSMI call status is 0 (success)

    @param my_ret: Return code from AMDSMI call (amdsmi API)
    """
    if my_ret != amdsmi_status_t.AMDSMI_STATUS_SUCCESS:
        err_str = c_char_p()
        try:
            # Try to get error string from library
            rocm_lib.amdsmi_status_code_to_string(my_ret, byref(err_str))
            if err_str.value:
                logging.error(f'AMDSMI Error: {err_str.value.decode()}')
            else:
                # Fallback to our dictionary
                err_msg = amdsmi_status_verbose_err_out.get(my_ret, f'Unknown error code: {my_ret}')
                logging.error(f'AMDSMI Error: {err_msg}')
        except Exception as e:
            # If amdsmi_status_code_to_string fails, use our dictionary
            err_msg = amdsmi_status_verbose_err_out.get(my_ret, f'Unknown error code: {my_ret}')
            logging.error(f'AMDSMI Error: {err_msg}')
        return False
    return True


def rsmi_ret_ok(my_ret):
    """ Returns true if RSMI/AMDSMI call status is 0 (success)
    
    This function now wraps amdsmi_ret_ok for backward compatibility.

    @param my_ret: Return code from RSMI/AMDSMI call
    """
    return amdsmi_ret_ok(my_ret)


def smi_shutdown():
    """Shutdown the AMD SMI library interface.
    
    Cleans up processor handles and shuts down the amdsmi library.
    The library remains loaded but the interface is shut down.
    """
    global _processor_handles, _handle_initialized
    
    # Shutdown amdsmi
    ret = rocm_lib.amdsmi_shut_down()
    amdsmi_ret_ok(ret)
    
    # Clear processor handles
    _processor_handles = []
    _handle_initialized = False

    # Update reference count
    global _rocm_lib_refcount
    lib_load_lock.acquire()
    _rocm_lib_refcount -= 1
    lib_load_lock.release()


def smi_get_kernel_version():
    """returns ROCm kernerl driver version"""
    ver_str = create_string_buffer(256)
    ret = rocm_lib.rsmi_version_str_get(rsmi_sw_component_t.RSMI_SW_COMP_DRIVER, ver_str, 256)
    return ver_str.value.decode() if rsmi_ret_ok(ret) else ''

def smi_get_device_id(dev):
    """Returns device ID of the device as 64bit integer.
    
    Uses amdsmi_get_gpu_asic_info to retrieve device ID.
    
    @param dev: Device index (0-based)
    @return: Device ID as 64-bit integer, or -1 on error
    """
    try:
        handle = _get_processor_handle(dev)
        asic_info = amdsmi_asic_info_t()
        ret = rocm_lib.amdsmi_get_gpu_asic_info(handle, byref(asic_info))
        
        if rsmi_ret_ok(ret):
            return asic_info.device_id
        else:
            return -1
    except Exception as e:
        logging.error(f'Error getting device ID for device {dev}: {e}')
        return -1

def smi_get_device_count():
    """Returns the number of AMD GPU devices.
    
    This function returns the count of AMD GPU processors discovered
    during initialization. It uses the processor handle cache.
    
    @return: Number of GPU devices, or -1 on error
    """
    if not _handle_initialized:
        _init_processor_handles()
    
    return len(_processor_handles)


def smi_get_device_name(dev):
    """Returns the market name of a GPU device.
    
    Uses amdsmi_get_gpu_asic_info to retrieve device information.
    
    @param dev: Device index (0-based)
    @return: Device market name as string, or empty string on error
    """
    try:
        handle = _get_processor_handle(dev)
        asic_info = amdsmi_asic_info_t()
        ret = rocm_lib.amdsmi_get_gpu_asic_info(handle, byref(asic_info))
        
        if rsmi_ret_ok(ret):
            return asic_info.market_name.decode('utf-8').rstrip('\x00')
        else:
            return ''
    except Exception as e:
        logging.error(f'Error getting device name for device {dev}: {e}')
        return ''

def smi_get_device_revision(dev):
    """Returns device revision ID.
    
    Uses amdsmi_get_gpu_asic_info to retrieve revision ID.
    
    @param dev: Device index (0-based)
    @return: Revision ID as integer, or -1 on error
    """
    try:
        handle = _get_processor_handle(dev)
        asic_info = amdsmi_asic_info_t()
        ret = rocm_lib.amdsmi_get_gpu_asic_info(handle, byref(asic_info))
        
        if rsmi_ret_ok(ret):
            return asic_info.rev_id
        else:
            return -1
    except Exception as e:
        logging.error(f'Error getting device revision for device {dev}: {e}')
        return -1

def smi_get_device_unique_id(dev):
    """Returns unique ID of the device as 64bit integer.
    
    Uses amdsmi_get_gpu_device_bdf to get the BDF (Bus/Device/Function)
    identifier which serves as a unique ID for the device.
    
    @param dev: Device index (0-based)
    @return: Unique device ID as 64-bit integer, or -1 on error
    """
    try:
        handle = _get_processor_handle(dev)
        bdf = amdsmi_bdf_t()
        ret = rocm_lib.amdsmi_get_gpu_device_bdf(handle, byref(bdf))
        
        if rsmi_ret_ok(ret):
            return bdf.as_uint
        else:
            return -1
    except Exception as e:
        logging.error(f'Error getting unique ID for device {dev}: {e}')
        return -1

def smi_get_device_utilization(dev):
    """Returns GPU device busy percentage.
    
    Uses amdsmi_get_gpu_activity to retrieve GFX (graphics) engine activity.
    
    @param dev: Device index (0-based)
    @return: GPU busy percentage (0-100), or -1 on error
    """
    try:
        handle = _get_processor_handle(dev)
        engine_usage = amdsmi_engine_usage_t()
        ret = rocm_lib.amdsmi_get_gpu_activity(handle, byref(engine_usage))
        
        if rsmi_ret_ok(ret):
            # GFX activity represents overall GPU busy percentage
            return engine_usage.gfx_activity
        else:
            return -1
    except Exception as e:
        logging.error(f'Error getting device utilization for device {dev}: {e}')
        return -1


def smi_get_device_memory_used(dev, type='VRAM'):
    """Returns used memory of device in bytes.
    
    Uses amdsmi_get_gpu_memory_usage to retrieve memory usage.
    
    @param dev: Device index (0-based)
    @param type: Memory type ('VRAM', 'VIS_VRAM', or 'GTT')
    @return: Used memory in bytes, or -1 on error
    """
    try:
        handle = _get_processor_handle(dev)
        type_idx = memory_type_l.index(type)
        
        # Map to amdsmi memory type
        if type_idx == 0:
            mem_type = amdsmi_memory_type_t.AMDSMI_MEM_TYPE_VRAM
        elif type_idx == 1:
            mem_type = amdsmi_memory_type_t.AMDSMI_MEM_TYPE_VIS_VRAM
        elif type_idx == 2:
            mem_type = amdsmi_memory_type_t.AMDSMI_MEM_TYPE_GTT
        else:
            logging.error(f'Invalid memory type: {type}')
            return -1
        
        used = c_uint64()
        ret = rocm_lib.amdsmi_get_gpu_memory_usage(handle, mem_type, byref(used))
        
        if rsmi_ret_ok(ret):
            return used.value
        else:
            return -1
    except Exception as e:
        logging.error(f'Error getting memory usage for device {dev}: {e}')
        return -1


def smi_get_device_memory_total(dev, type='VRAM'):
    """Returns total memory of device in bytes.
    
    Uses amdsmi_get_gpu_memory_total to retrieve total memory.
    
    @param dev: Device index (0-based)
    @param type: Memory type ('VRAM', 'VIS_VRAM', or 'GTT')
    @return: Total memory in bytes, or -1 on error
    """
    try:
        handle = _get_processor_handle(dev)
        type_idx = memory_type_l.index(type)
        
        # Map to amdsmi memory type
        if type_idx == 0:
            mem_type = amdsmi_memory_type_t.AMDSMI_MEM_TYPE_VRAM
        elif type_idx == 1:
            mem_type = amdsmi_memory_type_t.AMDSMI_MEM_TYPE_VIS_VRAM
        elif type_idx == 2:
            mem_type = amdsmi_memory_type_t.AMDSMI_MEM_TYPE_GTT
        else:
            logging.error(f'Invalid memory type: {type}')
            return -1
        
        total = c_uint64()
        ret = rocm_lib.amdsmi_get_gpu_memory_total(handle, mem_type, byref(total))
        
        if rsmi_ret_ok(ret):
            return total.value
        else:
            return -1
    except Exception as e:
        logging.error(f'Error getting total memory for device {dev}: {e}')
        return -1


def smi_get_device_memory_busy(dev):
    """Returns percentage of time memory controller is busy.
    
    Uses amdsmi_get_gpu_activity to retrieve UMC (Unified Memory Controller)
    activity, which represents memory busy percentage.
    
    @param dev: Device index (0-based)
    @return: Memory busy percentage (0-100), or -1 on error
    """
    try:
        handle = _get_processor_handle(dev)
        engine_usage = amdsmi_engine_usage_t()
        ret = rocm_lib.amdsmi_get_gpu_activity(handle, byref(engine_usage))
        
        if rsmi_ret_ok(ret):
            # UMC activity represents memory controller busy percentage
            return engine_usage.umc_activity
        else:
            return -1
    except Exception as e:
        logging.error(f'Error getting memory busy for device {dev}: {e}')
        return -1


def smi_get_device_memory_reserved_pages(dev):
    """Returns info about reserved/retired memory pages.
    
    Uses amdsmi_get_gpu_memory_reserved_pages to retrieve bad page information.
    
    @param dev: Device index (0-based)
    @return: Tuple of (num_pages, records) or -1 on error
    """
    try:
        handle = _get_processor_handle(dev)
        num_pages = c_uint32()
        
        # First call to get count
        ret = rocm_lib.amdsmi_get_gpu_memory_reserved_pages(handle, byref(num_pages), None)
        
        if not rsmi_ret_ok(ret):
            return -1
        
        if num_pages.value == 0:
            return (0, None)
        
        # Allocate array for records
        records = (amdsmi_retired_page_record_t * num_pages.value)()
        
        # Second call to get actual records
        ret = rocm_lib.amdsmi_get_gpu_memory_reserved_pages(handle, byref(num_pages), records)
        
        if rsmi_ret_ok(ret):
            # Return first record for compatibility (old API returned single record)
            return (num_pages.value, records[0] if num_pages.value > 0 else None)
        else:
            return -1
    except Exception as e:
        logging.error(f'Error getting reserved pages for device {dev}: {e}')
        return -1

def smi_get_device_fan_rpms(dev, index = 0):
    """Returns fan RPM (Revolutions Per Minute) for the specified fan sensor.
    
    Uses amdsmi_get_gpu_fan_rpms to retrieve fan speed.
    
    @param dev: Device index (0-based)
    @param index: Fan sensor index (default: 0)
    @return: Fan RPM, or -1 on error
    """
    try:
        handle = _get_processor_handle(dev)
        rpms = c_int64()
        ret = rocm_lib.amdsmi_get_gpu_fan_rpms(handle, index, byref(rpms))
        
        if rsmi_ret_ok(ret):
            return rpms.value if rpms.value >= 0 else -1
        else:
            return -1
    except Exception as e:
        logging.error(f'Error getting fan RPMs for device {dev}, sensor {index}: {e}')
        return -1

def smi_get_device_fan_speed(dev, index = 0):
    """Returns fan speed as a value relative to maximum fan speed.
    
    Uses amdsmi_get_gpu_fan_speed to retrieve fan speed percentage.
    
    @param dev: Device index (0-based)
    @param index: Fan sensor index (default: 0)
    @return: Fan speed (relative to max), or -1 on error
    """
    try:
        handle = _get_processor_handle(dev)
        speed = c_int64()
        ret = rocm_lib.amdsmi_get_gpu_fan_speed(handle, index, byref(speed))
        
        if rsmi_ret_ok(ret):
            return speed.value if speed.value >= 0 else -1
        else:
            return -1
    except Exception as e:
        logging.error(f'Error getting fan speed for device {dev}, sensor {index}: {e}')
        return -1

def smi_get_device_fan_speed_max(dev, index = 0):
    """Returns maximum fan speed for the specified fan sensor.
    
    Uses amdsmi_get_gpu_fan_speed_max to retrieve maximum fan speed.
    
    @param dev: Device index (0-based)
    @param index: Fan sensor index (default: 0)
    @return: Maximum fan speed, or -1 on error
    """
    try:
        handle = _get_processor_handle(dev)
        max_speed = c_uint64()
        ret = rocm_lib.amdsmi_get_gpu_fan_speed_max(handle, index, byref(max_speed))
        
        if rsmi_ret_ok(ret):
            return max_speed.value
        else:
            return -1
    except Exception as e:
        logging.error(f'Error getting max fan speed for device {dev}, sensor {index}: {e}')
        return -1

# PCIE functions
def smi_get_device_pcie_bandwidth(dev):
    """Returns PCIe bandwidth information for the device.
    
    Uses amdsmi_get_pcie_info to retrieve complete PCIe information.
    Returns the amdsmi_pcie_info_t structure with static and metric data.
    
    @param dev: Device index (0-based)
    @return: amdsmi_pcie_info_t structure, or -1 on error
    """
    try:
        handle = _get_processor_handle(dev)
        pcie_info = amdsmi_pcie_info_t()
        ret = rocm_lib.amdsmi_get_pcie_info(handle, byref(pcie_info))
        
        if rsmi_ret_ok(ret):
            return pcie_info
        else:
            return -1
    except Exception as e:
        logging.error(f'Error getting PCIe bandwidth for device {dev}: {e}')
        return -1


def smi_get_device_pci_id(dev):
    """Returns unique PCI ID (BDF) of the device in 64bit format.
    
    Uses amdsmi_get_gpu_device_bdf to get BDF identifier.
    Format: BDFID = ((DOMAIN & 0xffffffff) << 32) | ((BUS & 0xff) << 8) |
                    ((DEVICE & 0x1f) <<3 ) | (FUNCTION & 0x7)
    
    @param dev: Device index (0-based)
    @return: BDF ID as 64-bit integer, or -1 on error
    """
    try:
        handle = _get_processor_handle(dev)
        bdf = amdsmi_bdf_t()
        ret = rocm_lib.amdsmi_get_gpu_device_bdf(handle, byref(bdf))
        
        if rsmi_ret_ok(ret):
            return bdf.as_uint
        else:
            return -1
    except Exception as e:
        logging.error(f'Error getting PCI ID for device {dev}: {e}')
        return -1


def smi_get_device_topo_numa_affinity(dev):
    """Returns the NUMA node associated with the device.
    
    Uses amdsmi_get_gpu_topo_numa_affinity to get NUMA node.
    
    @param dev: Device index (0-based)
    @return: NUMA node number, or -1 on error
    """
    try:
        handle = _get_processor_handle(dev)
        numa_node = c_int32()
        ret = rocm_lib.amdsmi_get_gpu_topo_numa_affinity(handle, byref(numa_node))
        
        if rsmi_ret_ok(ret):
            return numa_node.value
        else:
            return -1
    except Exception as e:
        logging.error(f'Error getting NUMA affinity for device {dev}: {e}')
        return -1


def smi_get_device_pcie_throughput(dev):
    """Returns measured PCIe bandwidth/throughput for the device.
    
    Uses amdsmi_get_pcie_info to retrieve current PCIe bandwidth in Mb/s.
    
    @param dev: Device index (0-based)
    @return: PCIe bandwidth in bytes/sec, or -1 on error
    """
    try:
        handle = _get_processor_handle(dev)
        pcie_info = amdsmi_pcie_info_t()
        ret = rocm_lib.amdsmi_get_pcie_info(handle, byref(pcie_info))
        
        if rsmi_ret_ok(ret):
            # Convert from Mb/s to bytes/sec: Mb/s * 1024 * 1024 / 8
            bandwidth_mbps = pcie_info.pcie_metric.pcie_bandwidth
            return int(bandwidth_mbps * 1024 * 1024 / 8) if bandwidth_mbps > 0 else 0
        else:
            return -1
    except Exception as e:
        logging.error(f'Error getting PCIe throughput for device {dev}: {e}')
        return -1


def smi_get_device_pci_replay_counter(dev):
    """Returns PCIe replay counter of the device.
    
    Uses amdsmi_get_pcie_info to retrieve PCIe replay count.
    
    @param dev: Device index (0-based)
    @return: PCIe replay counter, or -1 on error
    """
    try:
        handle = _get_processor_handle(dev)
        pcie_info = amdsmi_pcie_info_t()
        ret = rocm_lib.amdsmi_get_pcie_info(handle, byref(pcie_info))
        
        if rsmi_ret_ok(ret):
            return pcie_info.pcie_metric.pcie_replay_count
        else:
            return -1
    except Exception as e:
        logging.error(f'Error getting PCI replay counter for device {dev}: {e}')
        return -1


# Compute partition functions
def smi_get_device_compute_partition(dev):
    """returns the compute partition of the device"""
    partition = create_string_buffer(RSMI_MAX_BUFFER_LENGTH)
    ret = rocm_lib.rsmi_dev_compute_partition_get(dev, byref(partition), RSMI_MAX_BUFFER_LENGTH)
    return partition.value.decode() if rsmi_ret_ok(ret) else ''


def smi_set_device_compute_partition(dev, partition):
    """modifies the compute partition of the selected device"""
    ret = rocm_lib.rsmi_dev_compute_partition_set(dev, partition)
    return rsmi_ret_ok(ret)


def smi_reset_device_compute_partition(dev):
    """reverts the compute partition of the selected device to its boot state"""
    ret = rocm_lib.rsmi_dev_compute_partition_reset(dev)
    return rsmi_ret_ok(ret)


# Memory partition functions
def smi_get_device_memory_partition(dev):
    """returns the memory partition of the device"""
    partition = create_string_buffer(RSMI_MAX_BUFFER_LENGTH)
    ret = rocm_lib.rsmi_dev_memory_partition_get(dev, byref(partition), RSMI_MAX_BUFFER_LENGTH)
    return partition.value.decode() if rsmi_ret_ok(ret) else ''


def smi_set_device_memory_partition(dev, partition):
    """modifies the memory partition of the selected device"""
    ret = rocm_lib.rsmi_dev_memory_partition_set(dev, partition)
    return rsmi_ret_ok(ret)


def smi_reset_device_memory_partition(dev):
    """reverts the memory partition of the selected device to its boot state"""
    ret = rocm_lib.rsmi_dev_memory_partition_reset(dev)
    return rsmi_ret_ok(ret)


# Hardware Topology functions
def smi_get_device_topo_numa_node_number(dev):
    """Returns the NUMA node associated with the device.
    
    Uses amdsmi_topo_get_numa_node_number to get NUMA node.
    Note: This is an alias for smi_get_device_topo_numa_affinity.
    
    @param dev: Device index (0-based)
    @return: NUMA node number, or -1 on error
    """
    try:
        handle = _get_processor_handle(dev)
        numa_node = c_uint32()
        ret = rocm_lib.amdsmi_topo_get_numa_node_number(handle, byref(numa_node))
        
        if rsmi_ret_ok(ret):
            return numa_node.value
        else:
            return -1
    except Exception as e:
        logging.error(f'Error getting NUMA node number for device {dev}: {e}')
        return -1


def smi_get_device_topo_link_weight(dev_src, dev_dst):
    """Returns the weight of the link between two devices.
    
    Uses amdsmi_topo_get_link_weight to get link weight/distance.
    
    @param dev_src: Source device index
    @param dev_dst: Destination device index
    @return: Link weight, or -1 on error
    """
    try:
        handle_src = _get_processor_handle(dev_src)
        handle_dst = _get_processor_handle(dev_dst)
        weight = c_uint64()
        ret = rocm_lib.amdsmi_topo_get_link_weight(handle_src, handle_dst, byref(weight))
        
        if rsmi_ret_ok(ret):
            return weight.value
        else:
            return -1
    except Exception as e:
        logging.error(f'Error getting link weight between devices {dev_src} and {dev_dst}: {e}')
        return -1


def smi_get_device_minmax_bandwidth(dev_src, dev_dst):
    """Returns the minimum and maximum I/O link bandwidth between two devices.
    
    Uses amdsmi_get_minmax_bandwidth_between_processors.
    Typically works if devices are connected via XGMI and are 1 hop away.
    
    @param dev_src: Source device index
    @param dev_dst: Destination device index
    @return: Tuple of (min_bandwidth, max_bandwidth) in bytes/sec, or -1 on error
    """
    try:
        handle_src = _get_processor_handle(dev_src)
        handle_dst = _get_processor_handle(dev_dst)
        min_bandwidth = c_uint64()
        max_bandwidth = c_uint64()
        ret = rocm_lib.amdsmi_get_minmax_bandwidth_between_processors(
            handle_src, handle_dst, byref(min_bandwidth), byref(max_bandwidth))
        
        if rsmi_ret_ok(ret):
            return (min_bandwidth.value, max_bandwidth.value)
        else:
            return -1
    except Exception as e:
        logging.error(f'Error getting min/max bandwidth between devices {dev_src} and {dev_dst}: {e}')
        return -1


def smi_get_device_link_type(dev_src, dev_dst):
    """Returns the hops and type of link between two devices.
    
    Uses amdsmi_topo_get_link_type to get link information.
    
    @param dev_src: Source device index
    @param dev_dst: Destination device index
    @return: Tuple of (hops, link_type), or -1 on error
    """
    try:
        handle_src = _get_processor_handle(dev_src)
        handle_dst = _get_processor_handle(dev_dst)
        hops = c_uint64()
        link_type = c_int()  # amdsmi_link_type_t
        ret = rocm_lib.amdsmi_topo_get_link_type(handle_src, handle_dst, byref(hops), byref(link_type))
        
        if rsmi_ret_ok(ret):
            return (hops.value, link_type.value)
        else:
            return -1
    except Exception as e:
        logging.error(f'Error getting link type between devices {dev_src} and {dev_dst}: {e}')
        return -1


def smi_is_device_p2p_accessible(dev_src, dev_dst):
    """Returns true if two devices are P2P accessible.
    
    Uses amdsmi_topo_get_p2p_status to check P2P accessibility.
    
    @param dev_src: Source device index
    @param dev_dst: Destination device index
    @return: True if P2P accessible, False otherwise, or -1 on error
    """
    try:
        handle_src = _get_processor_handle(dev_src)
        handle_dst = _get_processor_handle(dev_dst)
        link_type = c_int()  # amdsmi_link_type_t
        p2p_cap = amdsmi_p2p_capability_t()
        ret = rocm_lib.amdsmi_topo_get_p2p_status(handle_src, handle_dst, byref(link_type), byref(p2p_cap))
        
        if rsmi_ret_ok(ret):
            # Consider accessible if DMA is supported
            return bool(p2p_cap.is_iolink_dma)
        else:
            return -1
    except Exception as e:
        logging.error(f'Error checking P2P accessibility between devices {dev_src} and {dev_dst}: {e}')
        return -1


def smi_get_device_compute_process():
    """returns list of process ids running compute on the system"""
    num_procs = c_uint32()
    ret = rocm_lib.rsmi_compute_process_info_get(None, byref(num_procs))
    if rsmi_ret_ok(ret):
        buff_sz = num_procs.value + 10
        proc_info = (rsmi_process_info_t * buff_sz)()
        ret2 = rocm_lib.rsmi_compute_process_info_get(byref(proc_info), byref(num_procs))

        return [proc_info[i].process_id for i in range(num_procs.value)] if rsmi_ret_ok(ret2) else []
    else:
        return []


def smi_get_device_average_power(dev):
    """Returns average power consumption of the device in Watts.
    
    Uses amdsmi_get_power_info to retrieve power information.
    Returns average_socket_power for Navi/MI200 and earlier,
    or current_socket_power for MI300+ series.
    
    @param dev: Device index (0-based)
    @return: Power in Watts (float), or -1 on error
    """
    try:
        handle = _get_processor_handle(dev)
        power_info = amdsmi_power_info_t()
        ret = rocm_lib.amdsmi_get_power_info(handle, byref(power_info))
        
        if rsmi_ret_ok(ret):
            # For MI300+ series, use current_socket_power
            # For earlier cards, use average_socket_power
            # Try current first (MI300+), fallback to average
            if power_info.current_socket_power > 0:
                return float(power_info.current_socket_power)
            elif power_info.average_socket_power > 0:
                return float(power_info.average_socket_power)
            elif power_info.socket_power > 0:
                return float(power_info.socket_power)
            else:
                return -1
        else:
            return -1
    except Exception as e:
        logging.error(f'Error getting average power for device {dev}: {e}')
        return -1


# XGMI fuctions
def smi_get_device_xgmi_error_status(dev):
    """returns XGMI error status for a device"""
    status = rsmi_xgmi_status_t()
    ret = rocm_lib.rsmi_dev_xgmi_error_status(dev, byref(status))
    return status.value if rsmi_ret_ok(ret) else -1


def smi_reset_device_xgmi_error(dev):
    """resets XGMI error status for a device"""
    ret = rocm_lib.rsmi_dev_xgmi_error_reset(dev)
    return rsmi_ret_ok(ret)


def smi_get_device_xgmi_hive_id(dev):
    """returns XGMI hive ID for a device"""
    hive_id = c_uint64()
    ret = rocm_lib.rsmi_dev_xgmi_hive_id_get(dev, byref(hive_id))
    return hive_id.value if rsmi_ret_ok(ret) else -1


# constants for the UUID function
B1 = '%02x'
B2 = B1 * 2
B4 = B1 * 4
B6 = B1 * 6
nv_fmt = f'GPU-{B4}-{B2}-{B2}-{B2}-{B6}'

# UUID function
def smi_get_device_uuid(dev, format='roc'):
    """Returns the UUID of the device.
    
    Falls back to BDF-based unique ID since amdsmi_get_gpu_device_uuid
    may not be supported on all hardware/platforms.
    
    @param dev: Device index (0-based)
    @param format: Output format - 'roc' for ROCm format (GPU-xxx), 
                   'nv' for NVIDIA-style format, or 'raw' for raw UUID string
    @return: UUID string in the requested format, or empty string on error
    """
    try:
        # Try using amdsmi UUID API (may not be supported on all platforms)
        handle = _get_processor_handle(dev)
        
        # Allocate a fixed-size buffer (UUIDs are typically 64 bytes or less)
        uuid_buffer = create_string_buffer(256)
        uuid_length = c_uint(256)
        
        ret = rocm_lib.amdsmi_get_gpu_device_uuid(handle, byref(uuid_length), uuid_buffer)
        
        if rsmi_ret_ok(ret):
            uuid_str = uuid_buffer.value.decode('utf-8').rstrip('\x00')
            
            # Return in requested format
            if format == 'roc':
                # ROCm format: GPU-<uuid>
                if uuid_str.startswith('GPU-'):
                    return uuid_str
                else:
                    return f'GPU-{uuid_str}'
            elif format == 'raw':
                # Raw UUID without prefix
                if uuid_str.startswith('GPU-'):
                    return uuid_str[4:]
                else:
                    return uuid_str
            elif format == 'nv':
                # NVIDIA-style format: GPU-<8hex>-<4hex>-<4hex>-<4hex>-<12hex>
                # Get raw UUID (without GPU- prefix)
                raw_uuid = uuid_str[4:] if uuid_str.startswith('GPU-') else uuid_str
                # UUID is already in format "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
                # Just add GPU- prefix for NVIDIA format
                return f'GPU-{raw_uuid}'
            else:
                raise ValueError(f'Invalid format: \'{format}\'; use \'roc\', \'raw\', or \'nv\'')
        
        # Fallback: Generate UUID from BDF (unique but not the same as HSA UUID)
        logging.warning(f'amdsmi_get_gpu_device_uuid not supported, using BDF-based ID for device {dev}')
        
        bdf_id = smi_get_device_unique_id(dev)
        if bdf_id == -1:
            logging.error(f'Failed to get BDF-based unique ID for device {dev}')
            return ''
        
        # Format BDF as a hex string (pseudo-UUID)
        bdf_hex = f'{bdf_id:032x}'
        
        if format == 'roc':
            return f'GPU-{bdf_hex}'
        elif format == 'raw':
            return bdf_hex
        elif format == 'nv':
            # NVIDIA-style format from BDF hex: GPU-<8>-<4>-<4>-<4>-<12>
            # Format the 32-char hex string as UUID
            return f'GPU-{bdf_hex[:8]}-{bdf_hex[8:12]}-{bdf_hex[12:16]}-{bdf_hex[16:20]}-{bdf_hex[20:32]}'
        else:
            raise ValueError(f'Invalid format: \'{format}\'; use \'roc\', \'raw\', or \'nv\'')
    
    except Exception as e:
        logging.error(f'Error getting UUID for device {dev}: {e}')
        return ''
