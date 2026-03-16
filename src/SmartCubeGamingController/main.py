import os
import queue
import threading
import time

from binds.binds import BindingsConfiguration
from binds.moves import MoveHistory, MoveList
from binds.parsers import Parser
from python_utils.binds_mode import run_binds_mode
from python_utils.browser import launch_chromium
from python_utils.console import Console
from python_utils.console_mode import run_console_mode
from server.server import Server, ServerSettings

HTML_DIR = os.path.join("src", "HTML-JS")
BINDS_ROOT = os.path.join("binds")
BINDS_PATH = os.path.join(BINDS_ROOT, "config.yml")
PORT = 8766
URL = f"http://localhost:{PORT}/index.html"


try:
    mode = "BIND"

    server = Server(ServerSettings())
    server.start()

    bind_parser = Parser()
    binds_config = bind_parser.parse(server.binds_path)
    move_history = MoveHistory(binds_config.idle_time, time.time())

    console = Console()
    server.cursor_state = console.keyboard.cursor

    move = None

    browser = launch_chromium(URL)

    while True:
        try:
            mode = server.mode_queue.get(timeout=0.1)
        except queue.Empty:
            pass

        try:
            move = server.move_queue.get(timeout=0.1)
        except queue.Empty:
            continue

        if mode == "BIND":
            move_history.append(move)
            match: MoveList = move_history.find_match(binds_config.bindings)
            server.binds_buffer = move_history.to_str()

            if match:
                print(match)
                commands = binds_config.bindings.bindings.get(match)
                commands.execute()
                move_history.clear()

            move_history.set_time(time.time())

        elif mode == "CONSOLE":
            console.handle_move(move)
            server.cursor_state = console.keyboard.cursor

        else:
            mode = "BIND"


finally:
    browser.terminate()

# # stop_event = threading.Event()
# active_thread = None

# try:
#     # start on binds
#     active_thread = threading.Thread(
#         target=run_binds_mode,
#         args=(
#             stop_event,
#             get_binds_path(),
#         ),
#         daemon=True,
#     )
#     active_thread.start()
#     while True:
#         while not binds_path_changed_event.is_set() and mode_queue.empty():
#             if stop_event.wait(0.05):
#                 break

#         mode = None
#         if binds_path_changed_event.is_set():
#             binds_path_changed_event.clear()
#             mode = "BINDS"
#         elif not mode_queue.empty():
#             mode = mode_queue.get()  # frontend mode switch

#         if mode is None:
#             continue

#         if active_thread and active_thread.is_alive():
#             stop_event.set()
#             active_thread.join(timeout=2)
#             stop_event.clear()

#         if mode == "BINDS":
#             active_thread = threading.Thread(
#                 target=run_binds_mode,
#                 args=(
#                     stop_event,
#                     get_binds_path(),
#                 ),
#                 daemon=True,
#             )
#         elif mode == "CONSOLE":
#             clear_binds_buffer()
#             active_thread = threading.Thread(
#                 target=run_console_mode, args=(stop_event,), daemon=True
#             )
#         active_thread.start()
# finally:
#     browser.terminate()
