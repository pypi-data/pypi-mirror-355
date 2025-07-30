import logging
import platform
import time
import datetime
import os
from typing import Any, Callable, Optional
from colorama import Fore, Style
from rich.console import Console
from rich.text import Text
from playsound import playsound
import locale
import socket
import random

console = Console()

# Logging setup
logger = logging.getLogger("smartsys")
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')

file_handler = logging.FileHandler("smartsys.log")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# --- Colored Logging ---
def log_info(msg: str):
    logger.info(msg)
    console.print(f"{Fore.CYAN}[INFO]{Style.RESET_ALL} {msg}")

def log_warning(msg: str):
    logger.warning(msg)
    console.print(f"{Fore.YELLOW}[WARNING]{Style.RESET_ALL} {msg}")

def log_critical(msg: str):
    logger.critical(msg)
    console.print(f"{Fore.RED}[CRITICAL]{Style.RESET_ALL} {msg}")

# --- Alert System ---
def play_alert_sound():
    try:
        sound_file = os.path.join(os.path.dirname(__file__), "alert.mp3")
        if os.path.exists(sound_file):
            playsound(sound_file)
        else:
            log_warning("Alert sound file not found.")
    except Exception as e:
        log_warning(f"Failed to play alert sound: {e}")

def print_alert_message(message: str):
    console.print(Text(message, style="bold red"))

# --- Time & Locale Tools ---
def get_local_time() -> str:
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())

def get_uptime_seconds() -> int:
    return int(time.time() - psutil.boot_time())

def format_timedelta(seconds: int) -> str:
    return str(datetime.timedelta(seconds=seconds))

def get_locale_info() -> str:
    loc = locale.getdefaultlocale()
    return f"{loc[0]} ({loc[1]})" if loc else "Unknown"

# --- System Utilities ---
def is_windows() -> bool:
    return platform.system().lower() == 'windows'

def is_linux() -> bool:
    return platform.system().lower() == 'linux'

def get_hostname() -> str:
    return socket.gethostname()

def is_online(host="8.8.8.8", port=53, timeout=3) -> bool:
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except Exception:
        return False

# --- Formatter Tools ---
def format_bytes(size: int) -> str:
    # Manual alternative to humanize
    for unit in ['B','KB','MB','GB','TB']:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} PB"

def format_percentage(value: float) -> str:
    return f"{value:.1f}%"

# --- Retry Decorator ---
def retry(times: int = 3, delay: float = 1.0):
    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(times):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    log_warning(f"Retry {attempt + 1}/{times} failed: {e}")
                    last_exception = e
                    time.sleep(delay)
            raise last_exception
        return wrapper
    return decorator

# --- Debug Helper ---
def debug_data(title: str, data: Any):
    console.print(f"[bold green]{title}[/bold green]")
    console.print(data)

# --- Random Messages ---
def random_health_tip() -> str:
    tips = [
        "💧 Stay hydrated!",
        "🧘‍♀️ Take a break and breathe.",
        "🍎 Eat something healthy today.",
        "🚶‍♂️ Stretch or take a quick walk.",
        "🧠 Mental health matters too."
    ]
    return random.choice(tips)

# --- Enhanced Alert Logic ---
def notify_if_overload(resource: str, value: float, threshold: float):
    if value > threshold:
        msg = f"{resource} usage is {value:.1f}%, which is above the threshold of {threshold}%!"
        log_critical(msg)
        print_alert_message(msg)
        play_alert_sound()

def Licence():
    print("""MIT License Copyright (c) © 2025 Adam Alcander et Eden. All Rights Reserved . 
             Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), 
             to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, 
             and to permit persons to whom the Software is furnished to do so, subject to the following conditions:The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
             THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
             IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.""") 

import psutil

def get_cpu_usage():
    return psutil.cpu_percent(interval=1)

def get_memory_usage():
    return psutil.virtual_memory().percent

def get_disk_usage():
    return psutil.disk_usage('/').percent


# --- __main__ test run (optional) ---
if __name__ == "__main__":
    log_info("Utils test start.")
    print(f"Local Time: {get_local_time()}")
    print(f"Uptime: {format_timedelta(get_uptime_seconds())}")
    print(f"Locale: {get_locale_info()}")
    print(f"Online: {is_online()}")
    print(f"Health Tip: {random_health_tip()}")
    notify_if_overload("CPU", 88.5, 80)


