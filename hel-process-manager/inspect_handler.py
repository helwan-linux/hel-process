import psutil
from PyQt5.QtWidgets import QMessageBox

class InspectHandler:
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
            open_files_info = []
            try:
                for f in proc.open_files():
                    open_files_info.append(f.path)
                info += self.lang.get('inspect_open_files', "\nOpen Files ({count}):\n{files}\n").format(
                    count=len(open_files_info), files='\n'.join(open_files_info) if open_files_info else self.lang.get('none', 'None'))
            except psutil.AccessDenied:
                info += self.lang.get('inspect_open_files_denied', "\nOpen Files: Permission Denied\n")
            except Exception as e:
                info += self.lang.get('inspect_open_files_error', "\nOpen Files: Error retrieving ({error})\n").format(error=e)
            connections_info = []
            try:
                for conn in proc.connections():
                    laddr = f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else ""
                    raddr = f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else ""
                    connections_info.append(f"  {conn.status} Local: {laddr}, Remote: {raddr}")
                info += self.lang.get('inspect_connections', "\nConnections ({count}):\n{conns}\n").format(
                    count=len(connections_info), conns='\n'.join(connections_info) if connections_info else self.lang.get('none', 'None'))
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
