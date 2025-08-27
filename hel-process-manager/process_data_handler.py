import psutil
from datetime import datetime
from PyQt5.QtWidgets import QTableWidgetItem, QMessageBox
from PyQt5.QtCore import Qt

class ProcessDataHandler:
    def update_processes(self):
        search_text = self.search_bar.text().lower()
        self.table.setRowCount(0)
        processes_data = []

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
                if not path_str or path_str == self.lang.get('not_available', 'N/A'):
                    try:
                        path_str = proc.exe() if proc.exe() else self.lang.get('not_available', 'N/A')
                    except (psutil.AccessDenied, psutil.NoSuchProcess, OSError):
                        path_str = self.lang.get('permission_denied', "Permission Denied / N/A")

                processes_data.append({
                    'pid': pid, 'name': name, 'cpu': cpu_percent, 'mem': mem_percent,
                    'user': username, 'ppid': ppid, 'start_time': start_time_str,
                    'path': path_str, 'threads': num_threads, 'status': status,
                    'proc_object': proc
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
            except Exception as e:
                print(f"Error processing process info: {e}")
                continue

        self.table.setSortingEnabled(False)
        for row_data in processes_data:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(row_data['pid'])))
            self.table.setItem(row, 1, QTableWidgetItem(row_data['name']))
            self.table.setItem(row, 2, QTableWidgetItem(f"{row_data['cpu']:.1f}"))
            self.table.setItem(row, 3, QTableWidgetItem(f"{row_data['mem']:.1f}"))
            self.table.setItem(row, 4, QTableWidgetItem(row_data['user']))
            self.table.setItem(row, 5, QTableWidgetItem(str(row_data['ppid'])))
            self.table.setItem(row, 6, QTableWidgetItem(row_data['start_time']))
            self.table.setItem(row, 7, QTableWidgetItem(row_data['path']))
            self.table.setItem(row, 8, QTableWidgetItem(str(row_data['threads'])))
            self.table.setItem(row, 9, QTableWidgetItem(row_data['status']))
            self.table.item(row, 0).setData(Qt.UserRole, row_data['proc_object'])
        self.table.setSortingEnabled(True)

    def sort_processes_table(self, logical_index):
        self.table.sortItems(logical_index, Qt.AscendingOrder)

    def get_selected_process_object(self):
        row = self.table.currentRow()
        if row == -1:
            QMessageBox.warning(self, self.lang['title'], self.lang.get('select_process_warning', "Please select a process."))
            return None
        item = self.table.item(row, 0)
        if not item:
            QMessageBox.warning(self, self.lang['title'], self.lang.get('invalid_process_warning', "Invalid process selected."))
            return None
        proc_obj = item.data(Qt.UserRole)
        if proc_obj is None:
            QMessageBox.warning(self, self.lang['title'], self.lang.get('invalid_process_warning', "Invalid process selected (no process object found)."))
            return None
        try:
            return psutil.Process(proc_obj.pid)
        except psutil.NoSuchProcess:
            QMessageBox.warning(self, self.lang['title'], self.lang.get('no_such_process_error', "Process no longer exists."))
            self.update_processes()
            return None
        except Exception as e:
            QMessageBox.critical(self, self.lang['title'], self.lang.get('general_error', "An unexpected error occurred: {e}").format(e=e))
            return None
