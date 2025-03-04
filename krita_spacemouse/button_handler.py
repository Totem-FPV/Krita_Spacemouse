# button_handler.py
from PyQt5.QtCore import Qt, QTimer
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

    # Initialize button press tracking if not present
    if not hasattr(self, 'button_press_times'):
        self.button_press_times = {}
    if not hasattr(self, 'long_press_timer'):
        self.long_press_timer = QTimer()
        self.long_press_timer.setSingleShot(True)

    # Disconnect previous timeout signal to avoid stale button_id
    try:
        self.long_press_timer.timeout.disconnect()
    except TypeError:
        pass  # No previous connection, safe to ignore
    self.long_press_timer.timeout.connect(lambda: handle_long_press(self, button_id))

    # Get long press duration from docker (default 500ms)
    long_press_duration = getattr(docker, 'long_press_duration', 500)

    if press_state:  # Button pressed
        self.button_press_times[button_id] = time.time() * 1000  # Store start time in ms
        self.long_press_timer.start(long_press_duration)
    else:  # Button released
        if button_id in self.button_press_times:
            press_duration = (time.time() * 1000) - self.button_press_times[button_id]
            del self.button_press_times[button_id]
            self.long_press_timer.stop()
            if press_duration < long_press_duration:
                handle_short_press(self, button_id, mappings)
            # Long press is handled by timer if it fires

def handle_short_press(self, button_id, mappings):
    active_modifier = "None"
    for mod, state in self.modifier_states.items():
        if state and mod in ["Shift", "Ctrl", "Alt", "Super", "Meta"]:
            active_modifier = mod
            break

    action_name = mappings.get(active_modifier, mappings.get("None", "None"))
    debug_print(f"Short press mapped: {active_modifier}+{action_name}", 1, debug_level=self.docker.debug_level_value)
    execute_action(self, button_id, action_name, self.docker.debug_level_value)

def handle_long_press(self, button_id):
    mappings = self.docker.settings.button_mappings.get(str(button_id), {"None": "None"})
    action_name = mappings.get("Long", "None")
    if action_name != "None":
        debug_print(f"Long press on {button_id}: {action_name}", 1, debug_level=self.docker.debug_level_value)
        execute_action(self, button_id, action_name, self.docker.debug_level_value)

def execute_action(self, button_id, action_name, debug_level):
    modifier_map = {
        "Shift": "shift",
        "Ctrl": "ctrl",
        "Alt": "alt",
        "Super": "super",
        "Meta": "meta"
    }
    if action_name in modifier_map:
        key = modifier_map[action_name]
        if action_name not in self.modifier_states or self.modifier_states[action_name] != (action_name in self.button_press_times):
            if action_name in self.button_press_times:
                pyautogui.keyDown(key)
            else:
                pyautogui.keyUp(key)
            self.modifier_states[action_name] = action_name in self.button_press_times
            debug_print(f"Modifier {action_name} {'down' if action_name in self.button_press_times else 'up'}", 4, debug_level=debug_level)
        return

    if action_name != "None":
        view = Krita.instance().activeWindow().activeView()
        if not view:
            debug_print("No active view for button action", 1, debug_level=debug_level)
            return

        elif action_name.startswith("BrushPreset:"):
            preset_name = action_name.split(":", 1)[1]
            resources = Krita.instance().resources("preset")
            preset = resources.get(preset_name, None)
            if preset:
                try:
                    view.setCurrentBrushPreset(preset)
                    self.recent_presets.append(preset_name)
                    if len(self.recent_presets) > 2:
                        self.recent_presets.pop(0)
                    debug_print(f"Applied brush preset: {preset_name}", 1, debug_level=debug_level)
                except AttributeError:
                    debug_print(f"Failed to set brush preset '{preset_name}' - API method not available", 1, debug_level=debug_level)
            else:
                debug_print(f"Brush preset not found: {preset_name}", 1, debug_level=debug_level)

        elif action_name == "previous_preset":
            if self.recent_presets and len(self.recent_presets) > 1:
                previous_name = self.recent_presets[-2]
                resources = Krita.instance().resources("preset")
                preset = resources.get(previous_name, None)
                if preset:
                    view.setBrushPreset(preset)
                    debug_print(f"Reverted to previous preset: {previous_name}", 1, debug_level=debug_level)
                else:
                    debug_print(f"Previous preset not found: {previous_name}", 1, debug_level=debug_level)
            else:
                debug_print("No previous preset available", 1, debug_level=debug_level)

        elif action_name.startswith("store_view_") or action_name.startswith("recall_view_"):
            canvas = view.canvas()
            qwin = Krita.instance().activeWindow().qwindow()
            subwindow = qwin.findChild(QMdiArea).currentSubWindow()
            if not subwindow:
                debug_print("No subwindow for view action", 1, debug_level=debug_level)
                return
            scroll_area = subwindow.widget().findChild(QAbstractScrollArea)
            if not scroll_area:
                debug_print("No scroll area for view action", 1, debug_level=debug_level)
                return
            hscroll = scroll_area.horizontalScrollBar()
            vscroll = scroll_area.verticalScrollBar()
            if not (hscroll and vscroll):
                debug_print("Scrollbars missing for view action", 1, debug_level=debug_level)
                return

            view_key = action_name.split("_")[-1]
            ZOOM_SCALE_FACTOR = 4.17
            if action_name.startswith("store_view_"):
                x = hscroll.value()
                y = vscroll.value()
                zoom = canvas.zoomLevel()
                rotation = canvas.rotation()
                self.view_states[view_key] = (x, y, zoom, rotation)
                debug_print(f"Stored view {view_key}: x={x}, y={y}, zoom={zoom}, rotation={rotation}", 1, debug_level=debug_level)
            elif action_name.startswith("recall_view_"):
                if self.view_states.get(view_key):
                    x, y, zoom, rotation = self.view_states[view_key]
                    canvas.setZoomLevel(zoom / ZOOM_SCALE_FACTOR)
                    QApplication.processEvents()
                    canvas.setRotation(rotation)
                    hscroll.setValue(x)
                    vscroll.setValue(y)
                    QApplication.processEvents()
                    debug_print(f"Recalled view {view_key}: x={x}, y={y}, zoom={zoom}, rotation={rotation}", 1, debug_level=debug_level)
                else:
                    debug_print(f"No view stored for {view_key}", 1, debug_level=debug_level)

        elif action_name in ["lock_rotation", "lock_zoom", "lock_both"]:
            if action_name == "lock_rotation":
                self.lock_rotation = not self.lock_rotation
                self.lock_zoom = False
                debug_print(f"Rotation lock {'enabled' if self.lock_rotation else 'disabled'}, Zoom lock disabled", 1, debug_level=debug_level)
            elif action_name == "lock_zoom":
                self.lock_zoom = not self.lock_zoom
                self.lock_rotation = False
                debug_print(f"Zoom lock {'enabled' if self.lock_zoom else 'disabled'}, Rotation lock disabled", 1, debug_level=debug_level)
            elif action_name == "lock_both":
                self.lock_rotation = not self.lock_rotation
                self.lock_zoom = self.lock_rotation
                debug_print(f"Rotation and Zoom lock {'enabled' if self.lock_rotation else 'disabled'}", 1, debug_level=debug_level)

        else:
            action = Krita.instance().action(action_name)
            if action:
                action.trigger()
                debug_print(f"Triggered action: {action_name}", 4, debug_level=debug_level)
            else:
                debug_print(f"Action {action_name} not found", 1, debug_level=debug_level)
