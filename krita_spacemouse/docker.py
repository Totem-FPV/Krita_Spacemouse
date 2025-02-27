from PyQt5.QtWidgets import QDockWidget, QWidget, QVBoxLayout, QTabWidget
from krita import Krita
from .tabs.curves_tab import CurvesTab
from .tabs.buttons_tab import ButtonsTab
from .tabs.advanced_tab import AdvancedTab
from .tabs.log_tab import LogTab
from .configurator import ConfigDialogs  # Changed from config_dialogs
from .settings import SettingsManager
from .utils import debug_print

class SpacenavDocker(QDockWidget):
    def __init__(self):
        super().__init__()
        print("[PRE-INIT 1] Starting SpacenavDocker __init__")
        debug_print("Step 1: Starting SpacenavDocker __init__", 1, debug_level=1)
        self.setObjectName("spacenavDocker")
        self.setWindowTitle("Spacemouse Controls")
        self.widget = QWidget()
        self.setWidget(self.widget)
        self.layout = QVBoxLayout()
        self.widget.setLayout(self.layout)

        print("[PRE-INIT 2] debug_level_value set")
        debug_print("Step 2: debug_level_value set", 1, debug_level=1)

        try:
            self.settings = SettingsManager(self)
            debug_print("Step 3: SettingsManager initialized successfully", 1, debug_level=1)
        except Exception as e:
            debug_print(f"Step 3: Failed to initialize SettingsManager: {str(e)}", 1, debug_level=1)
            import traceback
            debug_print(f"Stack trace: {traceback.format_exc()}", 1, debug_level=1)
            self.settings = None

        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)
        print("[PRE-INIT 4] Tabs widget added")
        debug_print("Step 4: Tabs widget added", 1, debug_level=1)

        self.axis_settings_container = QWidget(self)
        self.axis_settings_container.setLayout(QVBoxLayout())
        self.axis_settings_container.setVisible(False)

        self.curves_tab = CurvesTab(self)
        debug_print("Step 5: CurvesTab initialized", 1, debug_level=1)
        print("[PRE-INIT 5] Before ButtonsTab")
        self.buttons_tab = ButtonsTab(self)
        debug_print("Step 6: ButtonsTab initialized", 1, debug_level=1)
        self.advanced_tab = AdvancedTab(self)
        debug_print("Step 7: AdvancedTab initialized", 1, debug_level=1)
        self.log_tab = LogTab(self)
        print("[PRE-INIT 6] LogTab initialized")
        debug_print("Step 8: LogTab initialized", 1, debug_level=1)

        self.config_dialogs = ConfigDialogs(self)
        debug_print("Step 9: ConfigDialogs initialized", 1, debug_level=1)

        self.tabs.addTab(self.curves_tab, "Curves")
        self.tabs.addTab(self.buttons_tab, "Buttons")
        self.tabs.addTab(self.advanced_tab, "Advanced")
        self.tabs.addTab(self.log_tab, "Log")
        debug_print("Step 10: Tabs added to QTabWidget", 1, debug_level=1)

        if self.settings:
            self.settings.load_settings()
            if not hasattr(self, 'debug_level_value'):  # Set default only if not loaded
                self.debug_level_value = 1
            debug_print("Settings loaded after initialization", 1, debug_level=self.debug_level_value)

        debug_print("Step 11: SpacenavDocker initialized", 1, debug_level=self.debug_level_value if self.settings else 1)
        print("[PRE-INIT 7] SpacenavDocker initialized")

    def button_clicked(self, event):
        pos = event.pos()
        for button_id, rect in self.buttons_tab.button_hotspots.items():
            if rect.contains(pos):
                if isinstance(button_id, int):
                    self.config_dialogs.show_button_config(button_id)
                else:
                    self.config_dialogs.show_puck_config()
                break

    def update_debug_level(self, index):
        old_level = self.debug_level_value
        self.debug_level_value = index
        debug_print(f"Debug level set to {self.advanced_tab.debug_level.currentText()}", 1, debug_level=old_level)
        if not hasattr(self, 'settings'):
            debug_print("self.settings not defined", 1, debug_level=old_level)
        elif self.settings is None:
            debug_print("self.settings is None", 1, debug_level=old_level)
        else:
            self.settings.save_current_settings()

    def update_polling_rate(self, value):
        if hasattr(self, 'extension'):
            self.extension.timer.stop()
            self.extension.timer.start(value)
            self.advanced_tab.polling_label.setText(f"Polling Rate: {value}ms ({1000/value:.1f}Hz)")
            debug_print(f"Polling rate set to {value}ms ({1000/value:.1f}Hz)", 1, debug_level=self.debug_level_value)
        if not hasattr(self, 'settings'):
            debug_print("self.settings not defined", 1, debug_level=self.debug_level_value)
        elif self.settings is None:
            debug_print("self.settings is None", 1, debug_level=self.debug_level_value)
        else:
            self.settings.save_current_settings()

    def save_current_settings(self):
        if not hasattr(self, 'settings'):
            debug_print("self.settings not defined", 1, debug_level=self.debug_level_value)
        elif self.settings is None:
            debug_print("self.settings is None", 1, debug_level=self.debug_level_value)
        else:
            self.settings.save_current_settings()

    def canvasChanged(self, canvas):
        pass

    def set_extension(self, extension):
        self.extension = extension
        debug_print("Extension linked to docker", 1, debug_level=self.debug_level_value)
