import sys
import os
import psutil
import pyqtgraph as pg
from datetime import datetime
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QMessageBox
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QTimer, Qt

# Import all modules from our new structure
from language_loader import load_language
from ui_manager import UIManager
from process_data_handler import ProcessDataHandler
from system_monitor import SystemMonitor
from network_monitor import NetworkMonitor
from graph_handler import GraphHandler
from process_actions import ProcessActions
from inspect_handler import InspectHandler
from startup_programs_handler import StartupProgramsHandler
# Note: You don't need to import startup_linux or startup_windows here,
# as startup_programs_handler handles the import logic.

class ProcessManager(QWidget, UIManager, ProcessDataHandler, SystemMonitor, NetworkMonitor, GraphHandler, ProcessActions, InspectHandler, StartupProgramsHandler):
    def __init__(self):
        super().__init__()
        
        # Set window icon
        icon_path_system = '/usr/share/icons/hicolor/256x256/apps/hel-process.png'
        local_icon_path = os.path.join("logo", "icon.png")
        if os.path.exists(icon_path_system):
            self.setWindowIcon(QIcon(icon_path_system))
        elif os.path.exists(local_icon_path):
            self.setWindowIcon(QIcon(local_icon_path))

        # Language initialization
        self.lang_code = 'en'
        try:
            self.lang = load_language(self.lang_code)
        except FileNotFoundError as e:
            QMessageBox.critical(self, "Error", str(e) + "\n" + "Ensure 'lang' folder exists with 'en.py' inside.")
            sys.exit(1)

        self.setWindowTitle(self.lang['title'])
        self.resize(1400, 800)

        # Initialize monitoring counters
        self.last_net_bytes_sent = 0
        self.last_net_bytes_recv = 0
        self.last_disk_read_bytes = 0
        self.last_disk_write_bytes = 0

        # Call methods from imported classes
        self.init_ui()
        self.init_graphs()
        self.update_processes()
        self.update_system_info()
        self.update_network_activity()
        self.update_disk_io_graph()
        self.update_startup_programs()
        self.update_texts()

    def change_language(self):
        self.lang_code = self.lang_selector.currentData()
        try:
            self.lang = load_language(self.lang_code)
        except FileNotFoundError as e:
            QMessageBox.critical(self, "Error", str(e) + "\n" + "Language file missing. Fallbacking to English.")
            self.lang_code = 'en'
            self.lang_selector.setCurrentIndex(self.lang_selector.findData('en'))
            self.lang = load_language('en')
        self.update_texts()
        self.update_processes()
        self.update_startup_programs()
