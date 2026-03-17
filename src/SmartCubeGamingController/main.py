import os
import queue
import threading
import time

from SmartCubeGamingController.binds.moves import MoveHistory, MoveList
from SmartCubeGamingController.binds.parsers import Parser
from SmartCubeGamingController.server.browser import launch_chromium
from SmartCubeGamingController.python_utils.console import Console
from SmartCubeGamingController.server.server import Server, ServerSettings

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
