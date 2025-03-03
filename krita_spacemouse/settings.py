# settings.py
from PyQt5.QtWidgets import QDoubleSpinBox, QSpinBox, QCheckBox, QComboBox, QInputDialog
from PyQt5.QtCore import Qt, QPointF
from .utils import debug_print, load_settings, save_settings

class SettingsManager:
    def __init__(self, parent, load=True):
        debug_print("Starting SettingsManager __init__", 1, debug_level=1)
        self.parent = parent
        self.button_mappings = {}
        self.button_presets = {
            "Default": {
                "0": {"None": "view_zoom_in"}, "1": {"None": "view_zoom_out"}, "2": {"None": "edit_undo"}, "3": {"None": "edit_redo"},
                "4": {"None": "KritaShape/KisToolBrush"}, "5": {"None": "erase_action"}, "6": {"None": "increase_brush_size"},
                "7": {"None": "decrease_brush_size"}, "8": {"None": "previous_preset"}, "9": {"None": "KritaFill/KisToolFill"},
                "10": {"None": "KritaTransform/KisToolMove"}, "11": {"None": "deselect"}, "12": {"None": "toggle_assistant"},
                "13": {"None": "reset_canvas_rotation"}, "14": {"None": "view_show_canvas_only"}, "15": {"None": "mirror_canvas"},
                "16": {"None": "rotate_canvas_left"}, "17": {"None": "rotate_canvas_right"}, "18": {"None": "invert_selection"},
                "19": {"None": "Alt"}, "20": {"None": "Shift"}, "21": {"None": "Ctrl"}, "22": {"None": "lock_both", "Shift": "lock_rotation", "Ctrl": "lock_zoom"},
                "23": {"None": "select_all"}, "24": {"None": "edit_cut"}, "25": {"None": "KisToolSelectRectangular"},
                "26": {"None": "swapForegroundBackground"}, "27": {"None": "recall_view_1", "Shift": "store_view_1"},
                "28": {"None": "recall_view_2", "Shift": "store_view_2"}, "29": {"None": "recall_view_3", "Shift": "store_view_3"},
                "30": {"None": "zoom_to_100pct"}
            }
        }
        self.puck_mappings = {
            "X": "None",
            "Y": "Zoom",
            "Z": "None",
            "RX": "Pan Y (Panning Vertical)",
            "RY": "Rotation",
            "RZ": "Pan X (Panning Horizontal)"
        }
        self.axis_settings = {}
        self.sn_axes = ["X", "Y", "Z", "RX", "RY", "RZ"]
        self.default_mappings = {"X": "RZ", "Y": "RX", "Zoom": "Y", "Rotation": "RY"}

        for canvas_axis in ["X (Panning Horizontal)", "Y (Panning Vertical)", "Zoom", "Rotation"]:
            self.axis_settings[canvas_axis] = {
                "sensitivity": 1.0,
                "dead_zone": 130 if "Panning" in canvas_axis else 50 if canvas_axis == "Zoom" else 150,
                "invert": True,
                "binding": self.default_mappings.get(canvas_axis.split()[0], "RZ")
            }
        for axis in self.sn_axes:
            self.axis_settings[axis] = {"dead_zone_offset": 0, "sensitivity": 1.0}

        if load:
            try:
                self.load_settings()
                debug_print("Settings loaded in __init__", 1, debug_level=1)
            except Exception as e:
                debug_print(f"Error in load_settings during __init__: {e}", 1, debug_level=1)
                raise

        debug_print("SettingsManager __init__ completed", 1, debug_level=1)

    def load_settings(self):
        debug_print("Starting load_settings", 1, debug_level=1)
        settings = load_settings()
        if settings:
            debug_print("Settings loaded from file", 1, debug_level=1)
            try:
                for canvas_axis in ["X (Panning Horizontal)", "Y (Panning Vertical)", "Zoom", "Rotation"]:
                    axis_key = canvas_axis.split()[0].lower()
                    debug_print(f"Loading {canvas_axis} settings", 2, debug_level=1)
                    self.axis_settings[canvas_axis]["sensitivity"] = settings.get(f"{axis_key}_sensitivity", self.axis_settings[canvas_axis]["sensitivity"])
                    self.axis_settings[canvas_axis]["dead_zone"] = settings.get(f"{axis_key}_dead_zone", self.axis_settings[canvas_axis]["dead_zone"])
                    self.axis_settings[canvas_axis]["invert"] = settings.get(f"{axis_key}_invert", True)
                    self.axis_settings[canvas_axis]["binding"] = settings.get(f"{axis_key}_binding", self.default_mappings.get(canvas_axis.split()[0], "RZ"))

                for axis in self.sn_axes:
                    axis_key = axis.lower()
                    if f"{axis_key}_dead_zone_offset" in settings:
                        self.axis_settings[axis]["dead_zone_offset"] = settings[f"{axis_key}_dead_zone_offset"]
                    elif f"{axis_key}_dead_zone" in settings:
                        global_dead_zone = settings.get("global_dead_zone", 130)
                        self.axis_settings[axis]["dead_zone_offset"] = settings[f"{axis_key}_dead_zone"] - global_dead_zone
                    if f"{axis_key}_sensitivity" in settings:
                        self.axis_settings[axis]["sensitivity"] = settings[f"{axis_key}_sensitivity"]

                if hasattr(self.parent, 'advanced_tab'):
                    self.parent.debug_level_value = settings.get("debug_level", 1)
                    self.parent.advanced_tab.debug_level.setCurrentIndex(self.parent.debug_level_value)
                    polling_interval = settings.get("polling_interval", 10)
                    self.parent.advanced_tab.polling_slider.setValue(polling_interval)
                    self.parent.advanced_tab.polling_label.setText(f"Polling Rate: {polling_interval}ms ({1000/polling_interval:.1f}Hz)")
                    global_dead_zone = settings.get("global_dead_zone", 130)
                    self.parent.advanced_tab.dead_zone_slider.setValue(global_dead_zone)
                    self.parent.advanced_tab.dead_zone_label.setText(f"Global Dead Zone: {global_dead_zone}")
                    global_sensitivity = settings.get("global_sensitivity", 100)
                    self.parent.advanced_tab.sensitivity_slider.setValue(global_sensitivity)
                    self.parent.advanced_tab.sensitivity_label.setText(f"Global Sensitivity: {global_sensitivity}%")
                else:
                    self.parent.debug_level_value = settings.get("debug_level", 1)

                loaded_mappings = settings.get("button_mappings", self.button_presets["Default"].copy())
                self.button_mappings = {}
                for btn_id, mapping in loaded_mappings.items():
                    btn_id = str(btn_id)
                    if isinstance(mapping, str):
                        self.button_mappings[btn_id] = {"None": mapping}
                    elif isinstance(mapping, dict):
                        if all(isinstance(v, str) for v in mapping.values()):
                            self.button_mappings[btn_id] = mapping
                        else:
                            self.button_mappings[btn_id] = {"None": "None"}
                            for mod, act in mapping.items():
                                if isinstance(act, str):
                                    self.button_mappings[btn_id][mod] = act
                    else:
                        debug_print(f"Unexpected mapping format for button {btn_id}: {mapping}", 1, debug_level=1)
                        self.button_mappings[btn_id] = {"None": "None"}

                self.button_presets = settings.get("button_presets", self.button_presets)
                loaded_puck_mappings = settings.get("puck_mappings", self.puck_mappings)
                self.puck_mappings = {}
                for axis, mapping in loaded_puck_mappings.items():
                    if isinstance(mapping, str):
                        self.puck_mappings[axis] = mapping
                    elif isinstance(mapping, dict) and "negative" in mapping and "positive" in mapping:
                        self.puck_mappings[axis] = mapping
                    else:
                        self.puck_mappings[axis] = "None"

                if hasattr(self.parent, 'curves_tab'):
                    for axis in ["x", "y", "zoom", "rotation"]:
                        debug_print(f"Loading curve for {axis}", 2, debug_level=self.parent.debug_level_value)
                        curve_points = settings.get(f"{axis}_curve", [[0.0, 0.0], [0.25, 0.25], [0.75, 0.75], [1.0, 1.0]])
                        debug_print(f"Loaded curve points for {axis}: {curve_points}", 2, debug_level=self.parent.debug_level_value)
                        editor = self.parent.curves_tab.curve_editors[axis.capitalize()]
                        for i, (x, y) in enumerate(curve_points):
                            editor.control_points[i] = QPointF(x, y)
                            debug_print(f"Set {axis} point {i}: ({x}, {y})", 3, debug_level=self.parent.debug_level_value)
                        editor.update_curve()
                        debug_print(f"Updated curve for {axis}", 2, debug_level=self.parent.debug_level_value)
                    self.parent.curves_tab.custom_presets = settings.get("custom_presets", {})
                    self.parent.curves_tab.preset_selector.addItems(self.parent.curves_tab.custom_presets.keys())

                debug_print("Settings applied successfully", 1, debug_level=1)
            except Exception as e:
                debug_print(f"Error applying settings: {e}", 1, debug_level=1)
                raise
        else:
            debug_print("No settings file, applying defaults", 1, debug_level=1)
            self.button_mappings = self.button_presets["Default"].copy()
            if hasattr(self.parent, 'advanced_tab'):
                self.parent.debug_level_value = 1
                self.parent.advanced_tab.debug_level.setCurrentIndex(1)
                self.parent.advanced_tab.polling_slider.setValue(10)
                self.parent.advanced_tab.dead_zone_slider.setValue(130)
                self.parent.advanced_tab.sensitivity_slider.setValue(100)
            else:
                self.parent.debug_level_value = 1
        self.load_button_preset("Default")
        debug_print("load_settings completed", 1, debug_level=1)

    def save_current_settings(self):
        debug_print("Saving current settings", 1, debug_level=getattr(self.parent, 'debug_level_value', 1))
        settings = {
            "button_mappings": self.button_mappings,
            "button_presets": self.button_presets,
            "custom_presets": self.parent.curves_tab.custom_presets if hasattr(self.parent, 'curves_tab') else {},
            "puck_mappings": self.puck_mappings,
        }
        if hasattr(self.parent, 'advanced_tab'):
            settings["debug_level"] = self.parent.advanced_tab.debug_level.currentIndex()
            settings["polling_interval"] = self.parent.advanced_tab.polling_slider.value()
            settings["global_dead_zone"] = self.parent.advanced_tab.dead_zone_slider.value()
            settings["global_sensitivity"] = self.parent.advanced_tab.sensitivity_slider.value()
        else:
            settings["debug_level"] = getattr(self.parent, 'debug_level_value', 1)
            settings["polling_interval"] = 10
            settings["global_dead_zone"] = 130
            settings["global_sensitivity"] = 100

        for canvas_axis in ["X (Panning Horizontal)", "Y (Panning Vertical)", "Zoom", "Rotation"]:
            axis_key = canvas_axis.split()[0].lower()
            settings[f"{axis_key}_sensitivity"] = self.axis_settings[canvas_axis]["sensitivity"]
            settings[f"{axis_key}_invert"] = self.axis_settings[canvas_axis]["invert"]
            settings[f"{axis_key}_binding"] = self.axis_settings[canvas_axis]["binding"]
            settings[f"{axis_key}_dead_zone"] = self.axis_settings[canvas_axis]["dead_zone"]
            editor = self.parent.curves_tab.curve_editors[canvas_axis.split()[0]] if hasattr(self.parent, 'curves_tab') else None
            settings[f"{axis_key}_curve"] = [[p.x(), p.y()] for p in editor.control_points] if editor else [[0.0, 0.0], [0.25, 0.25], [0.75, 0.75], [1.0, 1.0]]

        for axis in self.sn_axes:
            if axis in self.axis_settings:
                if "dead_zone_offset" in self.axis_settings[axis]:
                    settings[f"{axis.lower()}_dead_zone_offset"] = self.axis_settings[axis]["dead_zone_offset"]
                if "sensitivity" in self.axis_settings[axis]:
                    settings[f"{axis.lower()}_sensitivity"] = self.axis_settings[axis]["sensitivity"]
        save_settings(settings)
        debug_print("Settings saved", 1, debug_level=getattr(self.parent, 'debug_level_value', 1))

    def update_button_mapping(self, button_id, action, modifier="None"):
        button_id = str(button_id)
        if button_id not in self.button_mappings or not isinstance(self.button_mappings[button_id], dict):
            self.button_mappings[button_id] = {"None": "None"}
        index = self.parent.buttons_tab.available_actions.index(action) if action in self.parent.buttons_tab.available_actions else -1
        if index != -1 or action.startswith("BrushPreset:"):
            self.button_mappings[button_id][modifier] = action
            debug_print(f"Button {button_id} mapped to {modifier}+{action}", 1, debug_level=getattr(self.parent, 'debug_level_value', 1))
        self.save_current_settings()

    def update_puck_mapping(self, axis, value):
        if isinstance(value, str):
            self.puck_mappings[axis] = value
            if value == "None":
                for canvas_axis in ["X (Panning Horizontal)", "Y (Panning Vertical)", "Zoom", "Rotation"]:
                    if self.axis_settings[canvas_axis]["binding"] == axis:
                        self.axis_settings[canvas_axis]["binding"] = "None"
            elif value in ["Pan X (Panning Horizontal)", "Pan Y (Panning Vertical)", "Zoom", "Rotation"]:
                canvas_axis = value.split()[0]
                if canvas_axis == "Pan" and "Horizontal" in value:
                    canvas_axis = "X"
                elif canvas_axis == "Pan" and "Vertical" in value:
                    canvas_axis = "Y"
                full_axis = f"{canvas_axis} (Panning Horizontal)" if canvas_axis == "X" else f"{canvas_axis} (Panning Vertical)" if canvas_axis == "Y" else canvas_axis
                if full_axis in self.axis_settings:
                    for ca in self.axis_settings:
                        if ca != full_axis and self.axis_settings[ca]["binding"] == axis:
                            self.axis_settings[ca]["binding"] = "None"
                    self.axis_settings[full_axis]["binding"] = axis
        elif isinstance(value, dict) and "negative" in value and "positive" in value:
            self.puck_mappings[axis] = value
        else:
            debug_print(f"Invalid puck mapping value for {axis}: {value}", 1, debug_level=getattr(self.parent, 'debug_level_value', 1))
            self.puck_mappings[axis] = "None"
        debug_print(f"Puck {axis} updated to {value}", 1, debug_level=getattr(self.parent, 'debug_level_value', 1))
        self.save_current_settings()

    def save_button_preset(self):
        name, ok = QInputDialog.getText(self.parent, "Save Preset", "Preset Name:")
        if ok and name:
            self.save_button_preset_with_name(name)

    def save_button_preset_with_name(self, name):
        if name == "Default":
            debug_print("Cannot overwrite Default preset", 1, debug_level=getattr(self.parent, 'debug_level_value', 1))
            return
        self.button_presets[name] = self.button_mappings.copy()
        self.save_current_settings()
        debug_print(f"Saved button preset: {name}", 1, debug_level=getattr(self.parent, 'debug_level_value', 1))

    def delete_button_preset(self):
        name = "Default"
        self.delete_button_preset_with_name(name)

    def delete_button_preset_with_name(self, name):
        if name == "Default":
            debug_print("Cannot delete Default preset", 1, debug_level=getattr(self.parent, 'debug_level_value', 1))
            return
        if name in self.button_presets:
            del self.button_presets[name]
            self.load_button_preset("Default")
            self.save_current_settings()
            debug_print(f"Deleted button preset: {name}", 1, debug_level=getattr(self.parent, 'debug_level_value', 1))

    def load_button_preset(self, name):
        if name in self.button_presets:
            self.button_mappings = self.button_presets[name].copy()
            debug_print(f"Loaded button preset: {name}", 1, debug_level=getattr(self.parent, 'debug_level_value', 1))
