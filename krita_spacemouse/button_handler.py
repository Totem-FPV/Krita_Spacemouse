from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMdiArea, QAbstractScrollArea, QApplication
from krita import Krita
from .utils import debug_print
import time

def process_button_event(self, button_id, press_state):
    docker = self.docker
    debug_print(f"Button event - ID={button_id}, Press={press_state}", 1, debug_level=docker.debug_level_value)
    mappings = docker.settings.button_mappings.get(str(button_id), {"None": "None"})
    if isinstance(mappings, str):
        mappings = {"None": mappings}
    modifier_key = ("Ctrl" if self.modifier_states["Ctrl"] else
                   "Alt" if self.modifier_states["Alt"] else
                   "Shift" if self.modifier_states["Shift"] else "None")
    action_name = mappings.get(modifier_key, mappings.get("None", "None"))
    debug_print(f"Action mapped: {modifier_key}+{action_name}", 1, debug_level=docker.debug_level_value)

    if action_name in ["Shift", "Ctrl", "Alt"]:
        self.modifier_states[action_name] = press_state
        debug_print(f"Modifier {action_name} {'set' if press_state else 'cleared'}", 4, debug_level=docker.debug_level_value)
    elif press_state and action_name != "None":
        view = Krita.instance().activeWindow().activeView()
        if not view:
            debug_print("No active view for button action", 1, debug_level=docker.debug_level_value)
            return
        if action_name.startswith("BrushPreset:"):
            # [Unchanged BrushPreset logic]
            pass
        elif action_name == "previous_preset":
            # [Unchanged previous_preset logic]
            pass
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
            ZOOM_SCALE_FACTOR = 4.17  # From Scripter tests
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
                    canvas.setZoomLevel(zoom / ZOOM_SCALE_FACTOR)  # Adjust for Krita’s scaling
                    QApplication.processEvents()
                    canvas.setRotation(rotation)
                    hscroll.setValue(x)
                    vscroll.setValue(y)
                    QApplication.processEvents()
                    debug_print(f"Recalled view {view_key}: x={x}, y={y}, zoom={zoom}, rotation={rotation}", 1, debug_level=docker.debug_level_value)
                    debug_print(f"Final state: x={hscroll.value()}, y={vscroll.value()}, zoom={canvas.zoomLevel()}, rotation={canvas.rotation()}", 3, debug_level=docker.debug_level_value)
                else:
                    debug_print(f"No view stored for {view_key}", 1, debug_level=docker.debug_level_value)
        else:
            action = Krita.instance().action(action_name)
            if action:
                action.trigger()
                debug_print(f"Triggered action: {action_name}", 4, debug_level=docker.debug_level_value)
            else:
                debug_print(f"Action {action_name} not found", 1, debug_level=docker.debug_level_value)
