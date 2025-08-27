import os
import configparser
from startup_common import StartupItem

def get_startup_items():
    """
    Scans standard XDG autostart directories for startup applications on Linux.
    """
    items = []
    
    # User-specific autostart directory
    user_autostart_dir = os.path.join(os.path.expanduser('~'), '.config', 'autostart')
    if os.path.isdir(user_autostart_dir):
        for filename in os.listdir(user_autostart_dir):
            if filename.endswith('.desktop'):
                file_path = os.path.join(user_autostart_dir, filename)
                try:
                    config = configparser.ConfigParser(interpolation=None)
                    config.read(file_path)
                    if 'Desktop Entry' in config:
                        name = config['Desktop Entry'].get('Name', filename)
                        command = config['Desktop Entry'].get('Exec', '')
                        enabled = True # Assume it's enabled if it's there
                        if 'Hidden' in config['Desktop Entry']:
                            enabled = not config['Desktop Entry'].getboolean('Hidden')
                        
                        item = StartupItem(name, command, enabled, path=file_path)
                        item.is_user_item = True
                        items.append(item)
                except Exception:
                    continue
    
    # System-wide autostart directory
    system_autostart_dir = '/etc/xdg/autostart'
    if os.path.isdir(system_autostart_dir):
        for filename in os.listdir(system_autostart_dir):
            if filename.endswith('.desktop'):
                file_path = os.path.join(system_autostart_dir, filename)
                try:
                    config = configparser.ConfigParser(interpolation=None)
                    config.read(file_path)
                    if 'Desktop Entry' in config:
                        name = config['Desktop Entry'].get('Name', filename)
                        command = config['Desktop Entry'].get('Exec', '')
                        enabled = True # Assume it's enabled if it's there
                        if 'Hidden' in config['Desktop Entry']:
                            enabled = not config['Desktop Entry'].getboolean('Hidden')
                        
                        item = StartupItem(name, command, enabled, path=file_path)
                        item.is_user_item = False
                        items.append(item)
                except Exception:
                    continue

    return items

def set_startup_status(item, enable):
    """
    Sets the enabled status of a startup item by modifying its .desktop file.
    """
    if not item or not item.path or not os.path.exists(item.path):
        return False, "Item not found."

    try:
        config = configparser.ConfigParser(interpolation=None)
        config.read(item.path)
        if 'Desktop Entry' not in config:
            return False, "Invalid .desktop file format."

        # Set or update the Hidden key
        if enable:
            if config['Desktop Entry'].get('Hidden', '').lower() == 'true':
                del config['Desktop Entry']['Hidden']
        else:
            config['Desktop Entry']['Hidden'] = 'true'

        with open(item.path, 'w') as configfile:
            config.write(configfile)
        
        return True, "Success."

    except Exception as e:
        return False, str(e)
