# extension.py
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtWidgets import QApplication, QScrollBar, QMdiArea, QDockWidget, QMessageBox
from krita import Extension, Krita, DockWidgetFactory, DockWidgetFactoryBase
from .spnav import libspnav, SpnavEventWrapper, SPNAV_EVENT_BUTTON, SPNAV_EVENT_MOTION
from .docker import SpacenavDocker
from .utils import debug_print
from .event_handler import poll_spacenav
import os
import ctypes

class SpacenavControlExtension(Extension):
    def __init__(self, parent):
        super().__init__(parent)
        self.timer = QTimer()
        self.timer.timeout.connect(self.poll_spacenav)
        self.event = SpnavEventWrapper()
        self.current_zoom = 1.0
        self.docker = None
        self.last_motion_time = 0
        self.debounce_ms = 5
        self.last_dx = self.last_dy = self.last_zoom_delta = self.last_rotation_delta = 0
        self.last_motion_data = {"x": 0, "y": 0, "z": 0, "rx": 0, "ry": 0, "rz": 0}
        self.last_logged_motion = None
        self.button_states = {}
        self.modifier_states = {"Shift": False, "Ctrl": False, "Alt": False}
        self.recent_presets = []
        self.view_states = {"V1": None, "V2": None, "V3": None}  # (x, y, zoom, rotation)
        self.lock_rotation = False
        self.lock_zoom = False
        self.debug_level_value = 1
        from .settings import SettingsManager
        settings_manager = SettingsManager(self, load=False)  # Temp instance to peek at settings
        settings = settings_manager.load_settings()
        self.polling_interval = settings.get("polling_interval", 10) if settings else 10
        self.global_dead_zone = settings.get("global_dead_zone", 130) if settings else 130
        self.global_sensitivity = settings.get("global_sensitivity", 100) if settings else 100
        self.long_press_duration = settings.get("long_press_duration", 500) if settings else 500
        debug_print(f"SpacenavControlExtension initialized with polling_interval={self.polling_interval}ms", 1, debug_level=self.debug_level_value)

    def setup(self):
        debug_print("SpacenavControlExtension: Setting up...", 1, debug_level=self.docker.debug_level_value if self.docker else self.debug_level_value)

        # Dynamic socket detection
        possible_socket_paths = [
            "/var/run/spnav.sock",          # Arch Linux default
            "/tmp/.spnav.sock",             # Common on other distros
            os.path.join(os.environ.get("XDG_RUNTIME_DIR", "/tmp"), "spnav.sock"),  # XDG fallback
            os.environ.get("SPNAV_SOCKPATH")  # Custom env var, if set
        ]
        socket_path = None
        for path in possible_socket_paths:
            if path and os.path.exists(path):
                socket_path = path
                debug_print(f"SpaceMouse socket found at {socket_path}", 1, debug_level=self.docker.debug_level_value if self.docker else self.debug_level_value)
                break

        if not socket_path:
            QMessageBox.warning(None, "SpaceMouse Error", "No SpaceMouse socket found. Check if spacenavd is running.")
            debug_print("Error: No SpaceMouse socket found at common locations (/var/run/spnav.sock, /tmp/.spnav.sock, XDG_RUNTIME_DIR/spnav.sock, or SPNAV_SOCKPATH)", 1, debug_level=self.docker.debug_level_value if self.docker else self.debug_level_value)
            return  # Skip SpaceMouse setup but don’t crash

        # Set the socket path for libspnav (if needed, depends on implementation)
        # Note: libspnav typically uses X11 or autodetects; we assume it checks the socket
        result = libspnav.spnav_open()
        if result == -1:
            debug_print(f"Error: Failed to connect to SpaceNavigator daemon at {socket_path}", 1, debug_level=self.docker.debug_level_value if self.docker else self.debug_level_value)
            return
        debug_print("Connected to SpaceNavigator daemon", 1, debug_level=self.docker.debug_level_value if self.docker else self.debug_level_value)
        cleared = libspnav.spnav_remove_events(SPNAV_EVENT_MOTION)
        debug_print(f"Initial queue clear: {cleared} motion events", 1, debug_level=self.docker.debug_level_value if self.docker else self.debug_level_value)
        self.timer.start(self.polling_interval)

        try:
            Krita.instance().addDockWidgetFactory(
                DockWidgetFactory("spacenavDocker", DockWidgetFactoryBase.DockRight, SpacenavDocker)
            )
            debug_print("Docker factory registered", 1, debug_level=self.docker.debug_level_value if self.docker else self.debug_level_value)
        except Exception as e:
            debug_print(f"Error registering docker: {e}", 1, debug_level=self.docker.debug_level_value if self.docker else self.debug_level_value)

    def createActions(self, window):
        debug_print("createActions called", 3, debug_level=self.docker.debug_level_value if self.docker else self.debug_level_value)
        self.docker = window.findChild(QDockWidget, "spacenavDocker")
        if self.docker:
            self.docker.set_extension(self)
            debug_print("Docker found and extension set in createActions", 1, debug_level=self.docker.debug_level_value)
        else:
            debug_print("Docker not found in createActions, listing all dockers...", 1, debug_level=self.debug_level_value)
            dockers = Krita.instance().dockers()
            for d in dockers:
                debug_print(f"Docker: title={d.windowTitle()}, objectName={d.objectName()}", 3, debug_level=self.debug_level_value)

    def poll_spacenav(self):
        poll_spacenav(self)

    def stop(self):
        try:
            self.timer.stop()
            libspnav.spnav_close()
            debug_print("SpacenavControlExtension: Stopped.", 1, debug_level=self.docker.debug_level_value if self.docker else self.debug_level_value)
        except Exception as e:
            debug_print(f"Error in stop: {e}", 1, debug_level=self.docker.debug_level_value if self.docker else self.debug_level_value)

    def toggle_lock_rotation(self):
        self.lock_rotation = not self.lock_rotation
        debug_print(f"Rotation lock {'enabled' if self.lock_rotation else 'disabled'}", 1, debug_level=self.docker.debug_level_value if self.docker else self.debug_level_value)

    def toggle_lock_zoom(self):
        self.lock_zoom = not self.lock_zoom
        debug_print(f"Zoom lock {'enabled' if self.lock_zoom else 'disabled'}", 1, debug_level=self.docker.debug_level_value if self.docker else self.debug_level_value)

    def toggle_lock_both(self):
        self.lock_rotation = not self.lock_rotation
        self.lock_zoom = not self.lock_zoom
        debug_print(f"Rotation and Zoom lock {'enabled' if self.lock_rotation else 'disabled'}", 1, debug_level=self.docker.debug_level_value if self.docker else self.debug_level_value)
