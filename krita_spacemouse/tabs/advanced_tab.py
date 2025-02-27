from PyQt5.QtWidgets import QWidget, QVBoxLayout, QComboBox, QLabel, QSlider
from PyQt5.QtCore import Qt
from ..utils import debug_print  # Fixed from ...utils to ..utils

class AdvancedTab(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.layout = QVBoxLayout()

        self.debug_level = QComboBox()
        self.debug_level.addItems(["0 - None", "1 - Minimal", "2 - Verbose", "3 - Debug", "4 - Full"])
        self.debug_level.currentIndexChanged.connect(self.parent.update_debug_level)
        self.layout.addWidget(QLabel("Debug Logging Level:"))
        self.layout.addWidget(self.debug_level)

        self.polling_slider = QSlider(Qt.Horizontal)
        self.polling_slider.setMinimum(1)
        self.polling_slider.setMaximum(100)
        self.polling_slider.setValue(10)
        self.polling_slider.valueChanged.connect(self.parent.update_polling_rate)
        self.polling_label = QLabel(f"Polling Rate: {self.polling_slider.value()}ms ({1000/self.polling_slider.value():.1f}Hz)")
        self.layout.addWidget(self.polling_label)
        self.layout.addWidget(self.polling_slider)

        self.layout.addStretch()
        self.setLayout(self.layout)
        debug_print("AdvancedTab initialized", 1, debug_level=self.parent.debug_level_value)
