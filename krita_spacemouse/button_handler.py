from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMdiArea, QAbstractScrollArea
from krita import Krita
from krita_spacemouse.utils import debug_print
from krita_spacemouse.spnav import libspnav, SPNAV_EVENT_MOTION
import pyautogui

def process_button_event(self, button_id, press_state):
    docker = self.docker
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
        view = Krita.instance().activeWindow().activeView()
        if not view:
            debug_print("No active view for button action", 1, debug_level=docker.debug_level_value)
            return
        if action_name.startswith("BrushPreset:"):
            preset_name = action_name[len("BrushPreset:"):]
            presets = Krita.instance().resources("preset")
            preset = presets.get(preset_name)
            if preset:
                Krita.instance().writeSetting("", "currentBrushPreset", preset_name)
                view.setCurrentBrushPreset(preset)
                if len(self.recent_presets) >= 2:
                    self.recent_presets.pop(0)
                self.recent_presets.append(preset_name)
                debug_print(f"Switched to brush preset: {preset_name}", 4, debug_level=docker.debug_level_value)
            else:
                debug_print(f"Brush preset '{preset_name}' not found", 1, debug_level=docker.debug_level_value)
        elif action_name == "previous_preset":
            if len(self.recent_presets) >= 2:
                last_preset = self.recent_presets[-2]
                preset = Krita.instance().resources("preset").get(last_preset)
                if preset:
                    Krita.instance().writeSetting("", "currentBrushPreset", last_preset)
                    view.setCurrentBrushPreset(preset)
                    self.recent_presets.pop()
                    self.recent_presets.insert(0, last_preset)
                    debug_print(f"Toggled to previous preset: {last_preset}", 4, debug_level=docker.debug_level_value)
                else:
                    debug_print(f"Previous preset '{last_preset}' not found", 1, debug_level=docker.debug_level_value)
            else:
                debug_print("Not enough recent presets to toggle", 1, debug_level=docker.debug_level_value)
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

            view_key = action_name.split("_")[-1]  # "1", "2", "3"
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
                    hscroll.setValue(x)
                    vscroll.setValue(y)
                    canvas.setZoomLevel(zoom)
                    canvas.setRotation(rotation)
                    debug_print(f"Recalled view {view_key}: x={x}, y={y}, zoom={zoom}, rotation={rotation}", 1, debug_level=docker.debug_level_value)
                else:
                    debug_print(f"No view stored for {view_key}", 1, debug_level=docker.debug_level_value)
        else:
            action = Krita.instance().action(action_name)
            if action:
                action.trigger()
                debug_print(f"Triggered action: {action_name}", 4, debug_level=docker.debug_level_value)
                libspnav.spnav_remove_events(SPNAV_EVENT_MOTION)
            else:
                debug_print(f"Action {action_name} not found", 1, debug_level=docker.debug_level_value)
