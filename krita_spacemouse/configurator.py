# krita_spacemouse/configurator.py
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QComboBox, QLabel, QPushButton, QGridLayout, QInputDialog, QDoubleSpinBox, QSpinBox, QCheckBox, QHBoxLayout, QWidget, QMenu, QLineEdit, QScrollArea
from PyQt5.QtCore import pyqtSlot, Qt, QPoint, QSize, QTimer
from PyQt5.QtGui import QIcon, QPixmap, QColor, QPainter
from .utils import debug_print
from krita import Krita
from .brush_popup import BrushPresetPopup
from .preset_dialog import SavePresetDialog  # New import

class ConfigDialogs:
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.axis_widgets = {}
        self.axis_controls = {}
        self.button_id = None
        self.axis_labels = {}
        self.axis_indicators = {}
        self.axis_colors = {
            "X": "red",
            "Y": "green",
            "Z": "blue",
            "RX": "yellow",
            "RY": "purple",
            "RZ": "orange"
        }
        self.parent.buttons_tab.refresh_available_actions()

    def show_button_config(self, button_id):
        self.button_id = button_id
        dialog = QDialog(self.parent)
        dialog.setWindowTitle("Configure Button")
        layout = QVBoxLayout()
        mapped_actions = self.parent.settings.button_mappings.get(str(button_id), {"None": "None"})
        if isinstance(mapped_actions, str):
            mapped_actions = {"None": mapped_actions}
        label = QLabel(f"Button: {self.parent.buttons_tab.button_labels_map[str(button_id)]} (ID: {button_id})")
        layout.addWidget(label)

        default_layout = QHBoxLayout()
        default_label = QLabel("Default Action:")
        default_action = mapped_actions.get("None", "None")
        default_value = QLabel(default_action)
        default_btn = QPushButton("Select Action")
        default_btn.clicked.connect(lambda: self.select_action(button_id, "None", default_value))
        default_layout.addWidget(default_label)
        default_layout.addWidget(default_value)
        default_layout.addWidget(default_btn)
        layout.addLayout(default_layout)

        for modifier in ["Ctrl", "Alt", "Shift", "Super", "Meta", "Long"]:  # Added "Long"
            mod_layout = QHBoxLayout()
            mod_label = QLabel(f"{modifier}+Action:")
            mod_action = mapped_actions.get(modifier, "None")
            mod_value = QLabel(mod_action)
            mod_btn = QPushButton("Select Action")
            mod_btn.clicked.connect(lambda checked, m=modifier, v=mod_value: self.select_action(button_id, m, v))
            mod_layout.addWidget(mod_label)
            mod_layout.addWidget(mod_value)
            mod_layout.addWidget(mod_btn)
            layout.addLayout(mod_layout)

        dialog.setLayout(layout)
        dialog.exec_()

    def select_action(self, button_id, modifier, value_label):
        action_menu = QMenu(self.parent)
        action_menu.setStyleSheet("QMenu { menu-scrollable: 1; }")

        none_action = action_menu.addAction("None")
        none_action.triggered.connect(lambda checked: self.update_action(button_id, modifier, "None", value_label))
        action_menu.addSeparator()

        self.parent.buttons_tab.refresh_available_actions()
        view_actions = ["store_view_1", "recall_view_1", "store_view_2", "recall_view_2", "store_view_3", "recall_view_3",
                        "lock_rotation", "lock_zoom", "lock_both"]
        modifier_actions = ["Shift", "Ctrl", "Alt", "Super", "Meta"]
        for view_action in view_actions + modifier_actions:
            if view_action not in self.parent.buttons_tab.available_actions:
                self.parent.buttons_tab.available_actions.append(view_action)
        debug_print(f"Populating button config with {len(self.parent.buttons_tab.available_actions)} standard actions", 1, debug_level=self.parent.debug_level_value)

        categories = {
            "Krita": ["krita_", "animation", "blending", "filter", "general", "layer", "painting", "setting", "wg_"],
            "Menu": ["brushes", "edit_", "file_", "filter_", "help_", "image_", "select_", "setting_", "view_", "window_"],
            "Recorder": ["recorder_"],
            "Scripts": ["ai_", "python_", "ten_"],
            "SVG Tools": ["svg_"],
            "Tools": ["tool_", "kis_tool"],
            "View": ["store_view_", "recall_view_", "lock_"],
            "Modifiers": ["Shift", "Ctrl", "Alt", "Super", "Meta"],
            "Other": []
        }
        action_menus = {}
        for cat in categories:
            submenu = action_menu.addMenu(cat)
            submenu.setStyleSheet("QMenu { menu-scrollable: 1; }")
            action_menus[cat] = submenu

        for action_name in self.parent.buttons_tab.available_actions:
            if action_name == "None":
                continue
            qaction = Krita.instance().action(action_name) if not action_name.startswith(("store_view_", "recall_view_", "lock_", "Shift", "Ctrl", "Alt", "Super", "Meta")) else None
            placed = False
            for cat, prefixes in categories.items():
                if cat != "Other" and any(action_name.lower().startswith(prefix.lower()) for prefix in prefixes):
                    menu_action = action_menus[cat].addAction(qaction.icon() if qaction else QIcon(), action_name)
                    menu_action.triggered.connect(lambda checked, a=action_name: self.update_action(button_id, modifier, a, value_label))
                    placed = True
                    break
            if not placed:
                menu_action = action_menus["Other"].addAction(qaction.icon() if qaction else QIcon(), action_name)
                menu_action.triggered.connect(lambda checked, a=action_name: self.update_action(button_id, modifier, a, value_label))

        brush_menu = action_menu.addAction("Brush Presets")
        brush_menu.triggered.connect(lambda: self.show_brush_popup(action_menu))

        action_menu.exec_(QPoint(0, 0))

    def update_action(self, button_id, modifier, action, value_label):
        self.parent.settings.update_button_mapping(button_id, action, modifier)
        value_label.setText(action)

    def show_brush_popup(self, menu):
        resources = Krita.instance().resources("preset")
        popup = BrushPresetPopup(self.parent, resources, self.parent.settings, self.button_id)
        popup.move(menu.pos())
        popup.show()

    def show_puck_config(self):
        dialog = QDialog(self.parent)
        dialog.setWindowTitle("Configure SpaceMouse Axes")
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)

        spnav_axes = ["X", "Y", "Z", "RX", "RY", "RZ"]
        base_actions = ["None"]
        canvas_actions = ["Pan X (Panning Horizontal)", "Pan Y (Panning Vertical)", "Zoom", "Rotation"]

        columns_layout = QHBoxLayout()
        left_column = QVBoxLayout()
        right_column = QVBoxLayout()

        self.timer = QTimer(self.parent)
        self.timer.timeout.connect(self.update_axis_colors)
        self.timer.start(200)
        debug_print("Timer started for axis color updates", 1, debug_level=self.parent.debug_level_value)

        for axis in spnav_axes:
            self.axis_controls[axis] = {
                "sensitivity": None,
                "dead_zone": None,
                "invert": None,
                "layout": None,
                "neg_btn": None,
                "pos_btn": None,
                "neg_label": None,
                "pos_label": None,
                "mode_btn": None
            }

        for i, axis in enumerate(spnav_axes):
            axis_layout = QVBoxLayout()
            axis_layout.setSpacing(5)

            indicator_widget = QWidget()
            indicator_layout = QVBoxLayout(indicator_widget)
            indicator_layout.setContentsMargins(0, 0, 0, 0)
            label = QLabel(f"{axis} Axis:")
            label.setStyleSheet("font-weight: bold; color: black;")
            indicator_layout.addWidget(label)
            self.axis_labels[axis] = label
            self.axis_indicators[axis] = indicator_widget

            action_btn = QPushButton("Canvas Motion")
            action_btn.setToolTip("Select a canvas motion (e.g., Pan, Zoom) or switch to Krita Actions")
            action_menu = QMenu(action_btn)

            for action in base_actions:
                menu_action = action_menu.addAction(action)
                menu_action.triggered.connect(lambda checked, a=action, ax=axis: self.parent.settings.update_puck_mapping(ax, a))

            canvas_menu = action_menu.addMenu("Canvas Motion")
            for action in canvas_actions:
                menu_action = canvas_menu.addAction(action)
                menu_action.triggered.connect(lambda checked, a=action, ax=axis: self.parent.settings.update_puck_mapping(ax, a))

            action_btn.setMenu(action_menu)
            mode_btn = QPushButton("Krita Actions")
            mode_btn.setToolTip("Switch to mapping Krita actions (e.g., Undo, Redo) to this axis")
            mode_btn.clicked.connect(lambda checked, ax=axis, btn=mode_btn: self.toggle_axis_mode(ax, btn))

            settings_container = QWidget()
            settings_layout = QGridLayout()
            settings_container.setLayout(settings_layout)
            self.axis_widgets[axis] = settings_container

            self._update_advanced_settings(axis, self.parent.settings.puck_mappings.get(axis, "None"), settings_layout, action_menu, mode_btn)
            action_menu.triggered.connect(lambda: self._update_advanced_settings(axis, self.parent.settings.puck_mappings.get(axis, "None"), settings_layout, action_menu, mode_btn))

            axis_layout.addWidget(indicator_widget)
            axis_layout.addWidget(QLabel("Map to:"))
            axis_layout.addWidget(action_btn)
            axis_layout.addWidget(mode_btn)
            axis_layout.addWidget(settings_container)

            if i < 3:
                left_column.addLayout(axis_layout)
            else:
                right_column.addLayout(axis_layout)

        columns_layout.addLayout(left_column)
        columns_layout.addLayout(right_column)
        main_layout.addLayout(columns_layout)

        save_btn = QPushButton("Save")
        save_btn.setToolTip("Save all axis settings and close this dialog")
        def save_settings():
            global_dead_zone = self.parent.advanced_tab.dead_zone_slider.value() if hasattr(self.parent, 'advanced_tab') else 130
            for axis, controls in self.axis_controls.items():
                action = self.parent.settings.puck_mappings.get(axis, "None")
                if isinstance(action, dict):
                    if controls["dead_zone"] is not None:
                        if axis not in self.parent.settings.axis_settings:
                            self.parent.settings.axis_settings[axis] = {"dead_zone_offset": 0}
                        self.parent.settings.axis_settings[axis]["dead_zone_offset"] = controls["dead_zone"].value()
                        debug_print(f"Saved {axis} Krita action dead zone offset: {controls['dead_zone'].value()}", 2, debug_level=self.parent.debug_level_value)
                    if controls["sensitivity"] is not None:
                        self.parent.settings.axis_settings[axis]["sensitivity"] = controls["sensitivity"].value()
                        debug_print(f"Saved {axis} Krita action sensitivity: {controls['sensitivity'].value()}", 2, debug_level=self.parent.debug_level_value)
                elif action != "None" and all(controls[key] is not None for key in ["sensitivity", "dead_zone", "invert"]):
                    canvas_axis = action.split()[0]
                    if canvas_axis == "Pan" and "Horizontal" in action:
                        canvas_axis = "X"
                    elif canvas_axis == "Pan" and "Vertical" in action:
                        canvas_axis = "Y"
                    full_axis = f"{canvas_axis} (Panning Horizontal)" if canvas_axis == "X" else f"{canvas_axis} (Panning Vertical)" if canvas_axis == "Y" else canvas_axis
                    self.parent.settings.axis_settings[full_axis]["sensitivity"] = controls["sensitivity"].value()
                    self.parent.settings.axis_settings[full_axis]["dead_zone"] = global_dead_zone + controls["dead_zone"].value()
                    self.parent.settings.axis_settings[full_axis]["invert"] = controls["invert"].isChecked()
                    debug_print(f"Saved {full_axis} motion dead zone: {global_dead_zone + controls['dead_zone'].value()}", 2, debug_level=self.parent.debug_level_value)
            self.parent.settings.save_current_settings()
            self.timer.stop()
            dialog.accept()

        save_btn.clicked.connect(save_settings)
        main_layout.addWidget(save_btn)

        dialog.setLayout(main_layout)
        dialog.setMinimumWidth(600)
        dialog.finished.connect(self.timer.stop)
        dialog.exec_()

    def toggle_axis_mode(self, axis, mode_btn):
        current_action = self.parent.settings.puck_mappings.get(axis, "None")
        is_action_mode = isinstance(current_action, dict)
        if is_action_mode:
            self.parent.settings.update_puck_mapping(axis, "None")
            mode_btn.setText("Krita Actions")
        else:
            self.parent.settings.update_puck_mapping(axis, {"negative": "None", "positive": "None"})
            mode_btn.setText("Canvas Motion")
        self._update_advanced_settings(axis, self.parent.settings.puck_mappings[axis], self.axis_widgets[axis].layout(), self.axis_controls[axis]["action_menu"], mode_btn)

    def update_axis_colors(self):
        if not hasattr(self.parent, 'extension') or not self.parent.extension or not self.parent.extension.last_motion_data:
            debug_print("No extension or motion data available", 1, debug_level=self.parent.debug_level_value)
            return
        motion_data = self.parent.extension.last_motion_data
        debug_print(f"Updating axis colors with motion_data: {motion_data}", 2, debug_level=self.parent.debug_level_value)

        max_axis = None
        max_value = 100
        for axis in self.axis_colors:
            value = abs(motion_data.get(axis.lower(), 0))
            if value > max_value:
                max_value = value
                max_axis = axis

        for axis, indicator in self.axis_indicators.items():
            value = motion_data.get(axis.lower(), 0)
            debug_print(f"Axis {axis}: raw_value={value}", 3, debug_level=self.parent.debug_level_value)
            if max_axis is None or abs(value) <= 100:
                indicator.setStyleSheet("background: transparent;")
            elif axis == max_axis:
                indicator.setStyleSheet(f"background: {self.axis_colors[axis]};")
            else:
                indicator.setStyleSheet(f"background: {self.axis_colors[axis]}; opacity: 0.3;")

    @pyqtSlot(str)
    def _update_advanced_settings(self, axis, action, settings_layout, action_menu, mode_btn):
        for i in reversed(range(settings_layout.count())):
            widget = settings_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        settings_layout.update()

        self.axis_controls[axis]["action_menu"] = action_menu
        self.axis_controls[axis]["mode_btn"] = mode_btn
        global_dead_zone = self.parent.advanced_tab.dead_zone_slider.value() if hasattr(self.parent, 'advanced_tab') else 130
        global_sensitivity = self.parent.advanced_tab.sensitivity_slider.value() / 333.33 if hasattr(self.parent, 'advanced_tab') else 0.3

        if action == "None":
            mode_btn.setText("Krita Actions")
            row = 0
            temp_sensitivity = QDoubleSpinBox()
            temp_sensitivity.setRange(0.1, 3.0)
            temp_sensitivity.setSingleStep(0.05)
            temp_sensitivity.setDecimals(2)
            temp_sensitivity.setValue(self.parent.settings.axis_settings.get(axis, {}).get("sensitivity", 1.0))
            temp_sensitivity.setToolTip(f"Adjust sensitivity relative to global ({global_sensitivity:.2f}); final = {global_sensitivity * temp_sensitivity.value():.2f}")
            temp_sensitivity.valueChanged.connect(lambda v, ax=axis: self._set_axis_setting(ax, "sensitivity", v))
            settings_layout.addWidget(QLabel("Sensitivity Factor:"), row, 0)
            settings_layout.addWidget(temp_sensitivity, row, 1)
            row += 1

            temp_dead_zone = QSpinBox()
            temp_dead_zone.setRange(-130, 370)
            temp_dead_zone.setValue(self.parent.settings.axis_settings.get(axis, {}).get("dead_zone_offset", 0))
            temp_dead_zone.setToolTip(f"Adjust dead zone relative to global ({global_dead_zone}); final = {global_dead_zone + temp_dead_zone.value()}")
            temp_dead_zone.valueChanged.connect(lambda v, ax=axis: self._set_axis_setting(ax, "dead_zone_offset", v))
            settings_layout.addWidget(QLabel("Dead Zone Offset:"), row, 0)
            settings_layout.addWidget(temp_dead_zone, row, 1)

            if axis in self.axis_controls:
                self.axis_controls[axis]["sensitivity"] = temp_sensitivity
                self.axis_controls[axis]["dead_zone"] = temp_dead_zone
                self.axis_controls[axis]["invert"] = None
                self.axis_controls[axis]["layout"] = settings_layout
                self.axis_controls[axis]["neg_btn"] = None
                self.axis_controls[axis]["pos_btn"] = None
                self.axis_controls[axis]["neg_label"] = None
                self.axis_controls[axis]["pos_label"] = None
            return

        if isinstance(action, str) and action in ["Pan X (Panning Horizontal)", "Pan Y (Panning Vertical)", "Zoom", "Rotation"]:
            mode_btn.setText("Krita Actions")
            canvas_axis = action.split()[0]
            if canvas_axis == "Pan" and "Horizontal" in action:
                canvas_axis = "X"
            elif canvas_axis == "Pan" and "Vertical" in action:
                canvas_axis = "Y"
            full_axis = f"{canvas_axis} (Panning Horizontal)" if canvas_axis == "X" else f"{canvas_axis} (Panning Vertical)" if canvas_axis == "Y" else canvas_axis

            row = 0
            temp_sensitivity = QDoubleSpinBox()
            temp_sensitivity.setRange(0.1, 3.0)
            temp_sensitivity.setSingleStep(0.05)
            temp_sensitivity.setDecimals(2)
            temp_sensitivity.setValue(self.parent.settings.axis_settings[full_axis]["sensitivity"])
            temp_sensitivity.setToolTip(f"Adjust sensitivity relative to global ({global_sensitivity:.2f}); final = {global_sensitivity * temp_sensitivity.value():.2f}")
            temp_sensitivity.valueChanged.connect(lambda v, fa=full_axis: self._set_axis_setting(fa, "sensitivity", v))
            settings_layout.addWidget(QLabel(f"{canvas_axis} Sensitivity Factor:"), row, 0)
            settings_layout.addWidget(temp_sensitivity, row, 1)
            row += 1

            temp_dead_zone = QSpinBox()
            temp_dead_zone.setRange(-130, 370)
            offset = self.parent.settings.axis_settings[full_axis]["dead_zone"] - global_dead_zone
            temp_dead_zone.setValue(offset)
            temp_dead_zone.setToolTip(f"Adjust dead zone relative to global ({global_dead_zone}); final = {global_dead_zone + offset}")
            temp_dead_zone.valueChanged.connect(lambda v, fa=full_axis: self._set_axis_setting(fa, "dead_zone", v))
            settings_layout.addWidget(QLabel("Dead Zone Offset:"), row, 0)
            settings_layout.addWidget(temp_dead_zone, row, 1)
            row += 1

            temp_invert = QCheckBox("Invert")
            temp_invert.setChecked(self.parent.settings.axis_settings[full_axis]["invert"])
            temp_invert.setToolTip("Reverses the direction of this motion")
            temp_invert.stateChanged.connect(lambda state, fa=full_axis: self._set_axis_setting(fa, "invert", state == Qt.Checked))
            settings_layout.addWidget(temp_invert, row, 0)

            if axis in self.axis_controls:
                self.axis_controls[axis]["sensitivity"] = temp_sensitivity
                self.axis_controls[axis]["dead_zone"] = temp_dead_zone
                self.axis_controls[axis]["invert"] = temp_invert
                self.axis_controls[axis]["layout"] = settings_layout
                self.axis_controls[axis]["neg_btn"] = None
                self.axis_controls[axis]["pos_btn"] = None
                self.axis_controls[axis]["neg_label"] = None
                self.axis_controls[axis]["pos_label"] = None
        else:  # Krita action
            mode_btn.setText("Canvas Motion")
            row = 0
            mapping = action if isinstance(action, dict) else {"negative": "None", "positive": "None"}
            neg_label = QLabel(f"Negative: {mapping['negative']}")
            pos_label = QLabel(f"Positive: {mapping['positive']}")
            neg_btn = QPushButton("Negative Action")
            pos_btn = QPushButton("Positive Action")
            neg_btn.setToolTip("Action triggered when pushing this axis in the negative direction")
            pos_btn.setToolTip("Action triggered when pushing this axis in the positive direction")

            def create_action_menu(direction, label):
                menu = QMenu(self.parent)
                menu.setStyleSheet("QMenu { menu-scrollable: 1; }")
                none_action = menu.addAction("None")
                none_action.triggered.connect(lambda checked: self.update_puck_action(axis, direction, "None", label))
                menu.addSeparator()
                categories = {
                    "Krita": ["krita_", "animation", "blending", "filter", "general", "layer", "painting", "setting", "wg_"],
                    "Menu": ["brushes", "edit_", "file_", "filter_", "help_", "image_", "select_", "setting_", "view_", "window_"],
                    "Recorder": ["recorder_"],
                    "Scripts": ["ai_", "python_", "ten_"],
                    "SVG Tools": ["svg_"],
                    "Tools": ["tool_", "kis_tool"],
                    "View": ["store_view_", "recall_view_", "lock_", "view_zoom", "zoom_to", "reset_canvas", "mirror", "rotate_canvas", "show"],
                    "Modifiers": ["Shift", "Ctrl", "Alt", "Super", "Meta"],
                    "Edit": ["edit_undo", "edit_redo", "edit_cut", "edit_copy", "edit_paste"],
                    "Selection": ["select_", "deselect", "invert_selection"],
                    "Other": []
                }

                action_menus = {}
                for cat in categories:
                    submenu = menu.addMenu(cat)
                    submenu.setStyleSheet("QMenu { menu-scrollable: 1; }")
                    action_menus[cat] = submenu
                self.parent.buttons_tab.refresh_available_actions()
                view_actions = ["store_view_1", "recall_view_1", "store_view_2", "recall_view_2", "store_view_3", "recall_view_3",
                                "lock_rotation", "lock_zoom", "lock_both"]
                modifier_actions = ["Shift", "Ctrl", "Alt", "Super", "Meta"]
                for action in view_actions + modifier_actions:
                    if action not in self.parent.buttons_tab.available_actions:
                        self.parent.buttons_tab.available_actions.append(action)
                for action_name in self.parent.buttons_tab.available_actions:
                    if action_name == "None":
                        continue
                    qaction = Krita.instance().action(action_name) if not action_name.startswith(("store_view_", "recall_view_", "lock_", "Shift", "Ctrl", "Alt", "Super", "Meta")) else None
                    placed = False
                    for cat, prefixes in categories.items():
                        if cat != "Other" and any(action_name.lower().startswith(prefix.lower()) for prefix in prefixes):
                            menu_action = action_menus[cat].addAction(qaction.icon() if qaction else QIcon(), action_name)
                            menu_action.triggered.connect(lambda checked, a=action_name: self.update_puck_action(axis, direction, a, label))
                            placed = True
                            break
                    if not placed:
                        menu_action = action_menus["Other"].addAction(qaction.icon() if qaction else QIcon(), action_name)
                        menu_action.triggered.connect(lambda checked, a=action_name: self.update_puck_action(axis, direction, a, label))
                return menu

            neg_btn.setMenu(create_action_menu("negative", neg_label))
            pos_btn.setMenu(create_action_menu("positive", pos_label))

            settings_layout.addWidget(neg_label, row, 0)
            settings_layout.addWidget(neg_btn, row, 1)
            row += 1
            settings_layout.addWidget(pos_label, row, 0)
            settings_layout.addWidget(pos_btn, row, 1)
            row += 1

            temp_dead_zone = QSpinBox()
            temp_dead_zone.setRange(-130, 370)
            offset = self.parent.settings.axis_settings.get(axis, {}).get("dead_zone_offset", 0)
            temp_dead_zone.setValue(offset)
            temp_dead_zone.setToolTip(f"Adjust dead zone relative to global ({global_dead_zone}); final = {global_dead_zone + offset}")
            temp_dead_zone.valueChanged.connect(lambda v, ax=axis: self._set_axis_setting(ax, "dead_zone_offset", v))
            settings_layout.addWidget(QLabel("Dead Zone Offset:"), row, 0)
            settings_layout.addWidget(temp_dead_zone, row, 1)
            row += 1

            temp_sensitivity = QDoubleSpinBox()
            temp_sensitivity.setRange(0.1, 3.0)
            temp_sensitivity.setSingleStep(0.05)
            temp_sensitivity.setDecimals(2)
            temp_sensitivity.setValue(self.parent.settings.axis_settings.get(axis, {}).get("sensitivity", 1.0))
            temp_sensitivity.setToolTip(f"Adjust sensitivity relative to global ({global_sensitivity:.2f}); final = {global_sensitivity * temp_sensitivity.value():.2f}")
            temp_sensitivity.valueChanged.connect(lambda v, ax=axis: self._set_axis_setting(ax, "sensitivity", v))
            settings_layout.addWidget(QLabel("Sensitivity Factor:"), row, 0)
            settings_layout.addWidget(temp_sensitivity, row, 1)

            if axis in self.axis_controls:
                self.axis_controls[axis]["sensitivity"] = temp_sensitivity
                self.axis_controls[axis]["dead_zone"] = temp_dead_zone
                self.axis_controls[axis]["invert"] = None
                self.axis_controls[axis]["layout"] = settings_layout
                self.axis_controls[axis]["neg_btn"] = neg_btn
                self.axis_controls[axis]["pos_btn"] = pos_btn
                self.axis_controls[axis]["neg_label"] = neg_label
                self.axis_controls[axis]["pos_label"] = pos_label

    def update_puck_action(self, axis, direction, action, label):
        mapping = self.parent.settings.puck_mappings.get(axis, {"negative": "None", "positive": "None"})
        if not isinstance(mapping, dict):
            mapping = {"negative": "None", "positive": "None"}
        mapping[direction] = action
        self.parent.settings.update_puck_mapping(axis, mapping)
        label.setText(f"{direction.capitalize()}: {action}")

    def _set_axis_setting(self, axis_or_full, key, value):
        if key == "dead_zone_offset" and axis_or_full in ["X", "Y", "Z", "RX", "RY", "RZ"]:
            if axis_or_full not in self.parent.settings.axis_settings:
                self.parent.settings.axis_settings[axis_or_full] = {}
            self.parent.settings.axis_settings[axis_or_full][key] = value
        elif key == "dead_zone":  # Motion mode stores absolute value
            global_dead_zone = self.parent.advanced_tab.dead_zone_slider.value() if hasattr(self.parent, 'advanced_tab') else 130
            self.parent.settings.axis_settings[axis_or_full][key] = global_dead_zone + value
        else:  # Sensitivity, invert
            self.parent.settings.axis_settings[axis_or_full][key] = value
        self.parent.settings.save_current_settings()
