import sys
import os
from PyQt5.QtWidgets import QApplication, QMessageBox

# Import the main application class and language loader
from process_manager import ProcessManager
from language_loader import load_language

if __name__ == "__main__":
    # --- Check for essential files/folders ---
    if not os.path.exists('lang'):
        print("Warning: 'lang' folder not found. Please create it and place language files inside.")
    if not os.path.exists(os.path.join('lang', 'en.py')):
        print("Warning: 'lang/en.py' not found. Please create this file with English translations.")

    # Ensure 'logo' folder exists for the icon
    if not os.path.exists('logo'):
        os.makedirs('logo')
    if not os.path.exists(os.path.join('logo', 'icon.png')):
        print("Warning: 'logo/icon.png' not found. Window icon might not be displayed.")

    try:
        # Load default language to handle potential errors
        lang = load_language('en')
    except FileNotFoundError as e:
        QMessageBox.critical(None, "Error", str(e) + "\n" + "Ensure 'lang' folder exists with 'en.py' inside.")
        sys.exit(1)

    app = QApplication(sys.argv)
    
    # Load Helwan Style (QSS)
    style_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "helwan_style.qss")
    if os.path.exists(style_path):
        with open(style_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
            
    window = ProcessManager()
    window.show()
    sys.exit(app.exec_())
