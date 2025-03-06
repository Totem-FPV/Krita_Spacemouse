# tabs/advanced_tab.py
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QComboBox, QLabel, QSlider, QPushButton
from PyQt5.QtCore import Qt
from ..utils import debug_print

class AdvancedTab(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.layout = QVBoxLayout()

        self.debug_level = QComboBox()
        self.debug_level.setToolTip("Set verbosity of debug logs (0 = off, 5 = max)")
        self.debug_level.addItems(["0 - None", "1 - Minimal", "2 - Verbose", "3 - Debug", "4 - Full", "5 - Memory"])
        self.debug_level.currentIndexChanged.connect(self.parent.update_debug_level)
        self.layout.addWidget(QLabel("Debug Logging Level:"))
        self.layout.addWidget(self.debug_level)

        self.polling_slider = QSlider(Qt.Horizontal)
        self.polling_slider.setToolTip("Adjust how often the SpaceMouse is checked (lower = faster, higher = less CPU)")
        self.polling_slider.setMinimum(1)
        self.polling_slider.setMaximum(100)
        self.polling_slider.setValue(10)
        self.polling_slider.valueChanged.connect(self.parent.update_polling_rate)
        self.polling_label = QLabel(f"Polling Rate: {self.polling_slider.value()}ms ({1000/self.polling_slider.value():.1f}Hz)")
        self.layout.addWidget(self.polling_label)
        self.layout.addWidget(self.polling_slider)

        self.dead_zone_slider = QSlider(Qt.Horizontal)
        self.dead_zone_slider.setToolTip("Set base input threshold for all axes; per-axis settings adjust relative to this")
        self.dead_zone_slider.setMinimum(0)
        self.dead_zone_slider.setMaximum(500)
        self.dead_zone_slider.setValue(130)
        self.dead_zone_slider.valueChanged.connect(self.update_global_dead_zone)
        self.dead_zone_label = QLabel(f"Global Dead Zone: {self.dead_zone_slider.value()}")
        self.layout.addWidget(self.dead_zone_label)
        self.layout.addWidget(self.dead_zone_slider)

        self.sensitivity_slider = QSlider(Qt.Horizontal)
        self.sensitivity_slider.setToolTip("Set base sensitivity (100% = max usable speed); per-axis settings multiply this")
        self.sensitivity_slider.setMinimum(0)
        self.sensitivity_slider.setMaximum(200)
        self.sensitivity_slider.setValue(100)
        self.sensitivity_slider.valueChanged.connect(self.update_global_sensitivity)
        self.sensitivity_label = QLabel(f"Global Sensitivity: {self.sensitivity_slider.value()}%")
        self.layout.addWidget(self.sensitivity_label)
        self.layout.addWidget(self.sensitivity_slider)

        self.long_press_slider = QSlider(Qt.Horizontal)
        self.long_press_slider.setToolTip("Set duration for a button press to count as long press")
        self.long_press_slider.setMinimum(100)  # 100ms
        self.long_press_slider.setMaximum(2000)  # 2s
        self.long_press_slider.setValue(500)  # Default 500ms
        self.long_press_slider.valueChanged.connect(self.update_long_press_duration)
        self.long_press_label = QLabel(f"Long Press Duration: {self.long_press_slider.value()}ms")
        self.layout.addWidget(self.long_press_label)
        self.layout.addWidget(self.long_press_slider)

        self.reset_button = QPushButton("Reset to Defaults")
        self.reset_button.setToolTip("Restore polling rate, dead zone, sensitivity, debug level, and long press to defaults")
        self.reset_button.clicked.connect(self.reset_to_defaults)
        self.layout.addWidget(self.reset_button)

        self.layout.addStretch()
        self.setLayout(self.layout)
        debug_level = getattr(self.parent, 'debug_level_value', 1)
        debug_print("AdvancedTab initialized", 1, debug_level=debug_level)

    def update_global_dead_zone(self, value):
        self.dead_zone_label.setText(f"Global Dead Zone: {value}")
        self.parent.save_current_settings()
        debug_print(f"Global dead zone set to {value}", 1, debug_level=self.parent.debug_level_value)

    def update_global_sensitivity(self, value):
        self.sensitivity_label.setText(f"Global Sensitivity: {value}%")
        self.parent.save_current_settings()
        debug_print(f"Global sensitivity set to {value}%", 1, debug_level=self.parent.debug_level_value)

    def update_long_press_duration(self, value):
        self.long_press_label.setText(f"Long Press Duration: {value}ms")
        self.parent.long_press_duration = value  # Store in docker
        self.parent.save_current_settings()
        debug_print(f"Long press duration set to {value}ms", 1, debug_level=self.parent.debug_level_value)

    def reset_to_defaults(self):
        # Set UI elements to default values
        self.polling_slider.setValue(10)
        self.polling_label.setText(f"Polling Rate: 10ms ({1000/10:.1f}Hz)")
        self.dead_zone_slider.setValue(130)
        self.dead_zone_label.setText(f"Global Dead Zone: 130")
        self.sensitivity_slider.setValue(100)
        self.sensitivity_label.setText(f"Global Sensitivity: 100%")
        self.debug_level.setCurrentIndex(1)  # "1 - Minimal"
        self.long_press_slider.setValue(500)
        self.long_press_label.setText(f"Long Press Duration: 500ms")

        # Update extension polling timer
        if hasattr(self.parent, 'extension'):
            self.parent.extension.timer.stop()
            self.parent.extension.timer.start(10)

        # Save the reset settings
        self.parent.save_current_settings()
        debug_print("Advanced settings reset to defaults", 1, debug_level=self.parent.debug_level_value)
