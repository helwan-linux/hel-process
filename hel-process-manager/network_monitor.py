import psutil

class NetworkMonitor:
    def update_network_activity(self):
        net_info_text = self.lang.get('net_info_connections', "Active Network Connections:\n")
        for conn in psutil.net_connections(kind='inet'):
            laddr = f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else ""
            raddr = f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else ""
            net_info_text += self.lang.get('net_conn_format', "PID: {pid}, Status: {status}, Local: {local}, Remote: {remote}\n").format(pid=conn.pid if conn.pid else 'N/A', status=conn.status, local=laddr, remote=raddr)

        try:
            sensors = psutil.sensors_temperatures()
            if sensors:
                net_info_text += self.lang.get('net_info_temps_header', "\nTemperatures:\n")
                for name, entries in sensors.items():
                    for entry in entries:
                        net_info_text += self.lang.get('net_info_temp_format', "{name} - {label}: {current}°C\n").format(name=name, label=entry.label or self.lang.get('unnamed_sensor', 'Unnamed'), current=entry.current)
            else:
                net_info_text += self.lang.get('no_temp_sensors', "\nTemperature sensors not available.\n")
        except Exception:
            net_info_text += self.lang.get('no_temp_sensors_error', "\nCould not retrieve temperature sensor data (permission or hardware issue).\n")

        self.net_info.setPlainText(net_info_text)

    def update_network_monitor(self):
        current_net = psutil.net_io_counters()
        upload_speed = (current_net.bytes_sent - self.last_net_bytes_sent) / 1024
        download_speed = (current_net.bytes_recv - self.last_net_bytes_recv) / 1024

        self.upload_data = self.upload_data[-59:] + [upload_speed]
        self.download_data = self.download_data[-59:] + [download_speed]
        self.upload_curve.setData(self.upload_data)
        self.download_curve.setData(self.download_data)

        self.last_net_bytes_sent = current_net.bytes_sent
        self.last_net_bytes_recv = current_net.bytes_recv

        details = self.lang.get('net_interfaces_header', "Network Interfaces:\n")
        for name, stats in psutil.net_io_counters(pernic=True).items():
            details += self.lang.get('net_interface_format', "{name}: Sent: {sent_kb:.1f} KB, Received: {recv_kb:.1f} KB\n").format(name=name, sent_kb=stats.bytes_sent / 1024, recv_kb=stats.bytes_recv / 1024)
        self.interface_info.setPlainText(details)
