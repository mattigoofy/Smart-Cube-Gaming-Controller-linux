import os
import threading

from python_utils.binds_mode import run_binds_mode
from python_utils.browser import launch_chromium
from python_utils.console_mode import run_console_mode
from python_utils.server import (
    binds_path_changed_event,
    clear_binds_buffer,
    get_binds_path,
    mode_queue,
    start_server,
)

HTML_DIR = os.path.join("src", "HTML-JS")
BINDS_ROOT = os.path.join("binds")
BINDS_PATH = os.path.join(BINDS_ROOT, "full_huffman_mapping.txt")
PORT = 8766
URL = f"http://localhost:{PORT}/index.html"

start_server(HTML_DIR, BINDS_PATH, BINDS_ROOT, port=PORT)
browser = launch_chromium(URL)

stop_event = threading.Event()
active_thread = None

try:
    # start on binds
    active_thread = threading.Thread(
        target=run_binds_mode,
        args=(
            stop_event,
            get_binds_path(),
        ),
        daemon=True,
    )
    active_thread.start()
    while True:
        while not binds_path_changed_event.is_set() and mode_queue.empty():
            if stop_event.wait(0.05):
                break

        mode = None
        if binds_path_changed_event.is_set():
            binds_path_changed_event.clear()
            mode = "BINDS"
        elif not mode_queue.empty():
            mode = mode_queue.get()  # frontend mode switch

        if mode is None:
            continue

        if active_thread and active_thread.is_alive():
            stop_event.set()
            active_thread.join(timeout=2)
            stop_event.clear()

        if mode == "BINDS":
            active_thread = threading.Thread(
                target=run_binds_mode,
                args=(
                    stop_event,
                    get_binds_path(),
                ),
                daemon=True,
            )
        elif mode == "CONSOLE":
            clear_binds_buffer()
            active_thread = threading.Thread(
                target=run_console_mode, args=(stop_event,), daemon=True
            )
        active_thread.start()
finally:
    browser.terminate()
