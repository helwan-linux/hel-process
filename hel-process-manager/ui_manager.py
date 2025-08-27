from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QLineEdit, QComboBox, QMessageBox, QTabWidget, QTextEdit, QInputDialog,
    QMenu, QAction, QHeaderView, QListWidget, QDialog, QCheckBox, QGridLayout
)
from PyQt5.QtCore import Qt
import pyqtgraph as pg

class UIManager:
    def init_ui(self):
        self.layout = QVBoxLayout(self)
        self.setLayout(self.layout)

        # Top layout for language selector and search bar
        top_layout = QHBoxLayout()
        top_layout.addWidget(QLabel(self.lang['language']))
        self.lang_selector = QComboBox()
        self.lang_selector.addItem("English", "en")
        self.lang_selector.addItem("العربية", "ar")
        self.lang_selector.addItem("Español", "es")
        self.lang_selector.addItem("Português", "pt")
        self.lang_selector.addItem("Français", "fr")
        self.lang_selector.addItem("Deutsch", "de")
        self.lang_selector.addItem("Italiano", "it")
        self.lang_selector.addItem("Türkçe", "tr")
        self.lang_selector.addItem("中文", "zh")
        self.lang_selector.setCurrentText(self.lang_code)
        self.lang_selector.currentIndexChanged.connect(self.change_language)
        top_layout.addWidget(self.lang_selector)

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText(self.lang['search'])
        self.search_bar.textChanged.connect(self.update_processes)
        top_layout.addWidget(self.search_bar)
        self.layout.addLayout(top_layout)

        # Main tab widget
        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)
        
        # --- Performance Tab ---
        self.graph_widget = pg.GraphicsLayoutWidget()
        self.cpu_plot = self.graph_widget.addPlot()
        self.cpu_curve = self.cpu_plot.plot(pen='y')
        self.cpu_data = []

        self.graph_widget.nextRow()
        self.ram_plot = self.graph_widget.addPlot()
        self.ram_curve = self.ram_plot.plot(pen='c')
        self.ram_data = []

        self.graph_widget.nextRow()
        self.disk_read_plot = self.graph_widget.addPlot()
        self.disk_read_curve = self.disk_read_plot.plot(pen='m')
        self.disk_read_data = []

        self.graph_widget.nextRow()
        self.disk_write_plot = self.graph_widget.addPlot()
        self.disk_write_curve = self.disk_write_plot.plot(pen='w')
        self.disk_write_data = []

        self.tabs.addTab(self.graph_widget, self.lang['tab_performance'])

        # --- Processes Tab ---
        self.process_tab = QWidget()
        self.process_layout = QVBoxLayout(self.process_tab)
        self.table = QTableWidget()
        self.table.setColumnCount(10)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.horizontalHeader().sectionClicked.connect(self.sort_processes_table)
        self.process_layout.addWidget(self.table)

        btns_layout = QHBoxLayout()
        self.refresh_btn = QPushButton(self.lang['refresh'])
        self.refresh_btn.clicked.connect(self.update_processes)
        btns_layout.addWidget(self.refresh_btn)

        self.kill_btn = QPushButton(self.lang['kill'])
        self.kill_btn.clicked.connect(self.kill_selected_process)
        btns_layout.addWidget(self.kill_btn)

        self.renice_btn = QPushButton(self.lang.get('renice', "Renice"))
        self.renice_btn.clicked.connect(self.renice_process)
        btns_layout.addWidget(self.renice_btn)

        self.inspect_btn = QPushButton(self.lang.get('inspect', "Inspect"))
        self.inspect_btn.clicked.connect(self.inspect_process)
        btns_layout.addWidget(self.inspect_btn)

        self.suspend_btn = QPushButton(self.lang.get('suspend_process', "Suspend"))
        self.suspend_btn.clicked.connect(self.suspend_selected_process)
        btns_layout.addWidget(self.suspend_btn)

        self.resume_btn = QPushButton(self.lang.get('resume_process', "Resume"))
        self.resume_btn.clicked.connect(self.resume_selected_process)
        btns_layout.addWidget(self.resume_btn)

        self.set_cpu_affinity_btn = QPushButton(self.lang.get('set_cpu_affinity', "Set CPU Affinity"))
        self.set_cpu_affinity_btn.clicked.connect(self.set_cpu_affinity)
        btns_layout.addWidget(self.set_cpu_affinity_btn)

        self.set_io_priority_btn = QPushButton(self.lang.get('set_io_priority', "Set I/O Priority"))
        self.set_io_priority_btn.clicked.connect(self.set_io_priority)
        btns_layout.addWidget(self.set_io_priority_btn)

        self.open_file_location_btn = QPushButton(self.lang.get('open_file_location', "Open File Location"))
        self.open_file_location_btn.clicked.connect(self.open_process_file_location)
        btns_layout.addWidget(self.open_file_location_btn)

        self.process_layout.addLayout(btns_layout)
        self.tabs.addTab(self.process_tab, self.lang['tab_processes'])

        # --- System Info Tab ---
        self.sys_tab = QWidget()
        self.sys_layout = QVBoxLayout(self.sys_tab)
        self.sys_info = QTextEdit()
        self.sys_info.setReadOnly(True)
        self.sys_layout.addWidget(self.sys_info)
        self.disk_info = QTextEdit()
        self.disk_info.setReadOnly(True)
        self.sys_layout.addWidget(self.disk_info)
        self.tabs.addTab(self.sys_tab, self.lang['tab_system_info'])

        # --- Network Connections & Sensors Tab ---
        self.net_tab = QWidget()
        self.net_layout = QVBoxLayout(self.net_tab)
        self.net_info = QTextEdit()
        self.net_info.setReadOnly(True)
        self.net_layout.addWidget(self.net_info)
        self.tabs.addTab(self.net_tab, self.lang['tab_network_sensors'])

        # --- Network Monitor Tab ---
        self.network_monitor_tab = QWidget()
        self.network_monitor_layout = QVBoxLayout(self.network_monitor_tab)
        self.network_graph = pg.GraphicsLayoutWidget()
        self.upload_plot = self.network_graph.addPlot()
        self.upload_curve = self.upload_plot.plot(pen='r')
        self.upload_data = []

        self.network_graph.nextRow()
        self.download_plot = self.network_graph.addPlot()
        self.download_curve = self.download_plot.plot(pen='g')
        self.download_data = []

        self.network_monitor_layout.addWidget(self.network_graph)
        self.interface_info = QTextEdit()
        self.interface_info.setReadOnly(True)
        self.network_monitor_layout.addWidget(self.interface_info)
        self.tabs.addTab(self.network_monitor_tab, self.lang['tab_network_monitor'])

        # --- Startup Programs Tab ---
        self.startup_tab = QWidget()
        self.startup_layout = QVBoxLayout(self.startup_tab)
        self.startup_list = QListWidget()
        self.startup_layout.addWidget(self.startup_list)

        startup_btns_layout = QHBoxLayout()
        self.refresh_startup_btn = QPushButton(self.lang.get('refresh_startup', "Refresh Startup Programs"))
        self.refresh_startup_btn.clicked.connect(self.update_startup_programs)
        startup_btns_layout.addWidget(self.refresh_startup_btn)

        self.disable_startup_btn = QPushButton(self.lang.get('disable_startup', "Disable Selected"))
        self.disable_startup_btn.clicked.connect(lambda: self.set_startup_status(False))
        startup_btns_layout.addWidget(self.disable_startup_btn)

        self.enable_startup_btn = QPushButton(self.lang.get('enable_startup', "Enable Selected"))
        self.enable_startup_btn.clicked.connect(lambda: self.set_startup_status(True))
        startup_btns_layout.addWidget(self.enable_startup_btn)

        self.startup_layout.addLayout(startup_btns_layout)
        self.tabs.addTab(self.startup_tab, self.lang.get('tab_startup_programs', "Startup Programs"))

        # --- About Tab ---
        self.about_tab = QWidget()
        self.about_layout = QVBoxLayout(self.about_tab)
        self.about_text = QTextEdit()
        self.about_text.setReadOnly(True)
        self.about_layout.addWidget(self.about_text)
        self.tabs.addTab(self.about_tab, self.lang['tab_about'])

        # --- Status Bar ---
        self.status_bar = QLabel("Ready.")
        self.status_bar.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.layout.addWidget(self.status_bar)

    def update_texts(self):
        self.setWindowTitle(self.lang['title'])
        self.search_bar.setPlaceholderText(self.lang['search'])
        self.refresh_btn.setText(self.lang['refresh'])
        self.kill_btn.setText(self.lang['kill'])
        self.inspect_btn.setText(self.lang.get('inspect', "Inspect"))
        self.renice_btn.setText(self.lang.get('renice', "Renice"))
        self.suspend_btn.setText(self.lang.get('suspend_process', "Suspend"))
        self.resume_btn.setText(self.lang.get('resume_process', "Resume"))
        self.set_cpu_affinity_btn.setText(self.lang.get('set_cpu_affinity', "Set CPU Affinity"))
        self.set_io_priority_btn.setText(self.lang.get('set_io_priority', "Set I/O Priority"))
        self.open_file_location_btn.setText(self.lang.get('open_file_location', "Open File Location"))

        self.table.setHorizontalHeaderLabels(self.lang['columns_process_table'])

        self.tabs.setTabText(0, self.lang['tab_performance'])
        self.tabs.setTabText(1, self.lang['tab_processes'])
        self.tabs.setTabText(2, self.lang['tab_system_info'])
        self.tabs.setTabText(3, self.lang['tab_network_sensors'])
        self.tabs.setTabText(4, self.lang['tab_network_monitor'])
        self.tabs.setTabText(5, self.lang.get('tab_startup_programs', "Startup Programs"))
        self.tabs.setTabText(6, self.lang['tab_about'])

        self.cpu_plot.setTitle(self.lang.get('cpu_graph_title', "CPU Usage (%)"))
        self.ram_plot.setTitle(self.lang.get('ram_graph_title', "RAM Usage (%)"))
        self.disk_read_plot.setTitle(self.lang.get('disk_read_graph_title', "Disk Read (KB/s)"))
        self.disk_write_plot.setTitle(self.lang.get('disk_write_graph_title', "Disk Write (KB/s)"))
        self.upload_plot.setTitle(self.lang.get('upload_graph_title', "Upload (KB/s)"))
        self.download_plot.setTitle(self.lang.get('download_graph_title', "Download (KB/s)"))

        self.refresh_startup_btn.setText(self.lang.get('refresh_startup', "Refresh Startup Programs"))
        self.disable_startup_btn.setText(self.lang.get('disable_startup', "Disable Selected"))
        self.enable_startup_btn.setText(self.lang.get('enable_startup', "Enable Selected"))
        self.about_text.setPlainText(self.lang['about_text'])
