import sys
from PyQt5.QtWidgets import QMessageBox, QListWidgetItem
from PyQt5.QtCore import Qt

# Import the correct platform-specific module
if sys.platform == "linux":
    from startup_linux import get_startup_items, set_startup_status
elif sys.platform == "win32":
    from startup_windows import get_startup_items, set_startup_status
else:
    # A fallback for other systems like macOS
    def get_startup_items():
        return []
    def set_startup_status(item, enable):
        return False, "Unsupported OS for this feature."

class StartupProgramsHandler:
    def update_startup_programs(self):
        self.startup_list.clear()
        try:
            items = get_startup_items()
            if not items:
                info_text = self.lang.get('no_startup_items', "No startup programs found for this platform.")
                self.startup_list.addItem(info_text)
                self.startup_list.item(0).setFlags(Qt.NoItemFlags)
                self.disable_startup_btn.setEnabled(False)
                self.enable_startup_btn.setEnabled(False)
            else:
                for item in items:
                    list_item = QListWidgetItem(item.name)
                    list_item.setData(Qt.UserRole, item)
                    list_item.setToolTip(item.command)
                    self.startup_list.addItem(list_item)
                self.disable_startup_btn.setEnabled(True)
                # Note: Windows set_startup_status is a placeholder, so enable button is disabled there
                self.enable_startup_btn.setEnabled(True and sys.platform != "win32")

        except Exception as e:
            self.startup_list.addItem(self.lang.get('startup_error', "Error retrieving startup programs: {e}").format(e=e))
            self.startup_list.item(0).setFlags(Qt.NoItemFlags)
            self.disable_startup_btn.setEnabled(False)
            self.enable_startup_btn.setEnabled(False)

    def set_startup_status(self, enable):
        selected_item = self.startup_list.currentItem()
        if not selected_item:
            QMessageBox.warning(self, self.lang['title'], self.lang.get('select_startup_item', "Please select a startup program."))
            return
        
        startup_item_obj = selected_item.data(Qt.UserRole)
        if not startup_item_obj:
            QMessageBox.warning(self, self.lang['title'], self.lang.get('invalid_startup_item', "Invalid startup item selected."))
            return
            
        success, message = set_startup_status(startup_item_obj, enable)
        if success:
            action = self.lang.get('enabled', 'enabled') if enable else self.lang.get('disabled', 'disabled')
            QMessageBox.information(self, self.lang['title'], self.lang.get('startup_success', "Startup item '{name}' has been {action} successfully.").format(name=startup_item_obj.name, action=action))
            self.update_startup_programs()
        else:
            QMessageBox.critical(self, self.lang['title'], self.lang.get('startup_error_mod', "Could not modify startup item '{name}': {msg}").format(name=startup_item_obj.name, msg=message))
