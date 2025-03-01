from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMdiArea, QScrollBar
from krita import Krita
from krita_spacemouse.utils import debug_print
from krita_spacemouse.spnav import libspnav, SPNAV_EVENT_MOTION
import math

def process_motion_event(self, axis_inputs):
    docker = self.docker
    max_input = 500
    dx = dy = zoom_delta = rotation_delta = 0
    zoom_scale = 0.004
    rotation_scale = 0.04
    modifiers = Qt.NoModifier
    if 0 in self.button_states and self.button_states[0]:
        modifiers |= Qt.ShiftModifier

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
        raw_input = axis_inputs.get(sm_axis, 0)

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
            elif axis_key == "Rotation":
                rotation_delta = max(min(scaled_value * rotation_scale, 10.0), -10.0)

    qwin = Krita.instance().activeWindow().qwindow()
    subwindow = qwin.findChild(QMdiArea).currentSubWindow()
    if not subwindow:
        debug_print("No subwindow found", 1, debug_level=docker.debug_level_value)
        return
    hscroll = vscroll = None
    for sb in subwindow.findChildren(QScrollBar):
        if sb.orientation() == Qt.Horizontal:
            hscroll = sb
        elif sb.orientation() == Qt.Vertical:
            vscroll = sb
    if not (hscroll and vscroll):
        debug_print("Scrollbars not found", 1, debug_level=docker.debug_level_value)
        return

    view = Krita.instance().activeWindow().activeView()
    canvas = view.canvas()

    if dx != 0 or dy != 0:
        if modifiers & Qt.ShiftModifier:
            if abs(dx) > abs(dy):
                dy = 0
            else:
                dx = 0
        hscroll.setValue(hscroll.value() + dx)
        vscroll.setValue(vscroll.value() + dy)
        debug_print(f"Panned: dx={dx}, dy={dy}", 1, debug_level=docker.debug_level_value)
        libspnav.spnav_remove_events(SPNAV_EVENT_MOTION)

    if zoom_delta != 0:
        zoom_action = "view_zoom_in" if zoom_delta > 0 else "view_zoom_out"
        action = Krita.instance().action(zoom_action)
        if action:
            steps = int(abs(zoom_delta) * 10)
            for _ in range(steps):
                action.trigger()
            debug_print(f"Zoomed {'in' if zoom_delta > 0 else 'out'} by {steps} steps", 1, debug_level=docker.debug_level_value)
            libspnav.spnav_remove_events(SPNAV_EVENT_MOTION)
        else:
            debug_print(f"Zoom action {zoom_action} not found", 1, debug_level=docker.debug_level_value)

    if rotation_delta != 0:
        current_rotation = canvas.rotation()
        new_rotation = current_rotation + rotation_delta
        canvas.setRotation(new_rotation)
        debug_print(f"Rotated to: {new_rotation}", 1, debug_level=docker.debug_level_value)
        libspnav.spnav_remove_events(SPNAV_EVENT_MOTION)
