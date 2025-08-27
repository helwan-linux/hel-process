import os
import importlib.util

def load_language(lang_code):
    lang_path = os.path.join(os.path.dirname(__file__), 'lang', f'{lang_code}.py')
    if not os.path.exists(lang_path):
        lang_path = os.path.join(os.path.dirname(__file__), 'lang', 'en.py')
        if not os.path.exists(lang_path):
            raise FileNotFoundError(f"English language file not found at {lang_path}. Please create a 'lang' folder with 'en.py'.")
    spec = importlib.util.spec_from_file_location("lang", lang_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.lang
