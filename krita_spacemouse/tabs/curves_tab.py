from PyQt5.QtWidgets import QWidget, QVBoxLayout, QComboBox, QLabel, QHBoxLayout, QPushButton
from PyQt5.QtCore import QPointF
from ..curves import BezierCurveEditor
from ..configurator import SavePresetDialog  # Changed from config_dialogs
from ..utils import debug_print

class CurvesTab(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.stock_presets = {
            "Linear": [[0.0, 0.0], [0.33, 0.33], [0.67, 0.67], [1.0, 1.0]],
            "Ease-In": [[0.0, 0.0], [0.42, 0.0], [1.0, 1.0], [1.0, 1.0]],
            "Ease-Out": [[0.0, 0.0], [0.0, 0.0], [0.58, 1.0], [1.0, 1.0]],
            "Ease-In-Out": [[0.0, 0.0], [0.42, 0.0], [0.58, 1.0], [1.0, 1.0]],
            "Steep": [[0.0, 0.0], [0.1, 0.1], [0.9, 0.9], [1.0, 1.0]]
        }
        self.custom_presets = {}

        self.curve_selector = QComboBox()
        self.curve_selector.addItems(["X", "Y", "Zoom", "Rotation"])
        self.curve_selector.currentTextChanged.connect(self.switch_curve)
        self.layout.addWidget(QLabel("Select Axis:"))
        self.layout.addWidget(self.curve_selector)

        self.preset_selector = QComboBox()
        self.preset_selector.addItem("Custom (Current)")
        self.preset_selector.addItems(self.stock_presets.keys())
        self.preset_selector.currentTextChanged.connect(self.apply_preset)
        self.layout.addWidget(QLabel("Preset:"))
        self.layout.addWidget(self.preset_selector)

        self.preset_buttons_layout = QHBoxLayout()
        self.save_preset_button = QPushButton("Save Preset")
        self.save_preset_button.clicked.connect(self.save_custom_preset)
        self.delete_preset_button = QPushButton("Delete Preset")
        self.delete_preset_button.clicked.connect(self.delete_custom_preset)
        self.preset_buttons_layout.addWidget(self.save_preset_button)
        self.preset_buttons_layout.addWidget(self.delete_preset_button)
        self.layout.addLayout(self.preset_buttons_layout)

        self.curve_editors = {
            "X": BezierCurveEditor(),
            "Y": BezierCurveEditor(),
            "Zoom": BezierCurveEditor(),
            "Rotation": BezierCurveEditor()
        }
        for editor in self.curve_editors.values():
            editor.parent_widget = self.parent
        self.current_curve_editor = self.curve_editors["X"]
        self.layout.addWidget(self.current_curve_editor)
        self.layout.addStretch()

    def switch_curve(self, axis):
        self.layout.removeWidget(self.current_curve_editor)
        self.current_curve_editor.hide()
        self.current_curve_editor = self.curve_editors[axis]
        self.layout.insertWidget(4, self.current_curve_editor)
        self.current_curve_editor.show()
        self.preset_selector.setCurrentText("Custom (Current)")

    def apply_preset(self, preset_name):
        if preset_name == "Custom (Current)":
            return
        if preset_name in self.stock_presets:
            points = self.stock_presets[preset_name]
        elif preset_name in self.custom_presets:
            points = self.custom_presets[preset_name]
        else:
            debug_print(f"Preset '{preset_name}' not found", 1, debug_level=self.parent.debug_level_value)
            return
        for i, (x, y) in enumerate(points):
            self.current_curve_editor.control_points[i] = QPointF(x, y)
        self.current_curve_editor.update_curve()
        self.parent.save_current_settings()
        debug_print(f"Applied preset '{preset_name}' to {self.curve_selector.currentText()} axis", 1, debug_level=self.parent.debug_level_value)

    def save_custom_preset(self):
        dialog = SavePresetDialog(self)
        if dialog.exec_():
            name = dialog.get_name()
            if name:
                if name in self.stock_presets:
                    debug_print(f"Cannot overwrite stock preset '{name}'", 1, debug_level=self.parent.debug_level_value)
                    return
                current_points = [[p.x(), p.y()] for p in self.current_curve_editor.control_points]
                self.custom_presets[name] = current_points
                if name not in [self.preset_selector.itemText(i) for i in range(self.preset_selector.count())]:
                    self.preset_selector.addItem(name)
                self.preset_selector.setCurrentText(name)
                self.parent.save_current_settings()
                debug_print(f"Saved custom preset '{name}'", 1, debug_level=self.parent.debug_level_value)

    def delete_custom_preset(self):
        preset_name = self.preset_selector.currentText()
        if preset_name == "Custom (Current)" or preset_name in self.stock_presets:
            debug_print(f"Cannot delete '{preset_name}'", 1, debug_level=self.parent.debug_level_value)
            return
        if preset_name in self.custom_presets:
            del self.custom_presets[preset_name]
            self.preset_selector.removeItem(self.preset_selector.findText(preset_name))
            self.preset_selector.setCurrentText("Custom (Current)")
            self.parent.save_current_settings()
            debug_print(f"Deleted custom preset '{preset_name}'", 1, debug_level=self.parent.debug_level_value)

    def update_curve(self):
        t = np.linspace(0, 1, 100)
        x = [cubic_bezier(ti, self.control_points[0].x(), self.control_points[1].x(),
                          self.control_points[2].x(), self.control_points[3].x()) for ti in t]
        y = [cubic_bezier(ti, self.control_points[0].y(), self.control_points[1].y(),
                          self.control_points[2].y(), self.control_points[3].y()) for ti in t]
        self.curve.setData(x, y)
        self.control_lines.setData(
            [p.x() for p in self.control_points],
            [p.y() for p in self.control_points]
        )
        for i, item in enumerate(self.control_points_items):
            item.setData([self.control_points[i].x()], [self.control_points[i].y()])
        self.plot.update()  # Force UI refresh
