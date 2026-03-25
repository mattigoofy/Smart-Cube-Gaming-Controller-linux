import http.server
import json
import os
import pathlib
import queue
import subprocess
import threading
from dataclasses import dataclass
import time
from urllib.parse import parse_qs, urlparse

from SmartCubeGamingController.modes.binds.moves import MoveType
from SmartCubeGamingController.modes.console.console import CursorState


@dataclass
class ServerSettings:
    """
    A class holding all settings pertaining to the server settings.
    """

    html_dir: str = os.path.join("src/", "HTML-JS/")
    binds_root: str = os.path.join("binds/")
    binds_path: str = os.path.join(binds_root, "config.yml")
    host: str = "localhost"
    port: int = 8766
    url: str = f"http://localhost:{port}/index.html"


class Server:
    """
    "Glue" between the backend code and the HTML server code. Handles all translation between the two.
    """

    def __init__(self, settings: ServerSettings) -> None:
        self._settings = settings

        self._browser_process: subprocess.Popen[bytes] | None = None

        self._cursor_state = None

        self._move_queue: queue.Queue[str] = queue.Queue()
        self._mode_queue: queue.Queue[str] = queue.Queue()

        self._binds_reload_event = threading.Event()
        self._binds_path_changed_event = threading.Event()

        # NOTE I'm blindly copying the previous code, but why the lock? It seems to only be used when modifying self._binds_path, but isn't an assignment operation atomic anyway (I assume that's the case for `str`), meaning the lock doesn't do much?
        self._binds_lock = threading.Lock()
        self._binds_path: str = ""
        self._binds_root: str = ""

        self._binds_buffer_lock = threading.Lock()
        self._binds_buffer: list[str] = []

    @property
    def settings(self):
        return self._settings
    
    @property
    def cursor_state(self):
        return self._cursor_state

    @cursor_state.setter
    def cursor_state(self, cursor: CursorState):
        self._cursor_state = cursor

    @property
    def move_queue(self):
        return self._move_queue

    @property
    def mode_queue(self):
        return self._mode_queue

    @property
    def binds_reload_event(self):
        return self._binds_reload_event

    @property
    def binds_path_changed_event(self):
        return self._binds_path_changed_event

    @property
    def binds_path(self):
        with self._binds_lock:
            return self._binds_path

    @binds_path.setter
    def binds_path(self, new_path: str):
        with self._binds_lock:
            self._binds_path = new_path

    @property
    def binds_root(self):
        with self._binds_lock:
            return self._binds_root

    @binds_root.setter
    def binds_root(self, new_root: str):
        with self._binds_lock:
            self._binds_root = new_root

    @property
    # NOTE limit parameter is not reachable if you're using this as a property, hence the separate function `binds_buffer_with_limit`
    def binds_buffer(self, limit: int = 50):
        with self._binds_buffer_lock:
            return self._binds_buffer[-limit:]

    def binds_buffer_with_limit(self, limit: int = 50):
        with self._binds_buffer_lock:
            return self._binds_buffer[-limit:]

    @binds_buffer.setter
    def binds_buffer(self, moves: list[str]):
        with self._binds_buffer_lock:
            self._binds_buffer.clear()
            self._binds_buffer.extend(moves)

    def start(self):
        """
        Start the server, using the settings defined in `self._settings`
        """
        self.binds_root = self.settings.binds_root
        self.binds_path = self.settings.binds_path

        def handler_factory(*args, **kwargs):
            return CubeHandler(
                *args, directory=self.settings.html_dir, parent=self, **kwargs
            )

        server = http.server.HTTPServer(
            (self.settings.host, self.settings.port), handler_factory
        )
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()

        return server
    
    def launch_chromium(self) -> subprocess.Popen[bytes]:
        chromium_paths = [
            "/snap/bin/chromium",                                   # Snap
            "/var/lib/flatpak/exports/bin/org.chromium.Chromium",   # Flatpak (system)
            os.path.expanduser("~/.local/share/flatpak/exports/bin/org.chromium.Chromium"),  # Flatpak (user)
            "/var/lib/flatpak/exports/bin/com.google.Chrome",       # Flatpak Google Chrome (system)
            os.path.expanduser("~/.local/share/flatpak/exports/bin/com.google.Chrome"),  # Flatpak Google Chrome (user)
            "/run/current-system/sw/bin/chromium",                  # NixOS system
            os.path.expanduser("~/.nix-profile/bin/chromium"), # Nix user profile
            "/nix/var/nix/profiles/default/bin/chromium",           # Nix default profile
            "chromium",                                             # PATH fallback
            "chromium-browser",                                     # PATH fallback (Debian/Ubuntu)
            "google-chrome",                                        # Chrome fallback
        ]

        chromium_bin = next(
            (p for p in chromium_paths if os.path.isfile(p) or (not os.path.sep in p)),
            None,
        )

        if chromium_bin is None:
            raise FileNotFoundError("Could not find a Chromium or Chrome executable.")

        # Flatpak needs to be launched differently
        if "flatpak" in chromium_bin:
            if "google" in chromium_bin:
                app_name = "com.google.Chrome"
            else:
                app_name = "org.chromium.Chromium"
            cmd = [
                "flatpak", "run", app_name,
                "--enable-features=WebBluetooth",
                "--user-data-dir=/tmp/chrome-debug",
                self.settings.url,
            ]
        else:
            cmd = [
                chromium_bin,
                "--enable-features=WebBluetooth",
                "--user-data-dir=/tmp/chrome-debug",
                self.settings.url,
            ]

        process = subprocess.Popen(cmd)
        time.sleep(2)
        return process
    
    # For `with` statements
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        if self._browser_process:
            self._browser_process.terminate()


class CubeHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(
        self, *args, directory: str | None = None, parent: Server, **kwargs
    ) -> None:
        self._parent = parent
        super().__init__(*args, directory=directory, **kwargs)

    def _all_binds_filepaths(self) -> list[str]:
        if not self._parent.binds_root:
            return []
        root = pathlib.Path(self._parent.binds_root)
        files = [
            os.path.relpath(str(p), self._parent.binds_root)
            for p in root.rglob("*")
            if self._is_supported_binds_file(p)
        ]
        files.sort()
        return files

    def _is_supported_binds_file(self, path: pathlib.Path) -> bool:
        return path.is_file() and path.suffix.lower() in {".txt", ".json"}

    def _path_to_relative(self, path: str) -> str:
        if not self._parent.binds_root:
            return path
        try:
            return os.path.relpath(path, self._parent.binds_root)
        except ValueError:
            return path

    def _resolve_binds_selection(self, selection: str) -> str:
        selection = (selection or "").strip()
        if not selection:
            raise ValueError("Missing bind file selection")

        if not self._parent.binds_root:
            raise ValueError("Binds root is not configured")

        root = pathlib.Path(self._parent.binds_root).resolve()
        candidate = (root / selection).resolve()

        if root != candidate and root not in candidate.parents:
            raise ValueError("Invalid bind file path")
        if not self._is_supported_binds_file(candidate):
            raise ValueError("Selected file must be an existing .txt or .json file")

        return str(candidate)

    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        if parsed.path == "/move":
            turn = params.get("turn", [None])[0]
            turn = MoveType.from_str(turn)
            if turn:
                self._parent.move_queue.put(turn)
            self._send_plain(200, "OK")

        elif parsed.path == "/setmode":
            mode = params.get("mode", [None])[0]
            if mode in ("BINDS", "CONSOLE"):
                self._parent.mode_queue.put(mode)
                self._send_plain(200, "OK")
            else:
                self._send_plain(400, "Invalid mode")

        elif parsed.path == "/binds":
            try:
                with open(self._parent.binds_path, encoding="utf-8") as f:
                    content = f.read()
                data = content.encode()
                self.send_response(200)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
            except Exception as ex:
                self._send_plain(500, str(ex))

        elif parsed.path == "/binds/options":
            selected = self._parent.binds_path
            files = self._all_binds_filepaths()
            selected_rel = self._path_to_relative(selected)
            if selected_rel not in files:
                files.insert(0, selected_rel)
            self._send_json(200, {"selected": selected_rel, "files": files})

        elif parsed.path == "/moves/history":
            limit = 50
            try:
                limit = max(1, min(500, int(params.get("limit", ["50"])[0])))
            except ValueError:
                pass
            self._send_json(200, {"moves": self._parent.binds_buffer_with_limit(limit)})

        elif parsed.path == "/cursor":
            self._send_json(200, self._parent.cursor_state.to_dict())

        else:
            super().do_GET()

    def do_POST(self):
        global _binds_path
        parsed = urlparse(self.path)
        if parsed.path == "/binds":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8")
            try:
                with open(self._parent.binds_path, "w", encoding="utf-8") as f:
                    f.write(body)
                self._parent.binds_reload_event.set()
                self._send_plain(200, "OK")
            except Exception as ex:
                self._send_plain(500, str(ex))
        elif parsed.path == "/binds/select":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8")
            try:
                new_path = self._resolve_binds_selection(body)
                self._parent.binds_path = new_path
                self._parent.binds_path_changed_event.set()
                self._send_plain(200, "OK")
            except Exception as ex:
                self._send_plain(400, str(ex))
        else:
            self._send_plain(404, "Not found")

    def _send_plain(self, code: int, body: str):
        data = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_json(self, code: int, obj: object):
        data = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, format, *args):  # pyright: ignore[reportMissingParameterType]
        pass  # suppress per-request logging
