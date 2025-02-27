from PyQt5.QtWidgets import QDialog, QVBoxLayout, QComboBox, QLabel, QPushButton, QGridLayout, QInputDialog, QDoubleSpinBox, QSpinBox, QCheckBox, QHBoxLayout, QWidget, QMenu, QLineEdit, QScrollArea  # Added QWidget
from PyQt5.QtCore import pyqtSlot, Qt, QPoint, QSize, QTimer
from PyQt5.QtGui import QIcon, QPixmap, QColor, QPainter  # Added QPainter for fallback
from .utils import debug_print
from krita import Krita

class SavePresetDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Popup)
        self.setWindowTitle("Save Custom Preset")
        self.layout = QVBoxLayout(self)
        self.name_input = QLineEdit(self)
        self.name_input.setPlaceholderText("Enter preset name")
        self.layout.addWidget(QLabel("Preset Name:"))
        self.layout.addWidget(self.name_input)
        self.save_button = QPushButton("Save", self)
        self.save_button.clicked.connect(self.accept)
        self.cancel_button = QPushButton("Cancel", self)
        self.cancel_button.clicked.connect(self.reject)
        self.layout.addWidget(self.save_button)
        self.layout.addWidget(self.cancel_button)

    def get_name(self):
        return self.name_input.text().strip()

class BrushPresetPopup(QWidget):
    def __init__(self, parent, resources, settings, button_id):
        super().__init__(parent)
        self.setWindowFlags(Qt.Popup)
        self.resources = resources
        self.settings = settings
        self.button_id = button_id
        self.layout = QVBoxLayout(self)

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFixedHeight(400)
        scroll.setFixedWidth(1000)
        self.layout.addWidget(scroll)

        grid_widget = QWidget()
        self.grid = QGridLayout(grid_widget)
        scroll.setWidget(grid_widget)
        self.populate_grid()

    def populate_grid(self):
        row = 0
        col = 0
        for preset_name, preset in self.resources.items():
            preset_name_clean = preset_name.strip()
            pixmap = QPixmap.fromImage(preset.image()) if preset.image() and not preset.image().isNull() else QPixmap(64, 64)
            if pixmap.isNull():
                pixmap.fill(QColor(200, 200, 200))  # Fallback grey square
                painter = QPainter(pixmap)
                painter.drawText(5, 32, "No Img")
                painter.end()
            btn = QPushButton(self)
            btn.setFixedWidth(310)
            btn.setIcon(QIcon(pixmap.scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)))
            btn.setIconSize(QSize(64, 64))
            btn.setText(preset_name_clean)
            btn.setStyleSheet("text-align: left; padding-left: 10px;")
            btn.setLayoutDirection(Qt.LeftToRight)
            btn.clicked.connect(lambda checked, pn=preset_name_clean: self.on_button_clicked(pn))
            self.grid.addWidget(btn, row, col)
            col += 1
            if col >= 3:
                col = 0
                row += 1

    def on_button_clicked(self, preset_name):
        self.settings.update_button_mapping(self.button_id, f"BrushPreset:{preset_name}")
        self.hide()

