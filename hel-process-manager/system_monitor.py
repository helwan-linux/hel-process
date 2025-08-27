import psutil
from datetime import datetime

class SystemMonitor:
    def update_system_info(self):
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

        gpu_info_text = self.lang.get('gpu_info_header', "\nGPU Information:\n")
        try:
            gpu_info_text += self.lang.get('gpu_info_not_supported', "GPU monitoring not directly supported by psutil on this OS.\n")
        except Exception as e:
            gpu_info_text += self.lang.get('gpu_info_error', "Error retrieving GPU info: {error}\n").format(error=e)
        info += gpu_info_text

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

        disk_details = self.lang.get('disk_details_header', "Disk Partitions:\n")
        try:
            partitions = psutil.disk_partitions()
            for part in partitions:
                disk_details += self.lang.get('disk_partition_format', "  Device: {device}, Mountpoint: {mountpoint}, Filesystem: {fstype}\n").format(device=part.device, mountpoint=part.mountpoint, fstype=part.fstype)
                try:
                    usage = psutil.disk_usage(part.mountpoint)
                    disk_details += self.lang.get('disk_usage_format', "    Total: {total_gb:.2f} GB, Used: {used_gb:.2f} GB, Free: {free_gb:.2f} GB, Used: {percent}%\n").format(total_gb=usage.total / (1024**3), used_gb=usage.used / (1024**3), free_gb=usage.free / (1024**3), percent=usage.percent)
                except Exception as e:
                    disk_details += self.lang.get('disk_usage_error', "    Error getting usage: {error}\n").format(error=e)
        except Exception as e:
            disk_details += self.lang.get('disk_details_error', "Error retrieving disk partitions: {error}\n").format(error=e)
        self.disk_info.setPlainText(disk_details)

    def update_status_bar(self):
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        disk = psutil.disk_usage('/').percent
        status_text = self.lang.get('status_bar_format', "CPU: {cpu}% | RAM: {ram}% | Disk: {disk}%").format(cpu=cpu, ram=ram, disk=disk)
        self.status_bar.setText(status_text)
