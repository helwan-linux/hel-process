import os

class StartupItem:
    def __init__(self, name, command, enabled, path=None):
        self.name = name
        self.command = command
        self.enabled = enabled
        self.path = path # The file path, e.g., a .desktop file or a registry key name
        self.is_user_item = True # Assume user-level for now
    
    def __repr__(self):
        return f"StartupItem(name='{self.name}', enabled={self.enabled})"

def is_valid_startup_file(path):
    """
    Check if a file is a valid startup file (e.g., has .desktop extension and is a file).
    """
    return os.path.isfile(path) and (path.endswith('.desktop') or path.endswith('.lnk') or path.endswith('.vbs') or path.endswith('.url'))
