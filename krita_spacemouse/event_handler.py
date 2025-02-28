from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMdiArea, QScrollBar, QAbstractScrollArea
from krita import Krita
from .spnav import libspnav, SPNAV_EVENT_MOTION, SPNAV_EVENT_BUTTON
from .utils import debug_print
import ctypes
from time import time
import pyautogui
import os
import math

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
            debug_print(f"Event type: {self.event.type}", 1, debug_level=docker.debug_level_value)
            if self.event.type == SPNAV_EVENT_BUTTON:
                button_id = self.event.event.button.bnum
                press_state = self.event.event.button.press == 1
                debug_print(f"Button event - ID={button_id}, Press={press_state}", 1, debug_level=docker.debug_level_value)
                mappings = docker.settings.button_mappings.get(str(button_id), {"None": "None"})
                if isinstance(mappings, str):
                    mappings = {"None": mappings}
                modifier_key = "None"
                if self.modifier_states["Ctrl"]:
                    modifier_key = "Ctrl"
                elif self.modifier_states["Alt"]:
                    modifier_key = "Alt"
                elif self.modifier_states["Shift"]:
                    modifier_key = "Shift"
                action_name = mappings.get(modifier_key, mappings.get("None", "None"))
                debug_print(f"Action mapped: {modifier_key}+{action_name}", 1, debug_level=docker.debug_level_value)
                if action_name in ["Shift", "Ctrl", "Alt"]:
                    debug_print(f"Modifier {action_name} detected", 1, debug_level=docker.debug_level_value)
                    if press_state != self.modifier_states[action_name]:
                        key = action_name.lower()
                        if press_state:
                            pyautogui.keyDown(key)
                        else:
                            pyautogui.keyUp(key)
                        self.modifier_states[action_name] = press_state
                        debug_print(f"{action_name} {'down' if press_state else 'up'}", 4, debug_level=docker.debug_level_value)
                elif press_state and action_name != "None":
                    if action_name.startswith("BrushPreset:"):
                        preset_name = action_name[len("BrushPreset:"):]
                        presets = Krita.instance().resources("preset")
                        preset = presets.get(preset_name)
                        if preset and view:
                            Krita.instance().writeSetting("", "currentBrushPreset", preset_name)
                            view.setCurrentBrushPreset(preset)
                            if len(self.recent_presets) >= 2:
                                self.recent_presets.pop(0)
                            self.recent_presets.append(preset_name)
                            debug_print(f"Switched to brush preset: {preset_name}, recent: {self.recent_presets}", 4, debug_level=docker.debug_level_value)
                        else:
                            debug_print(f"Brush preset '{preset_name}' not found or no active view", 1, debug_level=docker.debug_level_value)
                    elif action_name == "previous_preset":
                        if len(self.recent_presets) >= 2:
                            last_preset = self.recent_presets[-2]
                            preset = Krita.instance().resources("preset").get(last_preset)
                            if preset and view:
                                Krita.instance().writeSetting("", "currentBrushPreset", last_preset)
                                view.setCurrentBrushPreset(preset)
                                self.recent_presets.pop()
                                self.recent_presets.insert(0, last_preset)
                                debug_print(f"Toggled to previous preset: {last_preset}", 4, debug_level=docker.debug_level_value)
                            else:
                                debug_print(f"Previous preset '{last_preset}' not found", 1, debug_level=docker.debug_level_value)
                        else:
                            debug_print("Not enough recent presets to toggle", 1, debug_level=docker.debug_level_value)
                    elif action_name in ["Toggle V1", "Toggle V2", "Toggle V3"]:
                        view_key = action_name.split()[1]
                        qwin = window.qwindow()
                        subwindow = qwin.findChild(QMdiArea).currentSubWindow()
                        if not subwindow:
                            debug_print(f"No subwindow for {view_key}", 5, debug_level=docker.debug_level_value)
                            continue
                        canvas_widget = subwindow.widget()
                        if not canvas_widget:
                            debug_print(f"No canvas widget for {view_key}", 5, debug_level=docker.debug_level_value)
                            continue
                        scroll_area = canvas_widget.findChild(QAbstractScrollArea)
                        if not scroll_area:
                            debug_print(f"No scroll area for {view_key}", 5, debug_level=docker.debug_level_value)
                            continue
                        hscroll = scroll_area.horizontalScrollBar()
                        vscroll = scroll_area.verticalScrollBar()
                        if not (hscroll and vscroll):
                            debug_print(f"Scrollbars missing for {view_key}", 5, debug_level=docker.debug_level_value)
                            continue
                        if modifier_key == "Shift":
                            x = hscroll.value()
                            y = vscroll.value()
                            zoom = canvas.zoomLevel()
                            rotation = canvas.rotation()
                            self.view_states[view_key] = (x, y, zoom, rotation)
                            debug_print(f"Saved view {view_key}: x={x}, y={y}, zoom={zoom}, rotation={rotation}", 5, debug_level=docker.debug_level_value)
                        elif self.view_states.get(view_key):
                            x, y, zoom, rotation = self.view_states[view_key]
                            current_x = hscroll.value()
                            current_y = vscroll.value()
                            current_zoom = canvas.zoomLevel()
                            current_rotation = canvas.rotation()
                            if (abs(current_x - x) > 1 or abs(current_y - y) > 1 or
                                abs(current_zoom - zoom) > 0.01 or abs(current_rotation - rotation) > 0.1):
                                hscroll.setValue(x)
                                vscroll.setValue(y)
                                canvas.setZoomLevel(zoom)
                                canvas.setRotation(rotation)
                                debug_print(f"Recalled view {view_key}: x={x}, y={y}, zoom={zoom}, rotation={rotation}", 5, debug_level=docker.debug_level_value)
                            else:
                                debug_print(f"View {view_key} already at saved state: x={current_x}, y={current_y}, zoom={current_zoom}, rotation={current_rotation}", 5, debug_level=docker.debug_level_value)
                            libspnav.spnav_remove_events(SPNAV_EVENT_MOTION)
                            continue
                        else:
                            debug_print(f"No view saved for {view_key}", 5, debug_level=docker.debug_level_value)
                    else:
                        action = Krita.instance().action(action_name)
                        if action:
                            action.trigger()
                            debug_print(f"Triggered action: {action_name}", 4, debug_level=docker.debug_level_value)
                            libspnav.spnav_remove_events(SPNAV_EVENT_MOTION)
                        else:
                            debug_print(f"Action {action_name} not found", 1, debug_level=docker.debug_level_value)
            elif self.event.type == SPNAV_EVENT_MOTION:
                axis_inputs = {
                    "x": self.event.event.motion.x,
                    "y": self.event.event.motion.y,
                    "z": self.event.event.motion.z,
                    "rx": self.event.event.motion.rx,
                    "ry": self.event.event.motion.ry,
                    "rz": self.event.event.motion.rz
                }
                debug_print(f"Raw SN inputs: {axis_inputs}", 2, debug_level=docker.debug_level_value)
                latest_inputs = axis_inputs.copy()
            else:
                debug_print(f"Unknown event type: {self.event.type}", 1, debug_level=docker.debug_level_value)

        if num_events > 0:
            debug_print("Polling SpaceNavigator...", 2, debug_level=docker.debug_level_value)
            debug_print(f"Number of events: {num_events}", 2, debug_level=docker.debug_level_value)
            self.last_motion_data = latest_inputs
            if self.last_logged_motion != self.last_motion_data:
                debug_print(f"Motion data stored: {self.last_motion_data}", 2, debug_level=docker.debug_level_value)
                self.last_logged_motion = self.last_motion_data.copy()

            max_input = 500
            dx = dy = zoom_delta = rotation_delta = 0
            zoom_scale = 0.004
            rotation_scale = 0.04
            modifiers = Qt.NoModifier
            if 0 in self.button_states and self.button_states[0]:
                modifiers |= Qt.ShiftModifier

            debug_print(f"Puck mappings: {docker.settings.puck_mappings}", 1, debug_level=docker.debug_level_value)
            debug_print(f"Axis settings: {{k: v for k, v in docker.settings.axis_settings.items()}}", 1, debug_level=docker.debug_level_value)

            for sm_axis in ["x", "y", "z", "rx", "ry", "rz"]:
                action = docker.settings.puck_mappings.get(sm_axis.upper(), "None")
                if action == "None":
                    debug_print(f"Axis {sm_axis} mapped to None, skipping", 2, debug_level=docker.debug_level_value)
                    continue
                canvas_axis = action.split()[0]
                if canvas_axis == "Pan" and "Horizontal" in action:
                    axis_key = "X"
                elif canvas_axis == "Pan" and "Vertical" in action:
                    axis_key = "Y"
                else:
                    axis_key = canvas_axis

                full_axis = f"{axis_key} (Panning Horizontal)" if axis_key == "X" else f"{axis_key} (Panning Vertical)" if axis_key == "Y" else axis_key
                if full_axis not in docker.settings.axis_settings:
                    debug_print(f"Axis {full_axis} not in axis_settings", 1, debug_level=docker.debug_level_value)
                    continue

                settings = docker.settings.axis_settings[full_axis]
                sensitivity = settings["sensitivity"]
                invert = -1 if settings["invert"] else 1
                dead_zone = settings["dead_zone"]
                raw_input = self.last_motion_data.get(sm_axis, 0)

                debug_print(f"Processing {sm_axis} -> {full_axis}: raw_input={raw_input}", 2, debug_level=docker.debug_level_value)

                normalized_input = max(0, min(1, (abs(raw_input) - dead_zone) / (max_input - dead_zone))) if abs(raw_input) >= dead_zone else 0
                try:
                    curve_output = docker.curves_tab.curve_editors[axis_key].get_curve_value(normalized_input)
                except KeyError:
                    debug_print(f"Curve editor for {axis_key} not found", 1, debug_level=docker.debug_level_value)
                    continue
                scaled_value = curve_output * max_input * sensitivity * (1 if raw_input >= 0 else -1) * invert

                if abs(raw_input) >= dead_zone:
                    if axis_key == "X":
                        dx = int(scaled_value)
                    elif axis_key == "Y":
                        dy = int(scaled_value)
                    elif axis_key == "Zoom":
                        zoom_delta = scaled_value * zoom_scale
                        debug_print(f"Zoom detected: delta={zoom_delta}", 1, debug_level=docker.debug_level_value)
                    elif axis_key == "Rotation":
                        rotation_delta = max(min(scaled_value * rotation_scale, 10.0), -10.0)
                debug_print(f"Axis {axis_key}: raw={raw_input}, norm={normalized_input}, curve={curve_output}, scaled={scaled_value}", 2, debug_level=docker.debug_level_value)

            qwin = window.qwindow()
            subwindow = qwin.findChild(QMdiArea).currentSubWindow()
            if not subwindow:
                debug_print("No subwindow found", 1, debug_level=docker.debug_level_value)
                return
            scrollbars = subwindow.findChildren(QScrollBar)
            hscroll = vscroll = None
            for sb in scrollbars:
                if sb.orientation() == Qt.Horizontal:
                    hscroll = sb
                elif sb.orientation() == Qt.Vertical:
                    vscroll = sb
            if not (hscroll and vscroll):
                debug_print("Scrollbars not found", 1, debug_level=docker.debug_level_value)
                return

            if dx != 0 or dy != 0:
                debug_print(f"Computed Pan: dx={dx}, dy={dy}", 1, debug_level=docker.debug_level_value)
                if modifiers & Qt.ShiftModifier:
                    if abs(dx) > abs(dy):
                        dy = 0
                    else:
                        dx = 0
                old_h = hscroll.value()
                old_v = vscroll.value()
                hscroll.setValue(hscroll.value() + dx)
                vscroll.setValue(vscroll.value() + dy)
                debug_print(f"Panned: dx={dx}, dy={dy}, hscroll={old_h}->{hscroll.value()}, vscroll={old_v}->{vscroll.value()}, modifiers={modifiers}", 1, debug_level=docker.debug_level_value)
                self.last_dx, self.last_dy = dx, dy
                libspnav.spnav_remove_events(SPNAV_EVENT_MOTION)

            if zoom_delta != 0:
                zoom_action = "view_zoom_in" if zoom_delta > 0 else "view_zoom_out"
                action = Krita.instance().action(zoom_action)
                if action:
                    steps = int(abs(zoom_delta) * 10)
                    for _ in range(steps):
                        action.trigger()
                    debug_print(f"Zoomed {'in' if zoom_delta > 0 else 'out'} by {steps} steps, delta={zoom_delta}", 1, debug_level=docker.debug_level_value)
                    self.last_zoom_delta = zoom_delta
                    libspnav.spnav_remove_events(SPNAV_EVENT_MOTION)
                else:
                    debug_print(f"Zoom action {zoom_action} not found", 1, debug_level=docker.debug_level_value)

            if rotation_delta != 0:
                current_rotation = canvas.rotation()
                new_rotation = current_rotation + rotation_delta
                canvas.setRotation(new_rotation)
                debug_print(f"Rotated to: {new_rotation}, modifiers={modifiers}", 1, debug_level=docker.debug_level_value)
                self.last_rotation_delta = rotation_delta
                libspnav.spnav_remove_events(SPNAV_EVENT_MOTION)

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
