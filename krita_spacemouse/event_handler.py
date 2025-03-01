from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMdiArea, QScrollBar, QAbstractScrollArea
from krita import Krita
from krita_spacemouse.spnav import libspnav, SPNAV_EVENT_MOTION, SPNAV_EVENT_BUTTON
from krita_spacemouse.utils import debug_print
from krita_spacemouse.button_handler import process_button_event
from krita_spacemouse.motion_handler import process_motion_event
import ctypes
from time import time
import os

def poll_spacenav(self):
    try:
        current_time = int(time() * 1000)
        window = Krita.instance().activeWindow()
        if not window or not window.activeView():
            debug_print("No active window or view found", 1, debug_level=self.docker.debug_level_value if self.docker else 1)
            return
        view = window.activeView()
        canvas = view.canvas()

        if not self.docker:
            dockers = Krita.instance().dockers()
            for d in dockers:
                if d.objectName() == "spacenavDocker":
                    self.docker = d
                    self.docker.set_extension(self)
                    debug_print("Docker found by objectName and extension set", 1, debug_level=1)
                    self.update_lcd_buttons()
                    break
            else:
                debug_print("Docker not found, using defaults", 1, debug_level=1)
                return
        docker = self.docker
        if not hasattr(self, '_debug_level_logged'):
            debug_print(f"Initial debug level: {docker.debug_level_value if docker else 1}", 1, debug_level=docker.debug_level_value if self.docker else 1)
            self._debug_level_logged = True

        num_events = 0
        latest_inputs = self.last_motion_data.copy()
        while True:
            result = libspnav.spnav_poll_event(ctypes.byref(self.event))
            if result == 0:
                break
            num_events += 1
            debug_print(f"Poll result: {result}, Events: {num_events}", 2, debug_level=docker.debug_level_value)
            if self.event.type == SPNAV_EVENT_BUTTON:
                process_button_event(self, self.event.event.button.bnum, self.event.event.button.press == 1)
            elif self.event.type == SPNAV_EVENT_MOTION:
                axis_inputs = {
                    "x": self.event.event.motion.x, "y": self.event.event.motion.y, "z": self.event.event.motion.z,
                    "rx": self.event.event.motion.rx, "ry": self.event.event.motion.ry, "rz": self.event.event.motion.rz
                }
                debug_print(f"Raw SN inputs: {axis_inputs}", 2, debug_level=docker.debug_level_value)
                latest_inputs = axis_inputs.copy()
                process_motion_event(self, latest_inputs)

        if num_events > 0:
            debug_print("Polling SpaceNavigator...", 2, debug_level=docker.debug_level_value)
            self.last_motion_data = latest_inputs
            if self.last_logged_motion != self.last_motion_data:
                debug_print(f"Motion data stored: {self.last_motion_data}", 2, debug_level=docker.debug_level_value)
                self.last_logged_motion = self.last_motion_data.copy()
            if num_events > 5:
                cleared = libspnav.spnav_remove_events(SPNAV_EVENT_MOTION)
                debug_print(f"Cleared {cleared} motion events after {num_events} processed", 1, debug_level=docker.debug_level_value)

        self.last_motion_time = current_time

    except OSError as e:
        debug_print(f"Socket error in poll: {e}", 1, debug_level=self.docker.debug_level_value if self.docker else 1)
        self.timer.stop()
    except AttributeError as e:
        debug_print(f"Krita API error in poll: {e}", 1, debug_level=self.docker.debug_level_value if self.docker else 1)
    except Exception as e:
        debug_print(f"Unexpected error in poll: {e}", 1, debug_level=self.docker.debug_level_value if self.docker else 1)
        self.timer.stop()

def update_lcd_buttons(self):
    try:
        if not self.docker or not self.lcd_fd:
            return
        mappings = self.docker.settings.button_mappings
        lines = [f"{i}: {mappings.get(str(i), {'None': 'None'}).get('None', 'None')[:10]}" for i in range(12)]
        svg_text = "\n".join(f'<text x="10" y="{30 + i*20}" font-size="18" fill="white">{line}</text>' for i, line in enumerate(lines))
        svg = f"""<svg width="320" height="240" xmlns="http://www.w3.org/2000/svg">
                    <rect x="0" y="0" width="320" height="240" fill="black"/>
                    {svg_text}
                  </svg>""".encode()
        packet = bytearray([0x03]) + svg[:63] + b'\x00' * (64 - len(svg[:63]))
        os.write(self.lcd_fd, packet)
        debug_print("LCD: Updated buttons 0-11", 1, debug_level=self.docker.debug_level_value if self.docker else 1)
    except OSError as e:
        debug_print(f"LCD write failed: {e}", 1, debug_level=self.docker.debug_level_value if self.docker else 1)
