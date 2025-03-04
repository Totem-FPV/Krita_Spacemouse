# button_handler.py
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMdiArea, QAbstractScrollArea, QApplication
from krita import Krita
from .utils import debug_print
import time
import pyautogui

def process_button_event(self, button_id, press_state):
    docker = self.docker
    debug_print(f"Button event - ID={button_id}, Press={press_state}", 1, debug_level=docker.debug_level_value)
    mappings = docker.settings.button_mappings.get(str(button_id), {"None": "None"})
    if isinstance(mappings, str):
        mappings = {"None": mappings}

    # Map modifier strings to Qt enums for consistency (though pyautogui uses strings)
    modifier_map = {
        "Shift": Qt.ShiftModifier,
        "Ctrl": Qt.ControlModifier,
        "Alt": Qt.AltModifier,
        "Super": Qt.Key_Super_L,
        "Meta": Qt.MetaModifier
    }

    # Determine active modifier from states
    active_modifier = "None"
    for mod, state in self.modifier_states.items():
        if state and mod in modifier_map:
            active_modifier = mod
            break

    action_name = mappings.get(active_modifier, mappings.get("None", "None"))
    debug_print(f"Action mapped: {active_modifier}+{action_name}", 1, debug_level=docker.debug_level_value)

    # Handle modifier-only actions with pyautogui simulation
    if action_name in modifier_map:
        if press_state != self.modifier_states[action_name]:  # Only act if state changes
            key = action_name.lower()  # pyautogui uses lowercase: "shift", "ctrl", etc.
            if press_state:
                pyautogui.keyDown(key)
            else:
                pyautogui.keyUp(key)
            self.modifier_states[action_name] = press_state
            debug_print(f"Modifier {action_name} {'down' if press_state else 'up'}", 4, debug_level=docker.debug_level_value)
        return

    # Process actions only on press
    if press_state and action_name != "None":
        view = Krita.instance().activeWindow().activeView()
        if not view:
            debug_print("No active view for button action", 1, debug_level=docker.debug_level_value)
            return

        elif action_name.startswith("BrushPreset:"):
            preset_name = action_name.split(":", 1)[1]
            resources = Krita.instance().resources("preset")
            preset = resources.get(preset_name, None)
            if preset:
                try:
                    view.setCurrentBrushPreset(preset)  # Updated method
                    self.recent_presets.append(preset_name)
                    if len(self.recent_presets) > 2:
                        self.recent_presets.pop(0)
                    debug_print(f"Applied brush preset: {preset_name}", 1, debug_level=docker.debug_level_value)
                except AttributeError:
                    debug_print(f"Failed to set brush preset '{preset_name}' - API method not available", 1, debug_level=docker.debug_level_value)
            else:
                debug_print(f"Brush preset not found: {preset_name}", 1, debug_level=docker.debug_level_value)

        elif action_name == "previous_preset":
            if self.recent_presets and len(self.recent_presets) > 1:
                previous_name = self.recent_presets[-2]
                resources = Krita.instance().resources("preset")
                preset = resources.get(previous_name, None)
                if preset:
                    view.setBrushPreset(preset)
                    debug_print(f"Reverted to previous preset: {previous_name}", 1, debug_level=docker.debug_level_value)
                else:
                    debug_print(f"Previous preset not found: {previous_name}", 1, debug_level=docker.debug_level_value)
            else:
                debug_print("No previous preset available", 1, debug_level=docker.debug_level_value)

        elif action_name.startswith("store_view_") or action_name.startswith("recall_view_"):
            canvas = view.canvas()
            qwin = Krita.instance().activeWindow().qwindow()
            subwindow = qwin.findChild(QMdiArea).currentSubWindow()
            if not subwindow:
                debug_print("No subwindow for view action", 1, debug_level=docker.debug_level_value)
                return
            scroll_area = subwindow.widget().findChild(QAbstractScrollArea)
            if not scroll_area:
                debug_print("No scroll area for view action", 1, debug_level=docker.debug_level_value)
                return
            hscroll = scroll_area.horizontalScrollBar()
            vscroll = scroll_area.verticalScrollBar()
            if not (hscroll and vscroll):
                debug_print("Scrollbars missing for view action", 1, debug_level=docker.debug_level_value)
                return

            view_key = action_name.split("_")[-1]
            ZOOM_SCALE_FACTOR = 4.17
            if action_name.startswith("store_view_"):
                x = hscroll.value()
                y = vscroll.value()
                zoom = canvas.zoomLevel()
                rotation = canvas.rotation()
                self.view_states[view_key] = (x, y, zoom, rotation)
                debug_print(f"Stored view {view_key}: x={x}, y={y}, zoom={zoom}, rotation={rotation}", 1, debug_level=docker.debug_level_value)
            elif action_name.startswith("recall_view_"):
                if self.view_states.get(view_key):
                    x, y, zoom, rotation = self.view_states[view_key]
                    canvas.setZoomLevel(zoom / ZOOM_SCALE_FACTOR)
                    QApplication.processEvents()
                    canvas.setRotation(rotation)
                    hscroll.setValue(x)
                    vscroll.setValue(y)
                    QApplication.processEvents()
                    debug_print(f"Recalled view {view_key}: x={x}, y={y}, zoom={zoom}, rotation={rotation}", 1, debug_level=docker.debug_level_value)
                else:
                    debug_print(f"No view stored for {view_key}", 1, debug_level=docker.debug_level_value)

        elif action_name in ["lock_rotation", "lock_zoom", "lock_both"]:
            if action_name == "lock_rotation":
                self.lock_rotation = not self.lock_rotation
                self.lock_zoom = False
                debug_print(f"Rotation lock {'enabled' if self.lock_rotation else 'disabled'}, Zoom lock disabled", 1, debug_level=docker.debug_level_value)
            elif action_name == "lock_zoom":
                self.lock_zoom = not self.lock_zoom
                self.lock_rotation = False
                debug_print(f"Zoom lock {'enabled' if self.lock_zoom else 'disabled'}, Rotation lock disabled", 1, debug_level=docker.debug_level_value)
            elif action_name == "lock_both":
                self.lock_rotation = not self.lock_rotation
                self.lock_zoom = self.lock_rotation
                debug_print(f"Rotation and Zoom lock {'enabled' if self.lock_rotation else 'disabled'}", 1, debug_level=docker.debug_level_value)

        else:
            action = Krita.instance().action(action_name)
            if action:
                action.trigger()
                debug_print(f"Triggered action: {action_name}", 4, debug_level=docker.debug_level_value)
            else:
                debug_print(f"Action {action_name} not found", 1, debug_level=docker.debug_level_value)
