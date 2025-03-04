# krita_spacemouse/preset_dialog.py
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QLabel, QPushButton
from PyQt5.QtCore import Qt

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
