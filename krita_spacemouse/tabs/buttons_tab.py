# buttons_tab.py
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QLabel, QPushButton, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QMessageBox
from PyQt5.QtGui import QPixmap, QMouseEvent, QPen, QColor, QPainter
from PyQt5.QtCore import Qt, QRectF, QEvent
from krita import Krita
from ..utils import debug_print
from ..preset_dialog import SavePresetDialog
from .curves_tab import CurvesTab
import os

class ButtonsTab(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.layout = QVBoxLayout()

        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        plugin_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        image_path = os.path.join(plugin_dir, "images", "spacemouse_enterprise.png")
        self.pixmap = QPixmap(image_path)
        if self.pixmap.isNull():
            debug_print(f"Failed to load {image_path}", 1, debug_level=1, force=True)
            self.pixmap = QPixmap(640, 480)
            self.pixmap.fill(QColor(200, 200, 200))
            painter = QPainter(self.pixmap)
            painter.drawText(10, 240, "Image Missing")
            painter.end()
        else:
            debug_print(f"Loaded {image_path} successfully, Size: {self.pixmap.size()}", 1, debug_level=1, force=True)

        self.scene.clear()
        self.pixmap_item = self.scene.addPixmap(self.pixmap)
        self.pixmap_item.setTransformationMode(Qt.SmoothTransformation)
        self.scene.setSceneRect(0, 0, 640, 480)

        self.base_hotspots = {
            0: QRectF(26, 11, 82, 43), 1: QRectF(109, 11, 79, 43), 2: QRectF(188, 11, 77, 43), 3: QRectF(377, 11, 78, 43),
            4: QRectF(455, 11, 79, 43), 5: QRectF(534, 11, 79, 43), 6: QRectF(26, 54, 82, 51), 7: QRectF(109, 54, 79, 43),
            8: QRectF(188, 54, 77, 43), 9: QRectF(377, 54, 78, 43), 10: QRectF(455, 54, 79, 43), 11: QRectF(534, 54, 79, 51),
            12: QRectF(94, 437, 81, 37), 13: QRectF(468, 437, 81, 37), 14: QRectF(557, 238, 56, 73), 15: QRectF(526, 338, 68, 38),
            16: QRectF(473, 302, 46, 75), 17: QRectF(495, 230, 58, 52), 18: QRectF(22, 117, 106, 51), 19: QRectF(57, 323, 119, 58),
            20: QRectF(26, 230, 56, 93), 21: QRectF(82, 230, 82, 90), 22: QRectF(518, 282, 39, 54), 23: QRectF(128, 109, 99, 53),
            24: QRectF(416, 109, 100, 53), 25: QRectF(22, 176, 125, 55), 26: QRectF(72, 382, 104, 44), 27: QRectF(516, 117, 103, 37),
            28: QRectF(508, 158, 112, 39), 29: QRectF(491, 200, 128, 45), 30: QRectF(465, 382, 104, 44), "puck": QRectF(210, 138, 220, 204)
        }

        self.button_labels_map = {
            "0": "1", "1": "2", "2": "3", "3": "4",
            "4": "5", "5": "6", "6": "7", "7": "8",
            "8": "9", "9": "10", "10": "11", "11": "12",
            "12": "MENU", "13": "FIT", "14": "T", "15": "R",
            "16": "F", "17": "Rotate", "18": "ESC", "19": "Alt",
            "20": "Shift", "21": "Ctrl", "22": "LOCK", "23": "ENTER",
            "24": "DELETE", "25": "TAB", "26": "SPACE",
            "27": "V1", "28": "V2", "29": "V3",
            "30": "ISO1"
        }

        self.overlay_enabled = False
        self.overlay_items = {}
        if self.overlay_enabled and not self.pixmap.isNull():
            debug_print("Starting overlay addition", 1, debug_level=self.parent.debug_level_value)
            for button_id, rect in self.base_hotspots.items():
                item = self.scene.addRect(rect, QPen(QColor(Qt.red), 2))
                self.overlay_items[button_id] = item
                debug_print(f"Added overlay for {button_id} at {rect.x()},{rect.y()}, size {rect.width()}x{rect.height()}", 2, debug_level=self.parent.debug_level_value)
            debug_print("Overlay rectangles added", 1, debug_level=self.parent.debug_level_value)

        self.view.viewport().installEventFilter(self)
        self.layout.addWidget(self.view)

        self.preset_layout = QHBoxLayout()
        preset_label = QLabel("Preset:")
        preset_label.setToolTip("Load or switch between saved button mapping presets")
        self.preset_selector = QComboBox()
        self.preset_selector.setToolTip("Choose a preset to apply its button mappings")
        preset_keys = self.parent.settings.button_presets.keys() if self.parent.settings else ["Default"]
        self.preset_selector.addItems(preset_keys)
        self.preset_selector.setCurrentText("Default")
        self.preset_selector.currentTextChanged.connect(self.load_preset_mappings)
        self.save_preset_btn = QPushButton("Save Preset")
        self.save_preset_btn.setToolTip("Save the current button mappings as a new preset")
        self.save_preset_btn.clicked.connect(self.save_preset)
        self.delete_preset_btn = QPushButton("Delete Preset")
        self.delete_preset_btn.setToolTip("Remove the selected preset (except 'Default')")
        self.delete_preset_btn.clicked.connect(self.delete_preset)
        self.preset_layout.addWidget(preset_label)
        self.preset_layout.addWidget(self.preset_selector)
        self.preset_layout.addWidget(self.save_preset_btn)
        self.preset_layout.addWidget(self.delete_preset_btn)
        self.layout.addLayout(self.preset_layout)

        self.puck_config_btn = QPushButton("Configure Puck")
        self.puck_config_btn.setToolTip("Open settings to map puck axes to motions or actions")
        self.puck_config_btn.clicked.connect(self.show_puck_config_dialog)
        self.layout.addWidget(self.puck_config_btn)

        self.hotspot_toggle = QPushButton("Toggle Hotspot Overlay")
        self.hotspot_toggle.setToolTip("Show/hide red outlines around clickable button areas")
        self.hotspot_toggle.clicked.connect(self.toggle_hotspots)
        self.layout.addWidget(self.hotspot_toggle)

        self.layout.addStretch()
        self.setLayout(self.layout)

        self.refresh_available_actions()
        debug_print(f"Available actions initialized with {len(self.available_actions)} items", 1, debug_level=self.parent.debug_level_value if self.parent.settings else 1)
        debug_print("ButtonsTab initialized", 1, debug_level=self.parent.debug_level_value if self.parent.settings else 1)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if not self.pixmap.isNull():
            view_width = self.view.viewport().width()
            view_height = self.view.viewport().height()
            scale = min(view_width / 640, view_height / 480)
            self.pixmap_item.setScale(scale)
            if self.overlay_enabled:
                for button_id, rect in self.base_hotspots.items():
                    scaled_rect = QRectF(rect.x() * scale, rect.y() * scale, rect.width() * scale, rect.height() * scale)
                    self.overlay_items[button_id].setRect(scaled_rect)
            self.scene.setSceneRect(0, 0, 640 * scale, 480 * scale)

    def eventFilter(self, obj, event):
        if obj == self.view.viewport() and event.type() == QMouseEvent.MouseButtonPress:
            self.button_clicked(event)
            return True
        elif obj == self.view.viewport() and event.type() == QEvent.ToolTip:
            pos = self.view.mapToScene(event.pos())
            view_width = self.view.viewport().width()
            view_height = self.view.viewport().height()
            scale = min(view_width / 640, view_height / 480)
            for button_id, rect in self.base_hotspots.items():
                scaled_rect = QRectF(rect.x() * scale, rect.y() * scale, rect.width() * scale, rect.height() * scale)
                if scaled_rect.contains(pos):
                    if isinstance(button_id, int):
                        btn_id_str = str(button_id)
                        mappings = self.parent.settings.button_mappings.get(btn_id_str, {"None": "None"}) if self.parent.settings else {"None": "None"}
                        tooltip = f"{self.button_labels_map[btn_id_str]}:\n"
                        for mod in ["None", "Shift", "Ctrl", "Alt", "Super", "Meta", "Long"]:  # Added "Long"
                            action = mappings.get(mod, "None")
                            if action != "None":
                                tooltip += f"{mod}: {action}\n"
                    else:
                        tooltip = "Puck Configuration\nClick to map puck axes"
                    self.view.setToolTip(tooltip.strip())
                    break
            else:
                self.view.setToolTip("")
        return super().eventFilter(obj, event)

    def button_clicked(self, event):
        pos = self.view.mapToScene(event.pos())
        view_width = self.view.viewport().width()
        view_height = self.view.viewport().height()
        scale = min(view_width / 640, view_height / 480)
        for button_id, rect in self.base_hotspots.items():
            scaled_rect = QRectF(rect.x() * scale, rect.y() * scale, rect.width() * scale, rect.height() * scale)
            if scaled_rect.contains(pos):
                if isinstance(button_id, int):
                    self.parent.config_dialogs.show_button_config(button_id)
                else:
                    self.parent.config_dialogs.show_puck_config()
                debug_print(f"Clicked {button_id} at {pos} (scaled rect: {scaled_rect.x()},{scaled_rect.y()},{scaled_rect.width()}x{scaled_rect.height()})", 2, debug_level=self.parent.debug_level_value if self.parent.settings else 1)
                break
        else:
            debug_print(f"No hotspot hit at {pos} (viewport: {event.pos()})", 2, debug_level=self.parent.debug_level_value if self.parent.settings else 1)

    def toggle_hotspots(self):
        self.overlay_enabled = not self.overlay_enabled
        if self.overlay_enabled and not self.pixmap.isNull():
            if not self.overlay_items:
                debug_print("Adding hotspot overlays", 1, debug_level=self.parent.debug_level_value if self.parent.settings else 1)
                for button_id, rect in self.base_hotspots.items():
                    item = self.scene.addRect(rect, QPen(QColor(Qt.red), 2))
                    self.overlay_items[button_id] = item
            else:
                for item in self.overlay_items.values():
                    item.show()
            self.resizeEvent(None)
        elif self.overlay_items:
            for item in self.overlay_items.values():
                item.hide()
        debug_print(f"Hotspot overlay {'enabled' if self.overlay_enabled else 'disabled'}", 1, debug_level=self.parent.debug_level_value if self.parent.settings else 1)

    def save_preset(self):
        dialog = SavePresetDialog(self)
        if dialog.exec_():
            name = dialog.get_name()
            if name and self.parent.settings:
                self.parent.settings.save_button_preset_with_name(name)
                self.preset_selector.clear()
                self.preset_selector.addItems(self.parent.settings.button_presets.keys())
                self.preset_selector.setCurrentText(name)
                debug_print(f"Preset saved and selector refreshed: {name}", 1, debug_level=self.parent.debug_level_value)

    def delete_preset(self):
        name = self.preset_selector.currentText()
        if name == "Default":
            QMessageBox.warning(self, "Cannot Delete", "The 'Default' preset cannot be deleted.")
            return
        if self.parent.settings and name in self.parent.settings.button_presets:
            reply = QMessageBox.question(self, "Confirm Delete", f"Are you sure you want to delete preset '{name}'?",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.parent.settings.delete_button_preset_with_name(name)
                self.preset_selector.clear()
                self.preset_selector.addItems(self.parent.settings.button_presets.keys())
                self.preset_selector.setCurrentText("Default")
                debug_print(f"Preset deleted and selector refreshed: {name}", 1, debug_level=self.parent.debug_level_value)

    def load_preset_mappings(self, preset_name):
        if self.parent.settings:
            self.parent.settings.load_button_preset(preset_name)
            debug_print(f"Loaded preset: {preset_name}", 1, debug_level=self.parent.debug_level_value)

    def refresh_available_actions(self):
        self.available_actions = ["None"] + [action.objectName() for action in Krita.instance().actions() if action.objectName()]
        debug_print(f"Refreshed available actions: {len(self.available_actions)} items", 1, debug_level=self.parent.debug_level_value if self.parent.settings else 1)

    def show_puck_config_dialog(self):
        self.parent.config_dialogs.show_puck_config()
