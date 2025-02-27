from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtWidgets import QApplication, QScrollBar, QMdiArea, QDockWidget
from krita import Extension, Krita, DockWidgetFactory, DockWidgetFactoryBase
from .spnav import libspnav, SpnavEventWrapper, SPNAV_EVENT_BUTTON, SPNAV_EVENT_MOTION
from .docker import SpacenavDocker
from .utils import debug_print
from .event_handler import poll_spacenav, update_lcd_buttons  # New import
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
        self.lcd_fd = None
        self.modifier_states = {"Shift": False, "Ctrl": False, "Alt": False}
        self.recent_presets = []
        self.view_states = {"V1": None, "V2": None, "V3": None}  # (x, y, zoom, rotation)
        debug_print("SpacenavControlExtension initialized", 1, debug_level=1)

    def setup(self):
        debug_print("SpacenavControlExtension: Setting up...", 1, debug_level=self.docker.debug_level_value if self.docker else 1)
        socket_path = "/var/run/spnav.sock"
        if not os.path.exists(socket_path):
            debug_print(f"Error: Socket {socket_path} not found.", 1, debug_level=self.docker.debug_level_value if self.docker else 1)
            return
        result = libspnav.spnav_open()
        if result == -1:
            debug_print("Error: Failed to connect to SpaceNavigator daemon", 1, debug_level=self.docker.debug_level_value if self.docker else 1)
            return
        debug_print("Connected to SpaceNavigator daemon", 1, debug_level=self.docker.debug_level_value if self.docker else 1)
        cleared = libspnav.spnav_remove_events(SPNAV_EVENT_MOTION)
        debug_print(f"Initial queue clear: {cleared} motion events", 1, debug_level=self.docker.debug_level_value if self.docker else 1)
        self.timer.start(10)

        try:
            Krita.instance().addDockWidgetFactory(
                DockWidgetFactory("spacenavDocker", DockWidgetFactoryBase.DockRight, SpacenavDocker)
            )
            debug_print("Docker factory registered", 1, debug_level=self.docker.debug_level_value if self.docker else 1)
        except Exception as e:
            debug_print(f"Error registering docker: {e}", 1, debug_level=self.docker.debug_level_value if self.docker else 1)

    def createActions(self, window):
        debug_print("createActions called", 3, debug_level=self.docker.debug_level_value if self.docker else 1)
        self.docker = window.findChild(QDockWidget, "spacenavDocker")
        if self.docker:
            self.docker.set_extension(self)
            debug_print("Docker found and extension set in createActions", 1, debug_level=self.docker.debug_level_value)
            self.update_lcd_buttons()
        else:
            debug_print("Docker not found in createActions, listing all dockers...", 1, debug_level=1)
            dockers = Krita.instance().dockers()
            for d in dockers:
                debug_print(f"Docker: title={d.windowTitle()}, objectName={d.objectName()}", 3, debug_level=1)

    def poll_spacenav(self):
        poll_spacenav(self)  # Delegate to event_handler.py

    def update_lcd_buttons(self):
        update_lcd_buttons(self)  # Delegate to event_handler.py

    def stop(self):
        try:
            self.timer.stop()
            libspnav.spnav_close()
            if self.lcd_fd:
                os.close(self.lcd_fd)
                debug_print("LCD closed", 1, debug_level=self.docker.debug_level_value if self.docker else 1)
            debug_print("SpacenavControlExtension: Stopped.", 1, debug_level=self.docker.debug_level_value if self.docker else 1)
        except Exception as e:
            debug_print(f"Error in stop: {e}", 1, debug_level=self.docker.debug_level_value if self.docker else 1)
