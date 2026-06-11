import ctypes, time

ndi = ctypes.CDLL(r'C:\Program Files\NDI\NDI 6 Tools\Runtime\Processing.NDI.Lib.x64.dll')

class NDIlib_source_t(ctypes.Structure):
    _fields_ = [
        ('p_ndi_name', ctypes.c_char_p),
        ('p_url_address', ctypes.c_char_p),
    ]

class NDIlib_find_create_t(ctypes.Structure):
    _fields_ = [
        ('show_local_sources', ctypes.c_bool),
        ('p_groups', ctypes.c_char_p),
        ('p_extra_ips', ctypes.c_char_p),
    ]

ndi.NDIlib_initialize.restype = ctypes.c_bool
ndi.NDIlib_find_create_v2.argtypes = [ctypes.POINTER(NDIlib_find_create_t)]
ndi.NDIlib_find_create_v2.restype = ctypes.c_void_p
ndi.NDIlib_find_wait_for_sources.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
ndi.NDIlib_find_wait_for_sources.restype = ctypes.c_bool
ndi.NDIlib_find_get_current_sources.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint32)]
ndi.NDIlib_find_get_current_sources.restype = ctypes.POINTER(NDIlib_source_t)
ndi.NDIlib_find_destroy.argtypes = [ctypes.c_void_p]

if not ndi.NDIlib_initialize():
    print('NDI init failed')
    raise SystemExit(1)

create = NDIlib_find_create_t(True, None, None)
finder = ndi.NDIlib_find_create_v2(ctypes.byref(create))
if not finder:
    print('finder create failed')
    raise SystemExit(2)

ndi.NDIlib_find_wait_for_sources(finder, 3000)
time.sleep(1)

count = ctypes.c_uint32(0)
sources_ptr = ndi.NDIlib_find_get_current_sources(finder, ctypes.byref(count))

print(f'Found {count.value} NDI sources:')
for i in range(count.value):
    s = sources_ptr[i]
    name = s.p_ndi_name.decode('utf-8', errors='replace') if s.p_ndi_name else '?'
    url = s.p_url_address.decode('utf-8', errors='replace') if s.p_url_address else '?'
    print(f'  [{i}] name="{name}"  url={url}')

ndi.NDIlib_find_destroy(finder)
ndi.NDIlib_destroy()
