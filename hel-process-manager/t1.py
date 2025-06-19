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
    QMenu, QAction, QHeaderView
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QTimer, Qt

# Load language file
def load_language(lang_code):
    lang_path = os.path.join(os.path.dirname(__file__), 'lang', f'{lang_code}.py')
    spec = importlib.util.spec_from_file_location("lang", lang_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.lang

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
            # Fallback to a default or show no icon if neither is found
            pass

        self.lang_code = 'en' # Default language
        self.lang = load_language(self.lang_code)
        self.setWindowTitle(self.lang['title'])
        self.resize(1400, 800)

        self.last_net = psutil.net_io_counters() # Initialize for network monitor
        self.init_ui()
        self.init_graphs()
        self.update_processes()
        self.update_system_info()
        self.update_network_activity()

    def init_ui(self):
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # Top layout for language selector and search bar
        top_layout = QHBoxLayout()
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
        self.lang_selector.currentIndexChanged.connect(self.change_language)
        top_layout.addWidget(QLabel(self.lang['language']))
        top_layout.addWidget(self.lang_selector)

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText(self.lang['search'])
        self.search_bar.textChanged.connect(self.update_processes)
        top_layout.addWidget(self.search_bar)
        self.layout.addLayout(top_layout)

        # Main tab widget
        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)

        # Performance Tab
        self.graph_widget = pg.GraphicsLayoutWidget()
        self.cpu_plot = self.graph_widget.addPlot(title="CPU Usage (%)")
        self.cpu_curve = self.cpu_plot.plot(pen='y')
        self.cpu_data = []
        self.graph_widget.nextRow()
        self.ram_plot = self.graph_widget.addPlot(title="RAM Usage (%)")
        self.ram_curve = self.ram_plot.plot(pen='c')
        self.ram_data = []
        self.tabs.addTab(self.graph_widget, self.lang['tab_performance'])

        # Processes Tab
        self.process_tab = QWidget()
        self.process_layout = QVBoxLayout()
        self.process_tab.setLayout(self.process_layout)
        self.table = QTableWidget()
        self.table.setColumnCount(8) # PID, Name, CPU, RAM, User, Start Time, Path, Threads
        self.table.setHorizontalHeaderLabels(
            self.lang['columns'] + [
                self.lang.get('start_time_col', "Start Time"),
                self.lang.get('path_col', "Path"),
                self.lang.get('threads_col', "Threads")
            ]
        )
        self.table.setEditTriggers(QTableWidget.NoEditTriggers) # Make table non-editable
        self.table.setSelectionBehavior(QTableWidget.SelectRows) # Select entire rows
        self.table.setSelectionMode(QTableWidget.SingleSelection) # Allow only single row selection
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents) # Adjust column width to content
        self.process_layout.addWidget(self.table)

        # Buttons for Processes Tab
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

        # New buttons for advanced process management
        self.suspend_btn = QPushButton(self.lang.get('suspend_process', "Suspend"))
        self.suspend_btn.clicked.connect(self.suspend_selected_process)
        btns_layout.addWidget(self.suspend_btn)

        self.resume_btn = QPushButton(self.lang.get('resume_process', "Resume"))
        self.resume_btn.clicked.connect(self.resume_selected_process)
        btns_layout.addWidget(self.resume_btn)

        self.process_layout.addLayout(btns_layout)
        self.tabs.addTab(self.process_tab, self.lang['tab_processes'])

        # System Info Tab
        self.sys_tab = QWidget()
        self.sys_layout = QVBoxLayout()
        self.sys_tab.setLayout(self.sys_layout)
        self.sys_info = QTextEdit()
        self.sys_info.setReadOnly(True)
        self.sys_layout.addWidget(self.sys_info)
        self.tabs.addTab(self.sys_tab, self.lang['tab_system_info'])

        # Network Connections & Sensors Tab
        self.net_tab = QWidget()
        self.net_layout = QVBoxLayout()
        self.net_tab.setLayout(self.net_layout)
        self.net_info = QTextEdit()
        self.net_info.setReadOnly(True)
        self.net_layout.addWidget(self.net_info)
        self.tabs.addTab(self.net_tab, self.lang['tab_network_sensors'])

        # Network Monitor Tab (Graphs + Interface Info)
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

        # About Tab
        self.about_tab = QWidget()
        self.about_layout = QVBoxLayout()
        self.about_tab.setLayout(self.about_layout)
        self.about_text = QTextEdit()
        self.about_text.setReadOnly(True)
        self.about_layout.addWidget(self.about_text)
        self.tabs.addTab(self.about_tab, self.lang['tab_about'])

        self.update_texts() # Initial text update based on default language

    def init_graphs(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_graphs)
        self.timer.timeout.connect(self.update_system_info)
        self.timer.timeout.connect(self.update_network_activity)
        self.timer.timeout.connect(self.update_network_monitor)
        self.timer.start(1000) # Update every 1 second

    def update_graphs(self):
        # Update CPU and RAM graphs
        self.cpu_data = self.cpu_data[-59:] + [psutil.cpu_percent()]
        self.ram_data = self.ram_data[-59:] + [psutil.virtual_memory().percent]
        self.cpu_curve.setData(self.cpu_data)
        self.ram_curve.setData(self.ram_data)

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
        info += self.lang.get('sys_info_disk_total', "Disk Total: {total_gb:.2f} GB\n").format(total_gb=disk_usage.total / (1024**3))
        info += self.lang.get('sys_info_disk_used', "Disk Used: {used_gb:.2f} GB\n").format(used_gb=disk_usage.used / (1024**3))
        info += self.lang.get('sys_info_disk_free', "Disk Free: {free_gb:.2f} GB\n").format(free_gb=disk_usage.free / (1024**3))

        self.sys_info.setPlainText(info)

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
        upload_speed = (current_net.bytes_sent - self.last_net.bytes_sent) / 1024 # KB/s
        download_speed = (current_net.bytes_recv - self.last_net.bytes_recv) / 1024 # KB/s

        self.upload_data = self.upload_data[-59:] + [upload_speed]
        self.download_data = self.download_data[-59:] + [download_speed]
        self.upload_curve.setData(self.upload_data)
        self.download_curve.setData(self.download_data)

        self.last_net = current_net # Store for next calculation

        details = self.lang.get('net_interfaces_header', "Network Interfaces:\n")
        for name, stats in psutil.net_io_counters(pernic=True).items():
            details += self.lang.get('net_interface_format', "{name}: Sent: {sent_kb:.1f} KB, Received: {recv_kb:.1f} KB\n").format(
                name=name, sent_kb=stats.bytes_sent / 1024, recv_kb=stats.bytes_recv / 1024
            )

        self.interface_info.setPlainText(details)

    def change_language(self):
        self.lang_code = self.lang_selector.currentData()
        self.lang = load_language(self.lang_code)
        self.update_texts()
        self.update_processes() # Refresh process table headers

    def update_texts(self):
        self.setWindowTitle(self.lang['title'])
        self.search_bar.setPlaceholderText(self.lang['search'])
        self.refresh_btn.setText(self.lang['refresh'])
        self.kill_btn.setText(self.lang['kill'])
        self.inspect_btn.setText(self.lang.get('inspect', "Inspect"))
        self.renice_btn.setText(self.lang.get('renice', "Renice"))
        self.suspend_btn.setText(self.lang.get('suspend_process', "Suspend"))
        self.resume_btn.setText(self.lang.get('resume_process', "Resume"))


        # Update table headers
        self.table.setHorizontalHeaderLabels(
            self.lang['columns'] + [
                self.lang.get('start_time_col', "Start Time"),
                self.lang.get('path_col', "Path"),
                self.lang.get('threads_col', "Threads")
            ]
        )

        # Update tab titles
        self.tabs.setTabText(0, self.lang['tab_performance'])
        self.tabs.setTabText(1, self.lang['tab_processes'])
        self.tabs.setTabText(2, self.lang['tab_system_info'])
        self.tabs.setTabText(3, self.lang['tab_network_sensors'])
        self.tabs.setTabText(4, self.lang['tab_network_monitor'])
        self.tabs.setTabText(5, self.lang['tab_about'])

        # Update graph titles
        self.cpu_plot.setTitle(self.lang.get('cpu_graph_title', "CPU Usage (%)"))
        self.ram_plot.setTitle(self.lang.get('ram_graph_title', "RAM Usage (%)"))
        self.upload_plot.setTitle(self.lang.get('upload_graph_title', "Upload (KB/s)"))
        self.download_plot.setTitle(self.lang.get('download_graph_title', "Download (KB/s)"))

        self.about_text.setPlainText(self.lang['about_text'])

    def update_processes(self):
        search_text = self.search_bar.text().lower()
        self.table.setRowCount(0) # Clear existing rows
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'username', 'create_time', 'exe', 'num_threads']):
            try:
                # Get process info, handling potential AccessDenied or NoSuchProcess
                pid = proc.info.get('pid', 'N/A')
                name = proc.info.get('name', '') or ''
                cpu_percent = proc.info.get('cpu_percent', 0.0)
                mem_percent = proc.info.get('memory_percent', 0.0)
                username = proc.info.get('username', 'N/A')
                create_time = proc.info.get('create_time', None)
                exe_path = proc.info.get('exe', '')

                # Apply search filter
                if search_text and search_text not in name.lower() and search_text not in str(pid):
                    continue # Skip if no match

                row = self.table.rowCount()
                self.table.insertRow(row)

                self.table.setItem(row, 0, QTableWidgetItem(str(pid)))
                self.table.setItem(row, 1, QTableWidgetItem(name))
                self.table.setItem(row, 2, QTableWidgetItem(f"{cpu_percent:.1f}"))
                self.table.setItem(row, 3, QTableWidgetItem(f"{mem_percent:.1f}"))
                self.table.setItem(row, 4, QTableWidgetItem(username))

                # Format creation time
                start_time_str = "N/A"
                if create_time:
                    try:
                        start_time_str = datetime.fromtimestamp(create_time).strftime('%Y-%m-%d %H:%M:%S')
                    except (OSError, ValueError):
                        start_time_str = "N/A" # Handle invalid timestamp

                self.table.setItem(row, 5, QTableWidgetItem(start_time_str))

                # Handle executable path
                path_str = exe_path if exe_path else "N/A"
                if not path_str: # In case psutil returns empty string
                     try:
                         path_str = proc.exe() if proc.exe() else "N/A"
                     except (psutil.AccessDenied, psutil.NoSuchProcess, OSError):
                         path_str = self.lang.get('permission_denied', "Permission Denied / N/A")
                self.table.setItem(row, 6, QTableWidgetItem(path_str))


                # Handle number of threads
                threads_str = "N/A"
                try:
                    threads_str = str(proc.num_threads())
                except (psutil.AccessDenied, psutil.NoSuchProcess, OSError):
                    threads_str = self.lang.get('permission_denied', "Permission Denied / N/A")
                self.table.setItem(row, 7, QTableWidgetItem(threads_str))

            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                # Process might have terminated between iteration and info retrieval
                continue
            except Exception as e:
                # Catch any other unexpected errors during process info retrieval
                print(f"Error processing process info: {e}")
                continue

    def get_selected_pid(self):
        row = self.table.currentRow()
        if row == -1:
            QMessageBox.warning(self, self.lang['title'], self.lang.get('select_process_warning', "Please select a process."))
            return None
        pid_item = self.table.item(row, 0)
        if not pid_item:
            QMessageBox.warning(self, self.lang['title'], self.lang.get('invalid_process_warning', "Invalid process selected."))
            return None
        try:
            return int(pid_item.text())
        except ValueError:
            QMessageBox.warning(self, self.lang['title'], self.lang.get('invalid_pid_error', "Could not get process ID."))
            return None

    def kill_selected_process(self):
        pid = self.get_selected_pid()
        if pid is None:
            return
        try:
            proc = psutil.Process(pid)
            reply = QMessageBox.question(self, self.lang['title'],
                                         self.lang.get('confirm_kill', "Are you sure you want to kill process {pid} ({name})?").format(pid=pid, name=proc.name()),
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                proc.kill()
                QMessageBox.information(self, self.lang['title'], self.lang.get('kill_success', "Process {pid} killed successfully.").format(pid=pid))
                self.update_processes()
        except psutil.NoSuchProcess:
            QMessageBox.warning(self, self.lang['title'], self.lang.get('no_such_process_error', "Process no longer exists."))
            self.update_processes()
        except psutil.AccessDenied:
            QMessageBox.critical(self, self.lang['title'], self.lang.get('permission_denied_error', "Permission denied to kill this process. Try running as administrator/root."))
        except Exception as e:
            QMessageBox.critical(self, self.lang['title'], self.lang.get('kill_error', "An error occurred while trying to kill the process: {e}").format(e=e))

    def renice_process(self):
        pid = self.get_selected_pid()
        if pid is None:
            return
        try:
            proc = psutil.Process(pid)
            current_nice = proc.nice()
            value, ok = QInputDialog.getInt(self, self.lang.get('renice_title', "Change Priority"),
                                            self.lang.get('renice_prompt', "Nice Value (-20 to 19): Current: {current}").format(current=current_nice),
                                            current_nice, -20, 19)
            if ok:
                proc.nice(value)
                QMessageBox.information(self, self.lang['title'], self.lang.get('renice_success', "Process {pid} priority set to {value}.").format(pid=pid, value=value))
                self.update_processes() # Update table to reflect change if possible
        except psutil.NoSuchProcess:
            QMessageBox.warning(self, self.lang['title'], self.lang.get('no_such_process_error', "Process no longer exists."))
            self.update_processes()
        except psutil.AccessDenied:
            QMessageBox.critical(self, self.lang['title'], self.lang.get('permission_denied_error', "Permission denied to change priority. Try running as administrator/root."))
        except Exception as e:
            QMessageBox.critical(self, self.lang['title'], self.lang.get('renice_error', "An error occurred while trying to change priority: {e}").format(e=e))

    def inspect_process(self):
        pid = self.get_selected_pid()
        if pid is None:
            return
        try:
            proc = psutil.Process(pid)
            info = self.lang.get('inspect_pid', "PID: {pid}\n").format(pid=proc.pid)
            info += self.lang.get('inspect_name', "Name: {name}\n").format(name=proc.name())
            info += self.lang.get('inspect_exe', "Executable: {exe}\n").format(exe=proc.exe() if proc.exe() else self.lang.get('not_available', 'N/A'))
            info += self.lang.get('inspect_status', "Status: {status}\n").format(status=proc.status())
            info += self.lang.get('inspect_threads', "Threads: {threads}\n").format(threads=proc.num_threads())
            info += self.lang.get('inspect_user', "User: {user}\n").format(user=proc.username())
            info += self.lang.get('inspect_cwd', "CWD: {cwd}\n").format(cwd=proc.cwd() if proc.cwd() else self.lang.get('not_available', 'N/A'))
            info += self.lang.get('inspect_cmdline', "Command Line: {cmdline}\n").format(cmdline=' '.join(proc.cmdline()) if proc.cmdline() else self.lang.get('not_available', 'N/A'))

            # Attempt to get open files (may require higher privileges)
            open_files_info = []
            try:
                for f in proc.open_files():
                    open_files_info.append(f.path)
                info += self.lang.get('inspect_open_files', "Open Files ({count}):\n{files}\n").format(
                    count=len(open_files_info), files='\n'.join(open_files_info) if open_files_info else self.lang.get('none', 'None')
                )
            except psutil.AccessDenied:
                info += self.lang.get('inspect_open_files_denied', "Open Files: Permission Denied\n")
            except Exception as e:
                info += self.lang.get('inspect_open_files_error', "Open Files: Error retrieving ({error})\n").format(error=e)

            # Attempt to get network connections (may require higher privileges)
            connections_info = []
            try:
                for conn in proc.connections():
                    laddr = f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else ""
                    raddr = f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else ""
                    connections_info.append(f"  {conn.status} Local: {laddr}, Remote: {raddr}")
                info += self.lang.get('inspect_connections', "Connections ({count}):\n{conns}\n").format(
                    count=len(connections_info), conns='\n'.join(connections_info) if connections_info else self.lang.get('none', 'None')
                )
            except psutil.AccessDenied:
                info += self.lang.get('inspect_connections_denied', "Connections: Permission Denied\n")
            except Exception as e:
                info += self.lang.get('inspect_connections_error', "Connections: Error retrieving ({error})\n").format(error=e)

            QMessageBox.information(self, self.lang.get('inspect_dialog_title', "Process Details"), info)
        except psutil.NoSuchProcess:
            QMessageBox.warning(self, self.lang['title'], self.lang.get('no_such_process_error', "Process no longer exists."))
            self.update_processes()
        except psutil.AccessDenied:
            QMessageBox.critical(self, self.lang['title'], self.lang.get('permission_denied_error', "Permission denied to inspect this process. Try running as administrator/root."))
        except Exception as e:
            QMessageBox.critical(self, self.lang['title'], self.lang.get('inspect_error', "An error occurred while trying to inspect the process: {e}").format(e=e))

    def suspend_selected_process(self):
        pid = self.get_selected_pid()
        if pid is None:
            return
        try:
            proc = psutil.Process(pid)
            if proc.status() == psutil.STATUS_STOPPED:
                QMessageBox.information(self, self.lang['title'], self.lang.get('already_suspended', "Process {pid} is already suspended.").format(pid=pid))
                return

            proc.suspend()
            QMessageBox.information(self, self.lang['title'], self.lang.get('suspend_success', "Process {pid} suspended successfully.").format(pid=pid))
            self.update_processes()
        except psutil.NoSuchProcess:
            QMessageBox.warning(self, self.lang['title'], self.lang.get('no_such_process_error', "Process no longer exists."))
            self.update_processes()
        except psutil.AccessDenied:
            QMessageBox.critical(self, self.lang['title'], self.lang.get('permission_denied_error', "Permission denied to suspend this process. Try running as administrator/root."))
        except Exception as e:
            QMessageBox.critical(self, self.lang['title'], self.lang.get('suspend_error', "An error occurred while trying to suspend the process: {e}").format(e=e))

    def resume_selected_process(self):
        pid = self.get_selected_pid()
        if pid is None:
            return
        try:
            proc = psutil.Process(pid)
            if proc.status() != psutil.STATUS_STOPPED:
                QMessageBox.information(self, self.lang['title'], self.lang.get('not_suspended', "Process {pid} is not suspended.").format(pid=pid))
                return

            proc.resume()
            QMessageBox.information(self, self.lang['title'], self.lang.get('resume_success', "Process {pid} resumed successfully.").format(pid=pid))
            self.update_processes()
        except psutil.NoSuchProcess:
            QMessageBox.warning(self, self.lang['title'], self.lang.get('no_such_process_error', "Process no longer exists."))
            self.update_processes()
        except psutil.AccessDenied:
            QMessageBox.critical(self, self.lang['title'], self.lang.get('permission_denied_error', "Permission denied to resume this process. Try running as administrator/root."))
        except Exception as e:
            QMessageBox.critical(self, self.lang['title'], self.lang.get('resume_error', "An error occurred while trying to resume the process: {e}").format(e=e))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ProcessManager()
    window.show()
    sys.exit(app.exec_())
