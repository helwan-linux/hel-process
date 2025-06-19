import sys
import psutil
import pyqtgraph as pg
import importlib.util
import os
from datetime import datetime
from PyQt5.QtWidgets import (
	QApplication, QWidget, QVBoxLayout, QHBoxLayout,
	QLabel, QPushButton, QTableWidget, QTableWidgetItem,
	QLineEdit, QComboBox, QMessageBox, QTabWidget, QTextEdit, QInputDialog
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QTimer, Qt

def load_language(lang_code):
	lang_path = os.path.join(os.path.dirname(__file__), 'lang', f'{lang_code}.py')
	spec = importlib.util.spec_from_file_location("lang", lang_path)
	module = importlib.util.module_from_spec(spec)
	spec.loader.exec_module(module)
	return module.lang

class ProcessManager(QWidget):
	def __init__(self):
		super().__init__()
		self.setWindowIcon(QIcon(os.path.join("logo", "icon.png")))

		self.lang_code = 'en'
		self.lang = load_language(self.lang_code)
		self.setWindowTitle(self.lang['title'])
		self.resize(1400, 800)
		self.init_ui()
		self.init_graphs()
		self.update_processes()
		self.update_system_info()
		self.update_network_activity()

	def init_ui(self):
		self.layout = QVBoxLayout()
		self.setLayout(self.layout)

		top_layout = QHBoxLayout()
		self.lang_selector = QComboBox()
		self.lang_selector.addItem("English", "en")
		self.lang_selector.addItem("العربية", "ar")
		self.lang_selector.addItem("Español", "es")
		self.lang_selector.addItem("Português", "pt")
		self.lang_selector.addItem("Français", "fr")
		self.lang_selector.addItem("Deutsch", "de")         # الألمانية
		self.lang_selector.addItem("Italiano", "it")        # الإيطالية
		self.lang_selector.addItem("Türkçe", "tr")          # التركية
		self.lang_selector.addItem("中文", "zh")             # الصينية المبسطة
		self.lang_selector.currentIndexChanged.connect(self.change_language)
		top_layout.addWidget(QLabel(self.lang['language']))
		top_layout.addWidget(self.lang_selector)

		self.search_bar = QLineEdit()
		self.search_bar.setPlaceholderText(self.lang['search'])
		self.search_bar.textChanged.connect(self.update_processes)
		top_layout.addWidget(self.search_bar)
		self.layout.addLayout(top_layout)

		self.tabs = QTabWidget()
		self.layout.addWidget(self.tabs)

		self.graph_widget = pg.GraphicsLayoutWidget()
		self.cpu_plot = self.graph_widget.addPlot(title="CPU Usage (%)")
		self.cpu_curve = self.cpu_plot.plot(pen='y')
		self.cpu_data = []
		self.graph_widget.nextRow()
		self.ram_plot = self.graph_widget.addPlot(title="RAM Usage (%)")
		self.ram_curve = self.ram_plot.plot(pen='c')
		self.ram_data = []
		self.tabs.addTab(self.graph_widget, self.lang['tab_performance'])

		self.process_tab = QWidget()
		self.process_layout = QVBoxLayout()
		self.process_tab.setLayout(self.process_layout)
		self.table = QTableWidget()
		self.table.setColumnCount(8)
		self.process_layout.addWidget(self.table)

		btns_layout = QHBoxLayout()
		self.refresh_btn = QPushButton(self.lang['refresh'])
		self.refresh_btn.clicked.connect(self.update_processes)
		btns_layout.addWidget(self.refresh_btn)

		self.kill_btn = QPushButton(self.lang['kill'])
		self.kill_btn.clicked.connect(self.kill_selected_process)
		btns_layout.addWidget(self.kill_btn)

		self.renice_btn = QPushButton("Renice")
		self.renice_btn.clicked.connect(self.renice_process)
		btns_layout.addWidget(self.renice_btn)

		self.inspect_btn = QPushButton("Inspect")
		self.inspect_btn.clicked.connect(self.inspect_process)
		btns_layout.addWidget(self.inspect_btn)

		self.process_layout.addLayout(btns_layout)
		self.tabs.addTab(self.process_tab, self.lang['tab_processes'])

		self.sys_tab = QWidget()
		self.sys_layout = QVBoxLayout()
		self.sys_tab.setLayout(self.sys_layout)
		self.sys_info = QTextEdit()
		self.sys_info.setReadOnly(True)
		self.sys_layout.addWidget(self.sys_info)
		self.tabs.addTab(self.sys_tab, self.lang['tab_system_info'])

		self.net_tab = QWidget()
		self.net_layout = QVBoxLayout()
		self.net_tab.setLayout(self.net_layout)
		self.net_info = QTextEdit()
		self.net_info.setReadOnly(True)
		self.net_layout.addWidget(self.net_info)
		self.tabs.addTab(self.net_tab, self.lang['tab_network_sensors'])

		self.network_monitor_tab = QWidget()
		self.network_monitor_layout = QVBoxLayout()
		self.network_monitor_tab.setLayout(self.network_monitor_layout)

		self.network_graph = pg.GraphicsLayoutWidget()
		self.upload_plot = self.network_graph.addPlot(title="Upload (KB/s)")
		self.upload_curve = self.upload_plot.plot(pen='r')
		self.upload_data = []

		self.network_graph.nextRow()
		self.download_plot = self.network_graph.addPlot(title="Download (KB/s)")
		self.download_curve = self.download_plot.plot(pen='g')
		self.download_data = []

		self.network_monitor_layout.addWidget(self.network_graph)
		self.interface_info = QTextEdit()
		self.interface_info.setReadOnly(True)
		self.network_monitor_layout.addWidget(self.interface_info)
		self.tabs.addTab(self.network_monitor_tab, self.lang['tab_network_monitor'])

		self.about_tab = QWidget()
		self.about_layout = QVBoxLayout()
		self.about_tab.setLayout(self.about_layout)
		self.about_text = QTextEdit()
		self.about_text.setReadOnly(True)
		self.about_layout.addWidget(self.about_text)
		self.tabs.addTab(self.about_tab, self.lang['tab_about'])

		self.last_net = psutil.net_io_counters()
		self.update_texts()

	def init_graphs(self):
		self.timer = QTimer()
		self.timer.timeout.connect(self.update_graphs)
		self.timer.timeout.connect(self.update_system_info)
		self.timer.timeout.connect(self.update_network_activity)
		self.timer.timeout.connect(self.update_network_monitor)
		self.timer.start(1000)

	def update_graphs(self):
		self.cpu_data = self.cpu_data[-59:] + [psutil.cpu_percent()]
		self.ram_data = self.ram_data[-59:] + [psutil.virtual_memory().percent]
		self.cpu_curve.setData(self.cpu_data)
		self.ram_curve.setData(self.ram_data)

	def update_system_info(self):
		net = psutil.net_io_counters()
		boot = datetime.fromtimestamp(psutil.boot_time()).strftime('%Y-%m-%d %H:%M:%S')
		info = f"System Boot Time: {boot}\n"
		info += f"Total Sent: {net.bytes_sent / (1024**2):.2f} MB\n"
		info += f"Total Received: {net.bytes_recv / (1024**2):.2f} MB\n"
		info += f"\nCPU Cores: {psutil.cpu_count(logical=False)} Physical / {psutil.cpu_count()} Logical\n"
		info += f"CPU Usage: {psutil.cpu_percent()}%\n"
		info += f"RAM Usage: {psutil.virtual_memory().percent}%\n"
		info += f"Disk Usage: {psutil.disk_usage('/').percent}%\n"
		self.sys_info.setPlainText(info)

	def update_network_activity(self):
		net_info = "Active Network Connections:\n"
		for conn in psutil.net_connections(kind='inet'):
			laddr = f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else ""
			raddr = f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else ""
			net_info += f"PID: {conn.pid}, Status: {conn.status}, Local: {laddr}, Remote: {raddr}\n"

		try:
			sensors = psutil.sensors_temperatures()
			if sensors:
				net_info += "\nTemperatures:\n"
				for name, entries in sensors.items():
					for entry in entries:
						net_info += f"{name} - {entry.label or 'Unnamed'}: {entry.current}°C\n"
		except Exception:
			net_info += "\nTemperature sensors not available."

		self.net_info.setPlainText(net_info)

	def update_network_monitor(self):
		current_net = psutil.net_io_counters()
		upload_speed = (current_net.bytes_sent - self.last_net.bytes_sent) / 1024
		download_speed = (current_net.bytes_recv - self.last_net.bytes_recv) / 1024

		self.upload_data = self.upload_data[-59:] + [upload_speed]
		self.download_data = self.download_data[-59:] + [download_speed]
		self.upload_curve.setData(self.upload_data)
		self.download_curve.setData(self.download_data)

		self.last_net = current_net

		details = "Network Interfaces:\n"
		for name, stats in psutil.net_io_counters(pernic=True).items():
			details += f"{name}: Sent: {stats.bytes_sent / 1024:.1f} KB, Received: {stats.bytes_recv / 1024:.1f} KB\n"

		self.interface_info.setPlainText(details)

	def change_language(self):
		self.lang_code = self.lang_selector.currentData()
		self.lang = load_language(self.lang_code)
		self.update_texts()
		self.update_processes()

	def update_texts(self):
		self.setWindowTitle(self.lang['title'])
		self.search_bar.setPlaceholderText(self.lang['search'])
		self.refresh_btn.setText(self.lang['refresh'])
		self.kill_btn.setText(self.lang['kill'])
		self.inspect_btn.setText(self.lang['inspect'])
		self.renice_btn.setText(self.lang['renice'])

		self.table.setHorizontalHeaderLabels(
			self.lang['columns'] + [
				self.lang.get('start_time_col', "Start Time"),
				self.lang.get('path_col', "Path"),
				self.lang.get('threads_col', "Threads")
			]
		)
		self.tabs.setTabText(0, self.lang['tab_performance'])
		self.tabs.setTabText(1, self.lang['tab_processes'])
		self.tabs.setTabText(2, self.lang['tab_system_info'])
		self.tabs.setTabText(3, self.lang['tab_network_sensors'])
		self.tabs.setTabText(4, self.lang['tab_network_monitor'])
		self.tabs.setTabText(5, self.lang['tab_about'])

		self.about_text.setPlainText(self.lang['about_text'])

	def update_processes(self):
		search = self.search_bar.text().lower()
		self.table.setRowCount(0)
		for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'username', 'create_time', 'exe', 'num_threads']):
			try:
				name = proc.info.get('name', '') or ''
				if search in name.lower():
					row = self.table.rowCount()
					self.table.insertRow(row)
					self.table.setItem(row, 0, QTableWidgetItem(str(proc.info.get('pid', 'N/A'))))
					self.table.setItem(row, 1, QTableWidgetItem(name))
					self.table.setItem(row, 2, QTableWidgetItem(f"{proc.info.get('cpu_percent', 0.0):.1f}"))
					self.table.setItem(row, 3, QTableWidgetItem(f"{proc.info.get('memory_percent', 0.0):.1f}"))
					self.table.setItem(row, 4, QTableWidgetItem(proc.info.get('username', 'N/A')))

					try:
						start = datetime.fromtimestamp(proc.create_time()).strftime('%Y-%m-%d %H:%M:%S')
					except (psutil.AccessDenied, OSError, ValueError):
						start = "N/A"
					self.table.setItem(row, 5, QTableWidgetItem(start))

					try:
						path = proc.exe() if proc.exe() else "N/A"
					except (psutil.AccessDenied, psutil.NoSuchProcess, OSError):
						path = "Permission Denied / N/A"
					self.table.setItem(row, 6, QTableWidgetItem(path))

					try:
						threads = str(proc.num_threads())
					except (psutil.AccessDenied, psutil.NoSuchProcess, OSError):
						threads = "N/A"
					self.table.setItem(row, 7, QTableWidgetItem(threads))

			except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
				continue
			except Exception:
				continue

	def kill_selected_process(self):
		row = self.table.currentRow()
		if row == -1:
			QMessageBox.warning(self, self.lang['title'], self.lang.get('select_process_warning', "Please select a process to kill."))
			return
		pid_item = self.table.item(row, 0)
		if not pid_item:
			QMessageBox.warning(self, self.lang['title'], self.lang.get('invalid_process_warning', "Invalid process selected."))
			return
		try:
			pid = int(pid_item.text())
			proc = psutil.Process(pid)
			proc.kill()
			self.update_processes()
		except psutil.NoSuchProcess:
			QMessageBox.warning(self, self.lang['title'], self.lang.get('no_such_process_error', "Process no longer exists."))
			self.update_processes()
		except psutil.AccessDenied:
			QMessageBox.critical(self, self.lang['title'], self.lang.get('permission_denied_error', "Permission denied to kill this process. Try running as administrator/root."))
		except Exception as e:
			QMessageBox.critical(self, self.lang['title'], self.lang.get('kill_error', "An error occurred while trying to kill the process: {e}").format(e=e))

	def renice_process(self):
		row = self.table.currentRow()
		if row == -1:
			return
		pid = int(self.table.item(row, 0).text())
		value, ok = QInputDialog.getInt(self, "Change Priority", "Nice Value (-20 to 19):", 0, -20, 19)
		if ok:
			try:
				psutil.Process(pid).nice(value)
			except Exception as e:
				QMessageBox.critical(self, "Error", f"Failed to renice: {e}")

	def inspect_process(self):
		row = self.table.currentRow()
		if row == -1:
			return
		pid = int(self.table.item(row, 0).text())
		try:
			proc = psutil.Process(pid)
			info = f"PID: {proc.pid}\nName: {proc.name()}\nExe: {proc.exe()}\nStatus: {proc.status()}\nThreads: {proc.num_threads()}\n"
			info += f"Open Files: {[f.path for f in proc.open_files()]}\n"
			info += f"Connections: {proc.net_connections()}\n"
			QMessageBox.information(self, "Process Details", info)
		except Exception as e:
			QMessageBox.critical(self, "Error", f"Failed to inspect: {e}")

if __name__ == "__main__":
	app = QApplication(sys.argv)
	icon_path = '/usr/share/icons/hicolor/256x256/apps/hel-process.png'
	if os.path.exists(icon_path):
		app.setWindowIcon(QIcon(icon_path))

	window = ProcessManager()
	window.show()
	sys.exit(app.exec_())
