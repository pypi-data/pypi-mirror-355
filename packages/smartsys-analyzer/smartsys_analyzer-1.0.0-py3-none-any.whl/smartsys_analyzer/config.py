import os
import platform
import json
import pathlib
from typing import Dict, Any, Optional
from datetime import datetime
from colorama import Fore

# --- System Metadata ---
PROJECT_NAME = "SmartSys Analyzer"
VERSION = "1.0.0"
AUTHOR = "Adam Alcander et Eden"
LICENSE = "MIT"
GITHUB_URL = "https://github.com/yourusername/smartsys-analyzer"

# --- Default Thresholds ---
DEFAULT_THRESHOLD: Dict[str, int] = {
    "cpu": 80,
    "memory": 75,
    "disk": 85
}

# --- ANSI Style Color Configuration ---
STYLE_INFO = Fore.CYAN
STYLE_WARNING = Fore.YELLOW
STYLE_CRITICAL = Fore.RED
STYLE_SUCCESS = Fore.GREEN
STYLE_RESET = Fore.RESET

# --- OS Detection ---
IS_WINDOWS = platform.system().lower() == "windows"
IS_LINUX = platform.system().lower() == "linux"
IS_MAC = platform.system().lower() == "darwin"

OS_NAME = platform.system()
OS_RELEASE = platform.release()
OS_VERSION = platform.version()

# --- Directory Config ---
BASE_DIR = pathlib.Path(__file__).parent
LOG_FILE = BASE_DIR / "smartsys.log"
CONFIG_FILE_JSON = BASE_DIR / "settings.json"
CONFIG_FILE_YAML = BASE_DIR / "settings.yaml"  # if PyYAML available

# --- Language Support (extensible) ---
LANGUAGES = {
    "en": "English",
    "id": "Bahasa Indonesia",
    "zh-hans": "简体中文",
    "ar": "العربية"
}

CURRENT_LANG = "en"

# --- Time Config ---
TIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"

def now() -> str:
    return datetime.now().strftime(TIME_FORMAT)

def today() -> str:
    return datetime.now().strftime(DATE_FORMAT)

# --- Load JSON Config ---
def load_json_config(filepath: Optional[pathlib.Path] = None) -> Dict[str, Any]:
    path = filepath or CONFIG_FILE_JSON
    if not path.exists():
        return {}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"{STYLE_WARNING}[WARNING] Failed to load JSON config: {e}{STYLE_RESET}")
        return {}

# --- Save JSON Config ---
def save_json_config(data: Dict[str, Any], filepath: Optional[pathlib.Path] = None):
    path = filepath or CONFIG_FILE_JSON
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"{STYLE_CRITICAL}[ERROR] Failed to save JSON config: {e}{STYLE_RESET}")

# --- Global Runtime Flags ---
IS_DEBUG_MODE = False
IS_SCHEDULED = False
IS_OFFLINE_MODE = False

def toggle_debug():
    global IS_DEBUG_MODE
    IS_DEBUG_MODE = not IS_DEBUG_MODE

def set_language(lang_code: str):
    global CURRENT_LANG
    if lang_code in LANGUAGES:
        CURRENT_LANG = lang_code
    else:
        print(f"{STYLE_WARNING}Language '{lang_code}' not supported. Defaulting to English.{STYLE_RESET}")
        CURRENT_LANG = "en"

def show_config_summary():
    print(f"{STYLE_INFO}{'-'*30}")
    print(f"{PROJECT_NAME} v{VERSION}")
    print(f"Author   : {AUTHOR}")
    print(f"OS       : {OS_NAME} {OS_RELEASE}")
    print(f"Language : {LANGUAGES.get(CURRENT_LANG, 'Unknown')}")
    print(f"Debug    : {IS_DEBUG_MODE}")
    print(f"{'-'*30}{STYLE_RESET}")

# --- Extended Metadata ---
KEYWORDS = [
    "system", "monitor", "analyzer", "pydantic", "rich", "logging", "performance"
]

DESCRIPTION = (
    "SmartSys Analyzer is a powerful Python package that monitors CPU, memory, and disk "
    "usage in real-time with alerts, logs, visualization, and scheduling support."
)

# --- Default Template Configs ---
DEFAULT_JSON_CONFIG = {
    "threshold": DEFAULT_THRESHOLD,
    "language": CURRENT_LANG,
    "theme": "default",
    "debug": IS_DEBUG_MODE,
    "timestamp": now()
}

# --- __main__ test run ---
if __name__ == "__main__":
    print(">> Config Module Test")
    show_config_summary()
    print(">> Saving default config...")
    save_json_config(DEFAULT_JSON_CONFIG)
    print(">> Loading saved config...")
    config = load_json_config()
    print(config)
