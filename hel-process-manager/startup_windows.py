import winreg
from startup_common import StartupItem

def get_startup_items():
    """
    Scans the Windows Registry for startup programs.
    """
    items = []
    
    # Paths in the Registry for startup programs
    user_key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    system_key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
    
    # User-level startup programs
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, user_key_path) as key:
            i = 0
            while True:
                try:
                    name, command, _ = winreg.EnumValue(key, i)
                    item = StartupItem(name, command, enabled=True)
                    item.is_user_item = True
                    items.append(item)
                    i += 1
                except OSError:
                    break
    except Exception:
        pass
        
    # System-level startup programs
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, system_key_path) as key:
            i = 0
            while True:
                try:
                    name, command, _ = winreg.EnumValue(key, i)
                    item = StartupItem(name, command, enabled=True)
                    item.is_user_item = False
                    items.append(item)
                    i += 1
                except OSError:
                    break
    except Exception:
        pass
        
    # Note: .lnk files in the Startup folders are not handled here.
    # This is a simplified example focusing on the registry.

    return items

def set_startup_status(item, enable):
    """
    Disabling/enabling in the registry is complex. This is a placeholder.
    A common method is to move the entry to a different key, but this is
    not a standard practice and can be dangerous.
    """
    # This feature is not implemented to avoid potential registry issues.
    # A robust solution would involve moving the key to a 'RunOnce' key or
    # a custom key for re-enabling, but this is risky.
    return False, "Modifying Windows registry for startup is not supported in this example."
