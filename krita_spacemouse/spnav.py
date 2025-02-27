import ctypes
from .utils import debug_print  # Import debug_print for error logging

try:
    libspnav = ctypes.CDLL("libspnav.so.0")
    debug_print("libspnav loaded successfully", 1, debug_level=1)
except OSError as e:
    debug_print(f"Error: Could not load libspnav.so.0 - {e}", 1, debug_level=1)
    raise

# Event type constants
SPNAV_EVENT_MOTION = 1
SPNAV_EVENT_BUTTON = 2

class SpnavMotionEvent(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_int), ("y", ctypes.c_int), ("z", ctypes.c_int),
        ("rx", ctypes.c_int), ("ry", ctypes.c_int), ("rz", ctypes.c_int),
        ("period", ctypes.c_uint)
    ]

class SpnavButtonEvent(ctypes.Structure):
    _fields_ = [
        ("press", ctypes.c_int),
        ("bnum", ctypes.c_int)
    ]

class SpnavEvent(ctypes.Union):
    _fields_ = [
        ("motion", SpnavMotionEvent),
        ("button", SpnavButtonEvent)
    ]

class SpnavEventWrapper(ctypes.Structure):
    _fields_ = [
        ("type", ctypes.c_int),
        ("event", SpnavEvent)
    ]

# Configure function signatures
libspnav.spnav_poll_event.argtypes = [ctypes.POINTER(SpnavEventWrapper)]
libspnav.spnav_poll_event.restype = ctypes.c_int
libspnav.spnav_remove_events.argtypes = [ctypes.c_int]
libspnav.spnav_remove_events.restype = ctypes.c_int
libspnav.spnav_open.argtypes = []
libspnav.spnav_open.restype = ctypes.c_int
libspnav.spnav_close.argtypes = []
libspnav.spnav_close.restype = ctypes.c_int
