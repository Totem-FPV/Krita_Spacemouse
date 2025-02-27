from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QPushButton, QHBoxLayout, QApplication
from PyQt5.QtCore import Qt
from ..utils import debug_print

class LogTab(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.layout.addWidget(self.log_text)

        self.button_layout = QHBoxLayout()
        self.freeze_button = QPushButton("Freeze")
        self.freeze_button.setCheckable(True)
        self.freeze_button.toggled.connect(self.toggle_freeze)
        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self.clear_log)
        self.copy_button = QPushButton("Copy Contents")  # New button
        self.copy_button.clicked.connect(self.copy_log)
        self.button_layout.addWidget(self.freeze_button)
        self.button_layout.addWidget(self.clear_button)
        self.button_layout.addWidget(self.copy_button)
        self.layout.addLayout(self.button_layout)

        self.log_frozen = False
        debug_print("LogTab initialized", 1, debug_level=self.parent.debug_level_value)

    def toggle_freeze(self, checked):
        self.log_frozen = checked
        self.freeze_button.setText("Unfreeze" if checked else "Freeze")
        debug_print(f"Log {'frozen' if checked else 'unfrozen'}", 1, debug_level=self.parent.debug_level_value)

    def clear_log(self):
        self.log_text.clear()
        debug_print("Log cleared", 1, debug_level=self.parent.debug_level_value)

    def append_log(self, message):
        if not self.log_frozen:
            self.log_text.append(message)
            self.log_text.ensureCursorVisible()

    def copy_log(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.log_text.toPlainText())
        debug_print("Log contents copied to clipboard", 1, debug_level=self.parent.debug_level_value)
