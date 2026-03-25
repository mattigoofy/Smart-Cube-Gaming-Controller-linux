import queue
import time

from SmartCubeGamingController.modes.binds.moves import MoveHistory, MoveList, MoveType
from SmartCubeGamingController.modes.binds.parsers import Parser
from SmartCubeGamingController.modes.console.console import Console
from SmartCubeGamingController.server import Server, ServerSettings


class App:
    def __init__(self) -> None:
        settings: ServerSettings = ServerSettings()
        self._server: Server = Server(settings)

        self._bindings_config = Parser.parse_file(self._server.settings.binds_path)
        self._move_history = MoveHistory(self._bindings_config.idle_time, time.time())

        self._console = Console()
        self._server.cursor_state = self._console.keyboard.cursor

        self._current_mode: str = "BIND"

    def run(self):
        with self._server:
            self._server.start()
            self._server.launch_chromium()

            while True:
                self._run_once()

    def _run_once(self):
        move: str | None = None

        try:
            self._current_mode = self._server.mode_queue.get(timeout=0.1)
        except queue.Empty:
            pass

        try:
            move = self._server.move_queue.get(timeout=0.1)
        except queue.Empty:
            return

        # TODO Separate functions for each mode, maybe even make a quick Mode enum? --> fail on unrecognized mode
        if self._current_mode == "BIND":
            self._move_history.set_time(time.time())

            print(move)
            self._move_history.append(MoveType(move))
            match: MoveList | None = self._move_history.find_match(
                self._bindings_config.bindings, greedy=True
            )
            self._server.binds_buffer = self._move_history.to_str()

            if match:
                print(match)
                commands = self._bindings_config.bindings.bindings.get(match)
                if not commands:
                    raise ValueError(f"MoveList not found in bindings: {match}")
                commands.execute()
                self._move_history.clear()

        elif self._current_mode == "CONSOLE":
            self._console.handle_move(MoveType(move))
            self._server.cursor_state = self._console.keyboard.cursor


if __name__ == "__main__":
    app = App()
    app.run()
