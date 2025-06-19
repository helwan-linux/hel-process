import sys
import psutil
import pyqtgraph as pg
import importlib.util
import os
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QLineEdit, QComboBox, QMessageBox, QTabWidget, QTextEdit, QInputDialog,
    QMenu, QAction, QHeaderView, QListWidget, QListWidgetItem, QDialog,
    QCheckBox, QSpinBox, QSlider, QGridLayout
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QTimer, Qt

# --- Language Loading ---
def load_language(lang_code):
    lang_path = os.path.join(os.path.dirname(__file__), 'lang', f'{lang_code}.py')
    if not os.path.exists(lang_path):
        # Fallback to English if language file not found
        lang_path = os.path.join(os.path.dirname(__file__), 'lang', 'en.py')
        if not os.path.exists(lang_path):
            raise FileNotFoundError(f"English language file not found at {lang_path}. Please create a 'lang' folder with 'en.py'.")
    spec = importlib.util.spec_from_file_location("lang", lang_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.lang

# --- Main Application Class ---
class ProcessManager(QWidget):
    def __init__(self):
        super().__init__()
        # Set window icon - prioritize the installed one if available, otherwise use local
        icon_path_system = '/usr/share/icons/hicolor/256x256/apps/hel-process.png'
        local_icon_path = os.path.join("logo", "icon.png")

        if os.path.exists(icon_path_system):
            self.setWindowIcon(QIcon(icon_path_system))
        elif os.path.exists(local_icon_path):
            self.setWindowIcon(QIcon(local_icon_path))
        else:
            pass # No icon

        self.lang_code = 'en' # Default language. Make sure this file exists in 'lang' folder.
        try:
            self.lang = load_language(self.lang_code)
        except FileNotFoundError as e:
            QMessageBox.critical(self, "Error", str(e) + "\n" + self.lang.get('language_file_missing_hint', "Ensure 'lang' folder exists with 'en.py' and 'ar.py' inside."))
            sys.exit(1)

        self.setWindowTitle(self.lang['title'])
        self.resize(1400, 800)

        # Initialize network counters for monitoring
        self.last_net_bytes_sent = 0
        self.last_net_bytes_recv = 0
        self.last_disk_read_bytes = 0
        self.last_disk_write_bytes = 0

        self.init_ui()
        self.init_graphs()
        self.update_processes()
        self.update_system_info()
        self.update_network_activity()
        self.update_disk_io_graph() # Initial call
        self.update_startup_programs() # Initial call

    def init_ui(self):
        self.layout = QVBoxLayout()
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
        self.lang_selector.setCurrentText(self.lang_code) # Set initial language selected
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
        self.cpu_plot = self.graph_widget.addPlot(title=self.lang.get('cpu_graph_title', "CPU Usage (%)"))
        self.cpu_curve = self.cpu_plot.plot(pen='y')
        self.cpu_data = []

        self.graph_widget.nextRow()
        self.ram_plot = self.graph_widget.addPlot(title=self.lang.get('ram_graph_title', "RAM Usage (%)"))
        self.ram_curve = self.ram_plot.plot(pen='c')
        self.ram_data = []

        self.graph_widget.nextRow()
        self.disk_read_plot = self.graph_widget.addPlot(title=self.lang.get('disk_read_graph_title', "Disk Read (KB/s)"))
        self.disk_read_curve = self.disk_read_plot.plot(pen='m')
        self.disk_read_data = []

        self.graph_widget.nextRow()
        self.disk_write_plot = self.graph_widget.addPlot(title=self.lang.get('disk_write_graph_title', "Disk Write (KB/s)"))
        self.disk_write_curve = self.disk_write_plot.plot(pen='w')
        self.disk_write_data = []

        self.tabs.addTab(self.graph_widget, self.lang['tab_performance'])

        # --- Processes Tab ---
        self.process_tab = QWidget()
        self.process_layout = QVBoxLayout()
        self.process_tab.setLayout(self.process_layout)
        self.table = QTableWidget()
        # PID, Name, CPU, RAM, User, Parent PID, Start Time, Path, Threads, Status (for suspend/resume)
        self.table.setColumnCount(10)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.horizontalHeader().sectionClicked.connect(self.sort_processes_table) # Enable sorting
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
        self.sys_layout = QVBoxLayout()
        self.sys_tab.setLayout(self.sys_layout)
        self.sys_info = QTextEdit()
        self.sys_info.setReadOnly(True)
        self.sys_layout.addWidget(self.sys_info)

        self.disk_info = QTextEdit() # For detailed disk info
        self.disk_info.setReadOnly(True)
        self.sys_layout.addWidget(self.disk_info)

        self.tabs.addTab(self.sys_tab, self.lang['tab_system_info'])

        # --- Network Connections & Sensors Tab ---
        self.net_tab = QWidget()
        self.net_layout = QVBoxLayout()
        self.net_tab.setLayout(self.net_layout)
        self.net_info = QTextEdit()
        self.net_info.setReadOnly(True)
        self.net_layout.addWidget(self.net_info)
        self.tabs.addTab(self.net_tab, self.lang['tab_network_sensors'])

        # --- Network Monitor Tab (Graphs + Interface Info) ---
        self.network_monitor_tab = QWidget()
        self.network_monitor_layout = QVBoxLayout()
        self.network_monitor_tab.setLayout(self.network_monitor_layout)

        self.network_graph = pg.GraphicsLayoutWidget()
        self.upload_plot = self.network_graph.addPlot(title=self.lang.get('upload_graph_title', "Upload (KB/s)"))
        self.upload_curve = self.upload_plot.plot(pen='r')
        self.upload_data = []

        self.network_graph.nextRow()
        self.download_plot = self.network_graph.addPlot(title=self.lang.get('download_graph_title', "Download (KB/s)"))
        self.download_curve = self.download_plot.plot(pen='g')
        self.download_data = []

        self.network_monitor_layout.addWidget(self.network_graph)
        self.interface_info = QTextEdit()
        self.interface_info.setReadOnly(True)
        self.network_monitor_layout.addWidget(self.interface_info)
        self.tabs.addTab(self.network_monitor_tab, self.lang['tab_network_monitor'])

        # --- Startup Programs Tab ---
        self.startup_tab = QWidget()
        self.startup_layout = QVBoxLayout()
        self.startup_tab.setLayout(self.startup_layout)
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
        self.about_layout = QVBoxLayout()
        self.about_tab.setLayout(self.about_layout)
        self.about_text = QTextEdit()
        self.about_text.setReadOnly(True)
        self.about_layout.addWidget(self.about_text)
        self.tabs.addTab(self.about_tab, self.lang['tab_about'])

        # --- Status Bar ---
        self.status_bar = QLabel("Ready.")
        self.status_bar.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.layout.addWidget(self.status_bar)

        # Initial text update
        self.update_texts()

    def init_graphs(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_graphs)
        self.timer.timeout.connect(self.update_system_info)
        self.timer.timeout.connect(self.update_network_activity)
        self.timer.timeout.connect(self.update_network_monitor)
        self.timer.timeout.connect(self.update_disk_io_graph)
        self.timer.timeout.connect(self.update_status_bar)
        self.timer.start(1000) # Update every 1 second

    def update_graphs(self):
        # Update CPU and RAM graphs
        self.cpu_data = self.cpu_data[-59:] + [psutil.cpu_percent()]
        self.ram_data = self.ram_data[-59:] + [psutil.virtual_memory().percent]
        self.cpu_curve.setData(self.cpu_data)
        self.ram_curve.setData(self.ram_data)

    def update_disk_io_graph(self):
        # Update Disk I/O graphs
        disk_io = psutil.disk_io_counters()
        if disk_io:
            read_speed = (disk_io.read_bytes - self.last_disk_read_bytes) / 1024 # KB/s
            write_speed = (disk_io.write_bytes - self.last_disk_write_bytes) / 1024 # KB/s

            self.disk_read_data = self.disk_read_data[-59:] + [read_speed]
            self.disk_write_data = self.disk_write_data[-59:] + [write_speed]
            self.disk_read_curve.setData(self.disk_read_data)
            self.disk_write_curve.setData(self.disk_write_data)

            self.last_disk_read_bytes = disk_io.read_bytes
            self.last_disk_write_bytes = disk_io.write_bytes
        else:
            self.disk_read_plot.setTitle(self.lang.get('disk_io_not_available', "Disk I/O Not Available"))
            self.disk_write_plot.setTitle("") # Clear second title if unavailable


    def update_system_info(self):
        # Display system-wide information
        boot = datetime.fromtimestamp(psutil.boot_time()).strftime('%Y-%m-%d %H:%M:%S')
        disk_usage = psutil.disk_usage('/')

        info = self.lang.get('sys_info_boot', "System Boot Time: {boot_time}\n").format(boot_time=boot)
        info += self.lang.get('sys_info_cpu_cores', "CPU Cores: {physical} Physical / {logical} Logical\n").format(
            physical=psutil.cpu_count(logical=False), logical=psutil.cpu_count()
        )
        info += self.lang.get('sys_info_cpu_usage', "CPU Usage: {cpu_percent}%\n").format(cpu_percent=psutil.cpu_percent())
        info += self.lang.get('sys_info_ram_usage', "RAM Usage: {ram_percent}%\n").format(ram_percent=psutil.virtual_memory().percent)
        info += self.lang.get('sys_info_disk_usage', "Disk Usage ({mount_point}): {disk_percent}%\n").format(
            mount_point='/', disk_percent=disk_usage.percent
        )

        # GPU Info (basic check, psutil doesn't directly support GPU usage generally)
        gpu_info_text = self.lang.get('gpu_info_header', "\nGPU Information:\n")
        try:
            # This is a placeholder as psutil itself doesn't offer GPU stats across all platforms
            # You'd need specific libraries like gpustat or py3nvml for proper GPU monitoring.
            if sys.platform.startswith('linux') and os.path.exists('/dev/dri/renderD128'): # Basic check for Linux GPU
                gpu_info_text += self.lang.get('gpu_info_linux_hint', "GPU detection on Linux typically requires `nvidia-smi` or `radeontop`.\n")
                # Example for Nvidia (requires `gpustat` installed via pip):
                # import gpustat
                # gpu_stats = gpustat.new_query().gpus
                # if gpu_stats:
                #     for gpu in gpu_stats:
                #         gpu_info_text += f"  {gpu.name}: {gpu.utilization}% - {gpu.memory_used}/{gpu.memory_total}MB - {gpu.temperature}°C\n"
                # else:
                #     gpu_info_text += self.lang.get('gpu_info_not_found', "No GPUs found or gpustat not installed.\n")
            elif sys.platform == 'win32':
                gpu_info_text += self.lang.get('gpu_info_windows_hint', "GPU detection on Windows often requires WMI queries or third-party tools.\n")
            else:
                gpu_info_text += self.lang.get('gpu_info_not_supported', "GPU monitoring not directly supported by psutil on this OS.\n")

        except Exception as e:
            gpu_info_text += self.lang.get('gpu_info_error', "Error retrieving GPU info: {error}\n").format(error=e)
        info += gpu_info_text

        # Logged-in Users
        users_info = self.lang.get('users_info_header', "\nLogged-in Users:\n")
        try:
            users = psutil.users()
            if users:
                for user in users:
                    users_info += self.lang.get('user_format', "  User: {name}, Terminal: {terminal}, Host: {host}, Since: {started}\n").format(
                        name=user.name, terminal=user.terminal or self.lang.get('none', 'None'),
                        host=user.host or self.lang.get('none', 'None'),
                        started=datetime.fromtimestamp(user.started).strftime('%Y-%m-%d %H:%M:%S')
                    )
            else:
                users_info += self.lang.get('no_users_found', "No users currently logged in.\n")
        except Exception as e:
            users_info += self.lang.get('users_info_error', "Error retrieving user info: {error}\n").format(error=e)
        info += users_info

        self.sys_info.setPlainText(info)

        # Detailed Disk Info
        disk_details = self.lang.get('disk_details_header', "Disk Partitions:\n")
        try:
            partitions = psutil.disk_partitions()
            for part in partitions:
                disk_details += self.lang.get('disk_partition_format',
                    "  Device: {device}, Mountpoint: {mountpoint}, Filesystem: {fstype}\n"
                ).format(device=part.device, mountpoint=part.mountpoint, fstype=part.fstype)
                try:
                    usage = psutil.disk_usage(part.mountpoint)
                    disk_details += self.lang.get('disk_usage_format',
                        "    Total: {total_gb:.2f} GB, Used: {used_gb:.2f} GB, Free: {free_gb:.2f} GB, Used: {percent}%\n"
                    ).format(
                        total_gb=usage.total / (1024**3), used_gb=usage.used / (1024**3),
                        free_gb=usage.free / (1024**3), percent=usage.percent
                    )
                except Exception as e:
                    disk_details += self.lang.get('disk_usage_error', "    Error getting usage: {error}\n").format(error=e)
        except Exception as e:
            disk_details += self.lang.get('disk_details_error', "Error retrieving disk partitions: {error}\n").format(error=e)
        self.disk_info.setPlainText(disk_details)

    def update_network_activity(self):
        # Display active network connections and sensor temperatures
        net_info_text = self.lang.get('net_info_connections', "Active Network Connections:\n")
        for conn in psutil.net_connections(kind='inet'):
            laddr = f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else ""
            raddr = f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else ""
            net_info_text += self.lang.get('net_conn_format', "PID: {pid}, Status: {status}, Local: {local}, Remote: {remote}\n").format(
                pid=conn.pid if conn.pid else 'N/A', status=conn.status, local=laddr, remote=raddr
            )

        try:
            sensors = psutil.sensors_temperatures()
            if sensors:
                net_info_text += self.lang.get('net_info_temps_header', "\nTemperatures:\n")
                for name, entries in sensors.items():
                    for entry in entries:
                        net_info_text += self.lang.get('net_info_temp_format', "{name} - {label}: {current}°C\n").format(
                            name=name, label=entry.label or self.lang.get('unnamed_sensor', 'Unnamed'), current=entry.current
                        )
            else:
                net_info_text += self.lang.get('no_temp_sensors', "\nTemperature sensors not available.\n")
        except Exception:
            net_info_text += self.lang.get('no_temp_sensors_error', "\nCould not retrieve temperature sensor data (permission or hardware issue).\n")

        self.net_info.setPlainText(net_info_text)

    def update_network_monitor(self):
        # Update network speed graphs and interface details
        current_net = psutil.net_io_counters()
        upload_speed = (current_net.bytes_sent - self.last_net_bytes_sent) / 1024 # KB/s
        download_speed = (current_net.bytes_recv - self.last_net_bytes_recv) / 1024 # KB/s

        self.upload_data = self.upload_data[-59:] + [upload_speed]
        self.download_data = self.download_data[-59:] + [download_speed]
        self.upload_curve.setData(self.upload_data)
        self.download_curve.setData(self.download_data)

        self.last_net_bytes_sent = current_net.bytes_sent
        self.last_net_bytes_recv = current_net.bytes_recv

        details = self.lang.get('net_interfaces_header', "Network Interfaces:\n")
        for name, stats in psutil.net_io_counters(pernic=True).items():
            details += self.lang.get('net_interface_format', "{name}: Sent: {sent_kb:.1f} KB, Received: {recv_kb:.1f} KB\n").format(
                name=name, sent_kb=stats.bytes_sent / 1024, recv_kb=stats.bytes_recv / 1024
            )
        self.interface_info.setPlainText(details)

    def update_startup_programs(self):
        self.startup_list.clear()
        try:
            # psutil.win_service_iter() and psutil.boot_time() provide some info.
            # For true startup programs like msconfig on Windows,
            # you'd typically need platform-specific APIs or libraries.
            # psutil's 'autostart' module is in experimental.
            # Example for Windows using winreg (requires win32api on some systems):
            # import winreg
            # def get_windows_startup():
            #     startup_entries = []
            #     reg_paths = [
            #         r"Software\Microsoft\Windows\CurrentVersion\Run",
            #         r"Software\Microsoft\Windows\CurrentVersion\RunOnce"
            #     ]
            #     for path in reg_paths:
            #         try:
            #             key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, path)
            #             for i in range(1024): # Max entries to try
            #                 try:
            #                     name, value, type = winreg.EnumValue(key, i)
            #                     startup_entries.append({'name': name, 'path': value, 'enabled': True, 'type': 'Registry'})
            #                 except OSError:
            #                     break
            #         except Exception:
            #             pass
            #     return startup_entries

            # if sys.platform == "win32":
            #     startup_programs = get_windows_startup()
            # elif sys.platform.startswith('linux'):
            #     # Linux startup programs are complex (systemd, XDG autostart, etc.)
            #     # psutil doesn't directly list them.
            #     # This is a placeholder.
            #     startup_programs = [{'name': 'Systemd Service Example', 'path': 'N/A', 'enabled': True, 'type': 'Service (Placeholder)'}]
            # else:
            #     startup_programs = []

            # For now, a simplified placeholder or just mention limitation
            self.startup_list.addItem(self.lang.get('startup_info_placeholder', "Startup programs listing is complex and platform-specific.\npsutil offers limited direct access for this.\n\nOn Windows, it often involves registry keys and startup folders.\nOn Linux, it involves systemd, XDG autostart, and session managers.\n\nThis feature would require platform-specific implementations."))
            self.startup_list.item(0).setFlags(Qt.NoItemFlags) # Make it non-selectable
            self.disable_startup_btn.setEnabled(False) # Disable buttons as this is a placeholder
            self.enable_startup_btn.setEnabled(False)


            # To actually implement this, you'd integrate with:
            # - Windows: winreg, WMI, or pywin32 for COM objects
            # - Linux: Parsing .desktop files in XDG autostart directories, checking systemd services
            # This is beyond a simple psutil integration.
        except Exception as e:
            self.startup_list.addItem(self.lang.get('startup_error', "Error retrieving startup programs: {e}").format(e=e))
            self.startup_list.item(0).setFlags(Qt.NoItemFlags)
            self.disable_startup_btn.setEnabled(False)
            self.enable_startup_btn.setEnabled(False)

    def set_startup_status(self, enable):
        # Placeholder for actual implementation
        QMessageBox.information(self, self.lang['title'],
                               self.lang.get('startup_feature_note', "This feature is a placeholder and requires platform-specific implementation to enable/disable startup programs."))


    def update_status_bar(self):
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        disk = psutil.disk_usage('/').percent
        status_text = self.lang.get('status_bar_format', "CPU: {cpu}% | RAM: {ram}% | Disk: {disk}%").format(
            cpu=cpu, ram=ram, disk=disk
        )
        self.status_bar.setText(status_text)


    def change_language(self):
        self.lang_code = self.lang_selector.currentData()
        try:
            self.lang = load_language(self.lang_code)
        except FileNotFoundError as e:
            QMessageBox.critical(self, "Error", str(e) + "\n" + self.lang.get('language_file_missing_hint', "Ensure 'lang' folder exists with 'en.py' and 'ar.py' inside."))
            self.lang_code = 'en' # Fallback to English if new language file is missing
            self.lang_selector.setCurrentIndex(self.lang_selector.findData('en'))
            self.lang = load_language('en') # Reload English
        self.update_texts()
        self.update_processes() # Refresh process table headers
        self.update_startup_programs() # Refresh startup tab text

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

        # Update table headers
        self.table.setHorizontalHeaderLabels(
            self.lang['columns_process_table']
        )

        # Update tab titles
        self.tabs.setTabText(0, self.lang['tab_performance'])
        self.tabs.setTabText(1, self.lang['tab_processes'])
        self.tabs.setTabText(2, self.lang['tab_system_info'])
        self.tabs.setTabText(3, self.lang['tab_network_sensors'])
        self.tabs.setTabText(4, self.lang['tab_network_monitor'])
        self.tabs.setTabText(5, self.lang.get('tab_startup_programs', "Startup Programs")) # New Tab
        self.tabs.setTabText(6, self.lang['tab_about']) # Index changed due to new tab

        # Update graph titles
        self.cpu_plot.setTitle(self.lang.get('cpu_graph_title', "CPU Usage (%)"))
        self.ram_plot.setTitle(self.lang.get('ram_graph_title', "RAM Usage (%)"))
        self.disk_read_plot.setTitle(self.lang.get('disk_read_graph_title', "Disk Read (KB/s)"))
        self.disk_write_plot.setTitle(self.lang.get('disk_write_graph_title', "Disk Write (KB/s)"))
        self.upload_plot.setTitle(self.lang.get('upload_graph_title', "Upload (KB/s)"))
        self.download_plot.setTitle(self.lang.get('download_graph_title', "Download (KB/s)"))

        # Startup Tab Buttons
        self.refresh_startup_btn.setText(self.lang.get('refresh_startup', "Refresh Startup Programs"))
        self.disable_startup_btn.setText(self.lang.get('disable_startup', "Disable Selected"))
        self.enable_startup_btn.setText(self.lang.get('enable_startup', "Enable Selected"))


        self.about_text.setPlainText(self.lang['about_text'])

    def update_processes(self):
        search_text = self.search_bar.text().lower()
        self.table.setRowCount(0) # Clear existing rows
        processes_data = [] # Store data to sort before displaying

        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'username', 'create_time', 'exe', 'num_threads', 'ppid', 'status']):
            try:
                pid = proc.info.get('pid', 'N/A')
                name = proc.info.get('name', '') or ''
                cpu_percent = proc.info.get('cpu_percent', 0.0)
                mem_percent = proc.info.get('memory_percent', 0.0)
                username = proc.info.get('username', 'N/A')
                create_time = proc.info.get('create_time', None)
                exe_path = proc.info.get('exe', '')
                num_threads = proc.info.get('num_threads', 'N/A')
                ppid = proc.info.get('ppid', 'N/A')
                status = proc.info.get('status', 'N/A')

                if search_text and search_text not in name.lower() and search_text not in str(pid):
                    continue

                start_time_str = "N/A"
                if create_time:
                    try:
                        start_time_str = datetime.fromtimestamp(create_time).strftime('%Y-%m-%d %H:%M:%S')
                    except (OSError, ValueError):
                        pass

                path_str = exe_path if exe_path else self.lang.get('not_available', 'N/A')
                if not path_str or path_str == self.lang.get('not_available', 'N/A'): # Try proc.exe() if info.exe is empty
                     try:
                         path_str = proc.exe() if proc.exe() else self.lang.get('not_available', 'N/A')
                     except (psutil.AccessDenied, psutil.NoSuchProcess, OSError):
                         path_str = self.lang.get('permission_denied', "Permission Denied / N/A")

                processes_data.append({
                    'pid': pid, 'name': name, 'cpu': cpu_percent, 'mem': mem_percent,
                    'user': username, 'ppid': ppid, 'start_time': start_time_str,
                    'path': path_str, 'threads': num_threads, 'status': status,
                    'proc_object': proc # Keep reference to psutil process object for actions
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
            except Exception as e:
                print(f"Error processing process info: {e}")
                continue

        # Populate table after gathering all data
        self.table.setSortingEnabled(False) # Disable sorting during population
        for row_data in processes_data:
            row = self.table.rowCount()
            self.table.insertRow(row)

            self.table.setItem(row, 0, QTableWidgetItem(str(row_data['pid'])))
            self.table.setItem(row, 1, QTableWidgetItem(row_data['name']))
            self.table.setItem(row, 2, QTableWidgetItem(f"{row_data['cpu']:.1f}"))
            self.table.setItem(row, 3, QTableWidgetItem(f"{row_data['mem']:.1f}"))
            self.table.setItem(row, 4, QTableWidgetItem(row_data['user']))
            self.table.setItem(row, 5, QTableWidgetItem(str(row_data['ppid']))) # Parent PID
            self.table.setItem(row, 6, QTableWidgetItem(row_data['start_time']))
            self.table.setItem(row, 7, QTableWidgetItem(row_data['path']))
            self.table.setItem(row, 8, QTableWidgetItem(str(row_data['threads'])))
            self.table.setItem(row, 9, QTableWidgetItem(row_data['status']))

            # Store the psutil process object with the item for easy retrieval
            self.table.item(row, 0).setData(Qt.UserRole, row_data['proc_object'])
        self.table.setSortingEnabled(True) # Re-enable sorting

    def sort_processes_table(self, logical_index):
        self.table.sortItems(logical_index, Qt.AscendingOrder) # Default to ascending

    def get_selected_process_object(self):
        row = self.table.currentRow()
        if row == -1:
            QMessageBox.warning(self, self.lang['title'], self.lang.get('select_process_warning', "Please select a process."))
            return None
        item = self.table.item(row, 0)
        if not item:
            QMessageBox.warning(self, self.lang['title'], self.lang.get('invalid_process_warning', "Invalid process selected."))
            return None
        proc_obj = item.data(Qt.UserRole) # Retrieve the stored psutil process object
        if proc_obj is None:
            QMessageBox.warning(self, self.lang['title'], self.lang.get('invalid_process_warning', "Invalid process selected (no process object found)."))
            return None
        try:
            # Refresh the process object to ensure it's current
            return psutil.Process(proc_obj.pid)
        except psutil.NoSuchProcess:
            QMessageBox.warning(self, self.lang['title'], self.lang.get('no_such_process_error', "Process no longer exists."))
            self.update_processes()
            return None
        except Exception as e:
            QMessageBox.critical(self, self.lang['title'], self.lang.get('general_error', "An unexpected error occurred: {e}").format(e=e))
            return None


    def kill_selected_process(self):
        proc = self.get_selected_process_object()
        if proc is None:
            return
        try:
            reply = QMessageBox.question(self, self.lang['title'],
                                         self.lang.get('confirm_kill', "Are you sure you want to kill process {pid} ({name})?").format(pid=proc.pid, name=proc.name()),
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                proc.kill()
                QMessageBox.information(self, self.lang['title'], self.lang.get('kill_success', "Process {pid} killed successfully.").format(pid=proc.pid))
                self.update_processes()
        except psutil.NoSuchProcess:
            QMessageBox.warning(self, self.lang['title'], self.lang.get('no_such_process_error', "Process no longer exists."))
            self.update_processes()
        except psutil.AccessDenied:
            QMessageBox.critical(self, self.lang['title'], self.lang.get('permission_denied_error', "Permission denied to kill this process. Try running as administrator/root."))
        except Exception as e:
            QMessageBox.critical(self, self.lang['title'], self.lang.get('kill_error', "An error occurred while trying to kill the process: {e}").format(e=e))

    def renice_process(self):
        proc = self.get_selected_process_object()
        if proc is None:
            return
        try:
            current_nice = proc.nice()
            value, ok = QInputDialog.getInt(self, self.lang.get('renice_title', "Change Priority"),
                                            self.lang.get('renice_prompt', "Nice Value (-20 to 19): Current: {current}").format(current=current_nice),
                                            current_nice, -20, 19)
            if ok:
                proc.nice(value)
                QMessageBox.information(self, self.lang['title'], self.lang.get('renice_success', "Process {pid} priority set to {value}.").format(pid=proc.pid, value=value))
                self.update_processes()
        except psutil.NoSuchProcess:
            QMessageBox.warning(self, self.lang['title'], self.lang.get('no_such_process_error', "Process no longer exists."))
            self.update_processes()
        except psutil.AccessDenied:
            QMessageBox.critical(self, self.lang['title'], self.lang.get('permission_denied_error', "Permission denied to change priority. Try running as administrator/root."))
        except Exception as e:
            QMessageBox.critical(self, self.lang['title'], self.lang.get('renice_error', "An error occurred while trying to change priority: {e}").format(e=e))

    def inspect_process(self):
        proc = self.get_selected_process_object()
        if proc is None:
            return
        try:
            info = self.lang.get('inspect_pid', "PID: {pid}\n").format(pid=proc.pid)
            info += self.lang.get('inspect_name', "Name: {name}\n").format(name=proc.name())
            info += self.lang.get('inspect_exe', "Executable: {exe}\n").format(exe=proc.exe() if proc.exe() else self.lang.get('not_available', 'N/A'))
            info += self.lang.get('inspect_status', "Status: {status}\n").format(status=proc.status())
            info += self.lang.get('inspect_threads', "Threads: {threads}\n").format(threads=proc.num_threads())
            info += self.lang.get('inspect_user', "User: {user}\n").format(user=proc.username())
            info += self.lang.get('inspect_ppid', "Parent PID: {ppid}\n").format(ppid=proc.ppid())
            info += self.lang.get('inspect_cwd', "CWD: {cwd}\n").format(cwd=proc.cwd() if proc.cwd() else self.lang.get('not_available', 'N/A'))
            info += self.lang.get('inspect_cmdline', "Command Line: {cmdline}\n").format(cmdline=' '.join(proc.cmdline()) if proc.cmdline() else self.lang.get('not_available', 'N/A'))

            # Attempt to get open files
            open_files_info = []
            try:
                for f in proc.open_files():
                    open_files_info.append(f.path)
                info += self.lang.get('inspect_open_files', "\nOpen Files ({count}):\n{files}\n").format(
                    count=len(open_files_info), files='\n'.join(open_files_info) if open_files_info else self.lang.get('none', 'None')
                )
            except psutil.AccessDenied:
                info += self.lang.get('inspect_open_files_denied', "\nOpen Files: Permission Denied\n")
            except Exception as e:
                info += self.lang.get('inspect_open_files_error', "\nOpen Files: Error retrieving ({error})\n").format(error=e)

            # Attempt to get network connections
            connections_info = []
            try:
                for conn in proc.connections():
                    laddr = f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else ""
                    raddr = f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else ""
                    connections_info.append(f"  {conn.status} Local: {laddr}, Remote: {raddr}")
                info += self.lang.get('inspect_connections', "\nConnections ({count}):\n{conns}\n").format(
                    count=len(connections_info), conns='\n'.join(connections_info) if connections_info else self.lang.get('none', 'None')
                )
            except psutil.AccessDenied:
                info += self.lang.get('inspect_connections_denied', "\nConnections: Permission Denied\n")
            except Exception as e:
                info += self.lang.get('inspect_connections_error', "\nConnections: Error retrieving ({error})\n").format(error=e)

            QMessageBox.information(self, self.lang.get('inspect_dialog_title', "Process Details"), info)
        except psutil.NoSuchProcess:
            QMessageBox.warning(self, self.lang['title'], self.lang.get('no_such_process_error', "Process no longer exists."))
            self.update_processes()
        except psutil.AccessDenied:
            QMessageBox.critical(self, self.lang['title'], self.lang.get('permission_denied_error', "Permission denied to inspect this process. Try running as administrator/root."))
        except Exception as e:
            QMessageBox.critical(self, self.lang['title'], self.lang.get('inspect_error', "An error occurred while trying to inspect the process: {e}").format(e=e))

    def suspend_selected_process(self):
        proc = self.get_selected_process_object()
        if proc is None:
            return
        try:
            if proc.status() == psutil.STATUS_STOPPED:
                QMessageBox.information(self, self.lang['title'], self.lang.get('already_suspended', "Process {pid} is already suspended.").format(pid=proc.pid))
                return

            proc.suspend()
            QMessageBox.information(self, self.lang['title'], self.lang.get('suspend_success', "Process {pid} suspended successfully.").format(pid=proc.pid))
            self.update_processes()
        except psutil.NoSuchProcess:
            QMessageBox.warning(self, self.lang['title'], self.lang.get('no_such_process_error', "Process no longer exists."))
            self.update_processes()
        except psutil.AccessDenied:
            QMessageBox.critical(self, self.lang['title'], self.lang.get('permission_denied_error', "Permission denied to suspend this process. Try running as administrator/root."))
        except Exception as e:
            QMessageBox.critical(self, self.lang['title'], self.lang.get('suspend_error', "An error occurred while trying to suspend the process: {e}").format(e=e))

    def resume_selected_process(self):
        proc = self.get_selected_process_object()
        if proc is None:
            return
        try:
            if proc.status() != psutil.STATUS_STOPPED:
                QMessageBox.information(self, self.lang['title'], self.lang.get('not_suspended', "Process {pid} is not suspended.").format(pid=proc.pid))
                return

            proc.resume()
            QMessageBox.information(self, self.lang['title'], self.lang.get('resume_success', "Process {pid} resumed successfully.").format(pid=proc.pid))
            self.update_processes()
        except psutil.NoSuchProcess:
            QMessageBox.warning(self, self.lang['title'], self.lang.get('no_such_process_error', "Process no longer exists."))
            self.update_processes()
        except psutil.AccessDenied:
            QMessageBox.critical(self, self.lang['title'], self.lang.get('permission_denied_error', "Permission denied to resume this process. Try running as administrator/root."))
        except Exception as e:
            QMessageBox.critical(self, self.lang['title'], self.lang.get('resume_error', "An error occurred while trying to resume the process: {e}").format(e=e))

    def set_cpu_affinity(self):
        proc = self.get_selected_process_object()
        if proc is None:
            return

        cpu_count = psutil.cpu_count(logical=True)
        if cpu_count == 0:
            QMessageBox.warning(self, self.lang['title'], self.lang.get('no_cpus_found', "No CPU cores found to set affinity."))
            return

        dialog = QDialog(self)
        dialog.setWindowTitle(self.lang.get('set_cpu_affinity_title', "Set CPU Affinity"))
        layout = QVBoxLayout(dialog)

        # Current affinity
        try:
            current_affinity = proc.cpu_affinity()
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            QMessageBox.critical(self, self.lang['title'], self.lang.get('permission_denied_error', "Permission denied to get CPU affinity. Try running as administrator/root."))
            return
        except Exception as e:
            QMessageBox.critical(self.lang.get('general_error', "Error: {e}").format(e=e))
            return

        layout.addWidget(QLabel(self.lang.get('current_affinity', "Current CPU Affinity: {affinity}").format(affinity=current_affinity)))
        layout.addWidget(QLabel(self.lang.get('select_cpus', "Select CPU Cores:")))

        grid_layout = QGridLayout()
        self.affinity_checkboxes = []
        for i in range(cpu_count):
            checkbox = QCheckBox(f"CPU {i}")
            if i in current_affinity:
                checkbox.setChecked(True)
            self.affinity_checkboxes.append(checkbox)
            grid_layout.addWidget(checkbox, i // 4, i % 4) # 4 columns for checkboxes

        layout.addLayout(grid_layout)

        apply_btn = QPushButton(self.lang.get('apply', "Apply"))
        apply_btn.clicked.connect(lambda: self._apply_cpu_affinity(proc, dialog))
        layout.addWidget(apply_btn)

        dialog.exec_()

    def _apply_cpu_affinity(self, proc, dialog):
        selected_cpus = []
        for i, checkbox in enumerate(self.affinity_checkboxes):
            if checkbox.isChecked():
                selected_cpus.append(i)

        if not selected_cpus:
            QMessageBox.warning(self, self.lang['title'], self.lang.get('select_at_least_one_cpu', "Please select at least one CPU core."))
            return

        try:
            proc.cpu_affinity(selected_cpus)
            QMessageBox.information(self, self.lang['title'], self.lang.get('affinity_success', "CPU affinity for {pid} set to {cpus}.").format(pid=proc.pid, cpus=selected_cpus))
            dialog.accept()
        except psutil.AccessDenied:
            QMessageBox.critical(self, self.lang['title'], self.lang.get('permission_denied_error', "Permission denied to set CPU affinity. Try running as administrator/root."))
        except Exception as e:
            QMessageBox.critical(self, self.lang['title'], self.lang.get('affinity_error', "Error setting CPU affinity: {e}").format(e=e))

    def set_io_priority(self):
        proc = self.get_selected_process_object()
        if proc is None:
            return

        io_priorities = {
            self.lang.get('io_priority_high', 'High'): psutil.IOPRIO_HIGH,
            self.lang.get('io_priority_above_normal', 'Above Normal'): psutil.IOPRIO_ABOVE_NORMAL,
            self.lang.get('io_priority_normal', 'Normal'): psutil.IOPRIO_NORMAL,
            self.lang.get('io_priority_below_normal', 'Below Normal'): psutil.IOPRIO_BELOW_NORMAL,
            self.lang.get('io_priority_low', 'Low'): psutil.IOPRIO_LOW,
            self.lang.get('io_priority_idle', 'Idle'): psutil.IOPRIO_IDLE
        }

        # Invert dictionary for lookup
        priority_names = {v: k for k, v in io_priorities.items()}

        dialog = QDialog(self)
        dialog.setWindowTitle(self.lang.get('set_io_priority_title', "Set I/O Priority"))
        layout = QVBoxLayout(dialog)

        try:
            current_io_priority = proc.ionice(as_dict=False) # Returns (ioclass, iodata) tuple
            current_class = current_io_priority[0]
            current_class_name = priority_names.get(current_class, self.lang.get('unknown', 'Unknown'))
            layout.addWidget(QLabel(self.lang.get('current_io_priority', "Current I/O Priority: {priority}").format(priority=current_class_name)))
        except psutil.AccessDenied:
            QMessageBox.critical(self, self.lang['title'], self.lang.get('permission_denied_error', "Permission denied to get I/O priority. Try running as administrator/root."))
            return
        except Exception as e:
            QMessageBox.critical(self, self.lang['title'], self.lang.get('general_error', "Error: {e}").format(e=e))
            return

        combo = QComboBox()
        for name in io_priorities.keys():
            combo.addItem(name, io_priorities[name])
        # Set current selection
        for i in range(combo.count()):
            if combo.itemData(i) == current_class:
                combo.setCurrentIndex(i)
                break

        layout.addWidget(QLabel(self.lang.get('select_io_priority', "Select New I/O Priority:")))
        layout.addWidget(combo)

        apply_btn = QPushButton(self.lang.get('apply', "Apply"))
        apply_btn.clicked.connect(lambda: self._apply_io_priority(proc, combo.currentData(), dialog))
        layout.addWidget(apply_btn)

        dialog.exec_()

    def _apply_io_priority(self, proc, new_priority_value, dialog):
        try:
            proc.ionice(ioclass=new_priority_value)
            QMessageBox.information(self, self.lang['title'], self.lang.get('io_priority_success', "I/O priority for {pid} set successfully.").format(pid=proc.pid))
            dialog.accept()
        except psutil.AccessDenied:
            QMessageBox.critical(self, self.lang['title'], self.lang.get('permission_denied_error', "Permission denied to set I/O priority. Try running as administrator/root."))
        except Exception as e:
            QMessageBox.critical(self, self.lang['title'], self.lang.get('io_priority_error', "Error setting I/O priority: {e}").format(e=e))

    def open_process_file_location(self):
        proc = self.get_selected_process_object()
        if proc is None:
            return
        try:
            exe_path = proc.exe()
            if not exe_path:
                QMessageBox.warning(self, self.lang['title'], self.lang.get('no_executable_path', "Could not find executable path for this process."))
                return

            if sys.platform == "win32":
                os.startfile(os.path.dirname(exe_path))
            elif sys.platform == "darwin": # macOS
                os.system(f"open {os.path.dirname(exe_path)}")
            else: # Linux
                os.system(f"xdg-open {os.path.dirname(exe_path)}")
        except (psutil.AccessDenied, psutil.NoSuchProcess, OSError) as e:
            QMessageBox.critical(self, self.lang['title'], self.lang.get('permission_denied_or_no_path', "Permission denied or path not accessible: {e}").format(e=e))
        except Exception as e:
            QMessageBox.critical(self, self.lang['title'], self.lang.get('open_location_error', "Error opening file location: {e}").format(e=e))


if __name__ == "__main__":
    # Ensure 'lang' folder exists and has 'en.py' at least
    # These checks are minimal. The `load_language` function will handle more robust errors.
    if not os.path.exists('lang'):
        print("Warning: 'lang' folder not found. Please create it and place language files inside.")
    if not os.path.exists(os.path.join('lang', 'en.py')):
        print("Warning: 'lang/en.py' not found. Please create this file with English translations.")
    if not os.path.exists(os.path.join('lang', 'ar.py')):
        print("Warning: 'lang/ar.py' not found. Please create this file with Arabic translations.")

    # Ensure 'logo' folder exists for the icon
    if not os.path.exists('logo'):
        os.makedirs('logo')
    if not os.path.exists(os.path.join('logo', 'icon.png')):
        # You'll need to provide a default icon. For now, it will just not set an icon if missing.
        print("Warning: 'logo/icon.png' not found. Window icon might not be displayed.")


    app = QApplication(sys.argv)
    window = ProcessManager()
    window.show()
    sys.exit(app.exec_())
