import os
import threading

from python_utils.binds_mode import run_binds_mode
from python_utils.browser import launch_chromium
from python_utils.console_mode import run_console_mode
from python_utils.server import mode_queue, start_server

HTML_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "HTML-JS")
BINDS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "binds.txt")
URL = "http://localhost:8765/index.html"

start_server(HTML_DIR, BINDS_PATH)
browser = launch_chromium(URL)

stop_event = threading.Event()
active_thread = None

try:
    while True:
        mode = mode_queue.get()  # blocks until the frontend chooses a mode

        if active_thread and active_thread.is_alive():
            stop_event.set()
            active_thread.join(timeout=2)
            stop_event.clear()

        if mode == "BINDS":
            active_thread = threading.Thread(
                target=run_binds_mode, args=(stop_event,), daemon=True
            )
        elif mode == "CONSOLE":
            active_thread = threading.Thread(
                target=run_console_mode, args=(stop_event,), daemon=True
            )
        active_thread.start()
finally:
    browser.terminate()
