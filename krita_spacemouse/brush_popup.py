# krita_spacemouse/brush_popup.py
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QGridLayout, QPushButton
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QPixmap, QColor, QPainter
from .utils import debug_print

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
                pixmap.fill(QColor(200, 200, 200))
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
