from PyQt5.QtCore import QTimer
import psutil

class GraphHandler:
    def init_graphs(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_graphs)
        self.timer.timeout.connect(self.update_system_info)
        self.timer.timeout.connect(self.update_network_activity)
        self.timer.timeout.connect(self.update_network_monitor)
        self.timer.timeout.connect(self.update_disk_io_graph)
        self.timer.timeout.connect(self.update_status_bar)
        self.timer.start(1000)

    def update_graphs(self):
        self.cpu_data = self.cpu_data[-59:] + [psutil.cpu_percent()]
        self.ram_data = self.ram_data[-59:] + [psutil.virtual_memory().percent]
        self.cpu_curve.setData(self.cpu_data)
        self.ram_curve.setData(self.ram_data)

    def update_disk_io_graph(self):
        disk_io = psutil.disk_io_counters()
        if disk_io:
            read_speed = (disk_io.read_bytes - self.last_disk_read_bytes) / 1024
            write_speed = (disk_io.write_bytes - self.last_disk_write_bytes) / 1024

            self.disk_read_data = self.disk_read_data[-59:] + [read_speed]
            self.disk_write_data = self.disk_write_data[-59:] + [write_speed]
            self.disk_read_curve.setData(self.disk_read_data)
            self.disk_write_curve.setData(self.disk_write_data)

            self.last_disk_read_bytes = disk_io.read_bytes
            self.last_disk_write_bytes = disk_io.write_bytes
        else:
            self.disk_read_plot.setTitle(self.lang.get('disk_io_not_available', "Disk I/O Not Available"))
            self.disk_write_plot.setTitle("")
