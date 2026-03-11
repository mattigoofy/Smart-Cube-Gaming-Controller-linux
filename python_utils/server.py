import http.server
import json
import queue
import threading
from urllib.parse import parse_qs, urlparse

move_queue: queue.Queue[str] = queue.Queue()
mode_queue: queue.Queue[str] = queue.Queue()
binds_reload_event = threading.Event()
cursor_state: dict = {"row": 1, "col": 0, "shiftlock": False}

_binds_path: str = ""


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
                with open(_binds_path, encoding="utf-8") as f:
                    content = f.read()
                data = content.encode()
                self.send_response(200)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
            except Exception as ex:
                self._send_plain(500, str(ex))

        elif parsed.path == "/cursor":
            self._send_json(200, cursor_state)

        else:
            super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/binds":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8")
            try:
                with open(_binds_path, "w", encoding="utf-8") as f:
                    f.write(body)
                binds_reload_event.set()
                self._send_plain(200, "OK")
            except Exception as ex:
                self._send_plain(500, str(ex))
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
    directory: str, binds_path: str, host: str = "localhost", port: int = 8765
) -> http.server.HTTPServer:
    global _binds_path
    _binds_path = binds_path

    def handler_factory(*args, **kwargs):
        return CubeHandler(*args, directory=directory, **kwargs)

    server = http.server.HTTPServer((host, port), handler_factory)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server
