import http.server
import json
import os
import queue
import threading
from pathlib import Path
from urllib.parse import parse_qs, urlparse

move_queue: queue.Queue[str] = queue.Queue()
mode_queue: queue.Queue[str] = queue.Queue()
binds_reload_event = threading.Event()
binds_path_changed_event = threading.Event()
cursor_state: dict = {"row": 1, "col": 0, "shiftlock": False}

_binds_path: str = ""
_binds_root: str = ""
_binds_lock = threading.Lock()
_binds_buffer: list[str] = []
_binds_buffer_lock = threading.Lock()


def get_binds_path() -> str:
    with _binds_lock:
        return _binds_path


def set_binds_buffer(moves: list[str]) -> None:
    with _binds_buffer_lock:
        _binds_buffer.clear()
        _binds_buffer.extend(moves)


def clear_binds_buffer() -> None:
    set_binds_buffer([])


def get_binds_buffer(limit: int = 50) -> list[str]:
    with _binds_buffer_lock:
        return _binds_buffer[-limit:]


def _path_to_relative(path: str) -> str:
    if not _binds_root:
        return path
    try:
        return os.path.relpath(path, _binds_root)
    except ValueError:
        return path


def _is_supported_binds_file(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in {".txt", ".json"}


def _list_binds_files() -> list[str]:
    if not _binds_root:
        return []
    root = Path(_binds_root)
    files = [
        os.path.relpath(str(p), _binds_root)
        for p in root.rglob("*")
        if _is_supported_binds_file(p)
    ]
    files.sort()
    return files


def _resolve_binds_selection(selection: str) -> str:
    selection = (selection or "").strip()
    if not selection:
        raise ValueError("Missing bind file selection")

    if not _binds_root:
        raise ValueError("Binds root is not configured")

    root = Path(_binds_root).resolve()
    candidate = (root / selection).resolve()

    if root != candidate and root not in candidate.parents:
        raise ValueError("Invalid bind file path")
    if not _is_supported_binds_file(candidate):
        raise ValueError("Selected file must be an existing .txt or .json file")

    return str(candidate)


class CubeHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        if parsed.path == "/move":
            turn = params.get("turn", [None])[0]
            if turn:
                move_queue.put(turn)
            self._send_plain(200, "OK")

        elif parsed.path == "/setmode":
            mode = params.get("mode", [None])[0]
            if mode in ("BINDS", "CONSOLE"):
                mode_queue.put(mode)
                self._send_plain(200, "OK")
            else:
                self._send_plain(400, "Invalid mode")

        elif parsed.path == "/binds":
            try:
                with open(get_binds_path(), encoding="utf-8") as f:
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
            selected = get_binds_path()
            files = _list_binds_files()
            selected_rel = _path_to_relative(selected)
            if selected_rel not in files:
                files.insert(0, selected_rel)
            self._send_json(200, {"selected": selected_rel, "files": files})

        elif parsed.path == "/moves/history":
            limit = 50
            try:
                limit = max(1, min(500, int(params.get("limit", ["50"])[0])))
            except ValueError:
                pass
            self._send_json(200, {"moves": get_binds_buffer(limit)})

        elif parsed.path == "/cursor":
            self._send_json(200, cursor_state)

        else:
            super().do_GET()

    def do_POST(self):
        global _binds_path
        parsed = urlparse(self.path)
        if parsed.path == "/binds":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8")
            try:
                with open(get_binds_path(), "w", encoding="utf-8") as f:
                    f.write(body)
                binds_reload_event.set()
                self._send_plain(200, "OK")
            except Exception as ex:
                self._send_plain(500, str(ex))
        elif parsed.path == "/binds/select":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8")
            try:
                new_path = _resolve_binds_selection(body)
                with _binds_lock:
                    _binds_path = new_path
                binds_path_changed_event.set()
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

    def _send_json(self, code: int, obj):
        data = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, format, *args):
        pass  # suppress per-request logging


def start_server(
    directory: str,
    binds_path: str,
    binds_root: str,
    host: str = "localhost",
    port: int = 8765,
) -> http.server.HTTPServer:
    global _binds_path, _binds_root
    with _binds_lock:
        _binds_path = binds_path
    _binds_root = binds_root

    def handler_factory(*args, **kwargs):
        return CubeHandler(*args, directory=directory, **kwargs)

    server = http.server.HTTPServer((host, port), handler_factory)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server