class ConfigDialogs:
    def __init__(self, parent):
        self.parent = parent
        self.axis_widgets = {}
        self.axis_controls = {}
        self.button_id = None
        self.axis_labels = {}

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

        for modifier in ["Ctrl", "Alt", "Shift"]:
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
        debug_print(f"Populating button config with {len(self.parent.buttons_tab.available_actions)} standard actions", 1, debug_level=self.parent.debug_level_value)

        categories = {
            "Krita": ["krita_", "animation", "blending", "filter", "general", "layer", "painting", "setting", "wg_"],
            "Menu": ["brushes", "edit_", "file_", "filter_", "help_", "image_", "select_", "setting_", "view_", "window_"],
            "Recorder": ["recorder_"],
            "Scripts": ["ai_", "python_", "ten_"],
            "SVG Tools": ["svg_"],
            "Tools": ["tool_", "kis_tool"],
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
            qaction = Krita.instance().action(action_name)
            if qaction:
                placed = False
                for cat, prefixes in categories.items():
                    if cat != "Other" and any(action_name.lower().startswith(prefix.lower()) for prefix in prefixes):
                        menu_action = action_menus[cat].addAction(qaction.icon(), action_name)
                        menu_action.triggered.connect(lambda checked, a=action_name: self.update_action(button_id, modifier, a, value_label))
                        placed = True
                        break
                if not placed:
                    menu_action = action_menus["Other"].addAction(qaction.icon(), action_name)
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
        modifiers = ["None", "Shift", "Ctrl", "Alt"]

        columns_layout = QHBoxLayout()
        left_column = QVBoxLayout()
        right_column = QVBoxLayout()

        self.timer = QTimer(self.parent)
        self.timer.timeout.connect(self.update_axis_colors)
        self.timer.start(100)
        debug_print("Timer started for axis color updates", 1, debug_level=self.parent.debug_level_value)

        for axis in spnav_axes:
            self.axis_controls[axis] = {
                "sensitivity": None,
                "dead_zone": None,
                "invert": None,
                "layout": None
            }

        for i, axis in enumerate(spnav_axes):
            axis_layout = QVBoxLayout()
            axis_layout.setSpacing(5)
            label = QLabel(f"{axis} Axis:")
            label.setStyleSheet("font-weight: bold;")
            self.axis_labels[axis] = label
            action_btn = QPushButton("Select Action")
            action_menu = QMenu(action_btn)

            for action in base_actions:
                menu_action = action_menu.addAction(action)
                menu_action.triggered.connect(lambda checked, a=action, ax=axis: self.parent.settings.update_puck_mapping(ax, a, "action"))

            canvas_menu = action_menu.addMenu("Canvas Motion")
            for action in canvas_actions:
                menu_action = canvas_menu.addAction(action)
                menu_action.triggered.connect(lambda checked, a=action, ax=axis: self.parent.settings.update_puck_mapping(ax, a, "action"))

            action_btn.setMenu(action_menu)
            modifier_combo = QComboBox()
            modifier_combo.addItems(modifiers)
            modifier_combo.setCurrentText(self.parent.settings.puck_modifiers.get(axis, "None"))
            modifier_combo.currentTextChanged.connect(lambda text, a=axis: self.parent.settings.update_puck_mapping(a, text, "modifier"))

            settings_container = QWidget()
            settings_layout = QGridLayout()
            settings_container.setLayout(settings_layout)
            self.axis_widgets[axis] = settings_container

            self._update_advanced_settings(axis, self.parent.settings.puck_mappings.get(axis, "None"), settings_layout)
            action_menu.triggered.connect(lambda: self._update_advanced_settings(axis, self.parent.settings.puck_mappings.get(axis, "None"), settings_layout))

            axis_layout.addWidget(label)
            axis_layout.addWidget(QLabel("Map to:"))
            axis_layout.addWidget(action_btn)
            axis_layout.addWidget(QLabel("With:"))
            axis_layout.addWidget(modifier_combo)
            axis_layout.addWidget(settings_container)

            if i < 3:
                left_column.addLayout(axis_layout)
            else:
                right_column.addLayout(axis_layout)

        columns_layout.addLayout(left_column)
        columns_layout.addLayout(right_column)
        main_layout.addLayout(columns_layout)

        save_btn = QPushButton("Save")
        def save_settings():
            for axis, controls in self.axis_controls.items():
                action = self.parent.settings.puck_mappings.get(axis, "None")
                if action != "None" and all(controls[key] is not None for key in ["sensitivity", "dead_zone", "invert"]):
                    canvas_axis = action.split()[0]
                    if canvas_axis == "Pan" and "Horizontal" in action:
                        canvas_axis = "X"
                    elif canvas_axis == "Pan" and "Vertical" in action:
                        canvas_axis = "Y"
                    full_axis = f"{canvas_axis} (Panning Horizontal)" if canvas_axis == "X" else f"{canvas_axis} (Panning Vertical)" if canvas_axis == "Y" else canvas_axis
                    self.parent.settings.axis_settings[full_axis]["sensitivity"] = controls["sensitivity"].value()
                    self.parent.settings.axis_settings[full_axis]["dead_zone"] = controls["dead_zone"].value()
                    self.parent.settings.axis_settings[full_axis]["invert"] = controls["invert"].isChecked()
            self.parent.settings.save_current_settings()
            self.timer.stop()
            dialog.accept()

        save_btn.clicked.connect(save_settings)
        main_layout.addWidget(save_btn)

        dialog.setLayout(main_layout)
        dialog.setMinimumWidth(600)
        dialog.finished.connect(self.timer.stop)
        dialog.exec_()

    def update_axis_colors(self):
        if not hasattr(self.parent, 'extension') or not self.parent.extension or not self.parent.extension.last_motion_data:
            debug_print("No extension or motion data available", 1, debug_level=self.parent.debug_level_value)
            return
        motion_data = self.parent.extension.last_motion_data
        debug_print(f"Updating axis colors with motion data: {motion_data}", 2, debug_level=self.parent.debug_level_value)
        for axis, label in self.axis_labels.items():
            value = motion_data.get(axis.lower(), 0)
            action = self.parent.settings.puck_mappings.get(axis, "None")
            if action != "None":
                canvas_axis = action.split()[0]
                if canvas_axis == "Pan" and "Horizontal" in action:
                    canvas_axis = "X"
                elif canvas_axis == "Pan" and "Vertical" in action:
                    canvas_axis = "Y"
                full_axis = f"{canvas_axis} (Panning Horizontal)" if canvas_axis == "X" else f"{canvas_axis} (Panning Vertical)" if canvas_axis == "Y" else canvas_axis
                dead_zone = self.parent.settings.axis_settings.get(full_axis, {}).get("dead_zone", 0)
            else:
                dead_zone = 0
            max_input = 500
            intensity = min(abs(value) / (max_input - dead_zone), 1.0) if abs(value) > dead_zone else 0
            if value > 0:
                color = QColor(0, int(255 * intensity), 0)
            elif value < 0:
                color = QColor(int(255 * intensity), 0, 0)
            else:
                color = QColor(0, 0, 0)
            label.setStyleSheet(f"font-weight: bold; color: {color.name()};")

    @pyqtSlot(str)
    def _update_advanced_settings(self, axis, action, settings_layout):
        for i in reversed(range(settings_layout.count())):
            widget = settings_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        settings_layout.update()

        if action == "None":
            return

        canvas_axis = action.split()[0]
        if canvas_axis == "Pan" and "Horizontal" in action:
            canvas_axis = "X"
        elif canvas_axis == "Pan" and "Vertical" in action:
            canvas_axis = "Y"
        full_axis = f"{canvas_axis} (Panning Horizontal)" if canvas_axis == "X" else f"{canvas_axis} (Panning Vertical)" if canvas_axis == "Y" else canvas_axis

        row = 0
        temp_sensitivity = QDoubleSpinBox()
        temp_sensitivity.setRange(0.001, 10.0 if full_axis != "Zoom" else 1.0)
        temp_sensitivity.setSingleStep(0.1 if full_axis != "Zoom" else 0.01)
        temp_sensitivity.setDecimals(2 if full_axis != "Zoom" else 4)
        temp_sensitivity.setValue(self.parent.settings.axis_settings[full_axis]["sensitivity"])
        temp_sensitivity.valueChanged.connect(lambda v, fa=full_axis: self._set_axis_setting(fa, "sensitivity", v))
        settings_layout.addWidget(QLabel(f"{canvas_axis} Sensitivity:"), row, 0)
        settings_layout.addWidget(temp_sensitivity, row, 1)
        row += 1

        temp_dead_zone = QSpinBox()
        temp_dead_zone.setRange(0, 500)
        temp_dead_zone.setValue(self.parent.settings.axis_settings[full_axis]["dead_zone"])
        temp_dead_zone.valueChanged.connect(lambda v, fa=full_axis: self._set_axis_setting(fa, "dead_zone", v))
        settings_layout.addWidget(QLabel("Dead Zone:"), row, 0)
        settings_layout.addWidget(temp_dead_zone, row, 1)
        row += 1

        temp_invert = QCheckBox("Invert")
        temp_invert.setChecked(self.parent.settings.axis_settings[full_axis]["invert"])
        temp_invert.stateChanged.connect(lambda state, fa=full_axis: self._set_axis_setting(fa, "invert", state == Qt.Checked))
        settings_layout.addWidget(temp_invert, row, 0)

        if axis in self.axis_controls:
            self.axis_controls[axis]["sensitivity"] = temp_sensitivity
            self.axis_controls[axis]["dead_zone"] = temp_dead_zone
            self.axis_controls[axis]["invert"] = temp_invert
            self.axis_controls[axis]["layout"] = settings_layout

    def _set_axis_setting(self, full_axis, key, value):
        self.parent.settings.axis_settings[full_axis][key] = value
        self.parent.settings.save_current_settings()
