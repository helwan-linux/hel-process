import psutil
import os
import sys
from PyQt5.QtWidgets import QMessageBox, QInputDialog, QDialog, QVBoxLayout, QCheckBox, QGridLayout, QPushButton, QLabel

class ProcessActions:
    def kill_selected_process(self):
        proc = self.get_selected_process_object()
        if proc is None:
            return
        try:
            reply = QMessageBox.question(self, self.lang['title'], self.lang.get('confirm_kill', "Are you sure you want to kill process {pid} ({name})?").format(pid=proc.pid, name=proc.name()), QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
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
            value, ok = QInputDialog.getInt(self, self.lang.get('renice_title', "Change Priority"), self.lang.get('renice_prompt', "Nice Value (-20 to 19): Current: {current}").format(current=current_nice), current_nice, -20, 19)
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
        try:
            current_affinity = proc.cpu_affinity()
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            QMessageBox.critical(self, self.lang['title'], self.lang.get('permission_denied_error', "Permission denied to get CPU affinity. Try running as administrator/root."))
            return
        except Exception as e:
            QMessageBox.critical(self, self.lang.get('general_error', "Error: {e}").format(e=e))
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
            grid_layout.addWidget(checkbox, i // 4, i % 4)
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
        priority_names = {v: k for k, v in io_priorities.items()}
        dialog = QDialog(self)
        dialog.setWindowTitle(self.lang.get('set_io_priority_title', "Set I/O Priority"))
        layout = QVBoxLayout(dialog)
        try:
            current_io_priority = proc.ionice(as_dict=False)
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
            elif sys.platform == "darwin":
                os.system(f"open {os.path.dirname(exe_path)}")
            else:
                os.system(f"xdg-open {os.path.dirname(exe_path)}")
        except (psutil.AccessDenied, psutil.NoSuchProcess, OSError) as e:
            QMessageBox.critical(self, self.lang['title'], self.lang.get('permission_denied_or_no_path', "Permission denied or path not accessible: {e}").format(e=e))
        except Exception as e:
            QMessageBox.critical(self, self.lang['title'], self.lang.get('open_location_error', "Error opening file location: {e}").format(e=e))
