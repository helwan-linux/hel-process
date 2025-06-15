# lang/en.py
lang = {
    "title": "Helwan Process Manager",
    "language": "Language",
    "search": "Search...",
    "refresh": "Refresh",
    "kill": "Kill",
    "tab_performance": "Performance",
    "tab_processes": "Processes",
    "tab_system_info": "System Info",
    "tab_network_sensors": "Network & Sensors",
    "tab_network_monitor": "Network Monitor",
    "tab_about": "About",
    "columns": ["PID", "Name", "CPU %", "Memory %", "User"],
    "start_time_col": "Start Time",  # Added
    "path_col": "Path",              # Added
    "threads_col": "Threads",        # Added
    "about_text": (
        "Helwan Process Manager\n"
        "Version 1.0\n"
        "Developed by SMA Coding Team\n\n"
        "This tool provides real-time monitoring of CPU, RAM, processes, network activity,\n"
        "temperature sensors, and more — with multi-language support and advanced features."
    ),
    "select_process_warning": "Please select a process to kill.",
    "invalid_process_warning": "Invalid process selected.",
    "no_such_process_error": "Process no longer exists.",
    "permission_denied_error": "Permission denied to kill this process. Try running as administrator/root.",
    "kill_error": "An error occurred while trying to kill the process: {e}"
}
