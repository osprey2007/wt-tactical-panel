from __future__ import annotations

import os
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

UPSTREAM = "http://127.0.0.1:8111"
ALLOWED = {"/state", "/indicators", "/map_info.json", "/map_obj.json"}
HOST = os.getenv("WT_RELAY_HOST", "0.0.0.0")
PORT = int(os.getenv("WT_RELAY_PORT", "8112"))


class RelayHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        path = self.path.split("?", 1)[0]
        if path not in ALLOWED:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not found")
            return

        url = f"{UPSTREAM}{path}"
        try:
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=2.0) as resp:
                body = resp.read()
                self.send_response(resp.status)
                self.send_header("Content-Type", resp.headers.get("Content-Type", "application/json"))
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
        except urllib.error.HTTPError as exc:
            body = exc.read() or b""
            self.send_response(exc.code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except Exception:
            self.send_response(502)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"War Thunder upstream unavailable on 127.0.0.1:8111")

    def log_message(self, fmt: str, *args) -> None:
        # Keep logs concise in the console while still showing requests.
        super().log_message(fmt, *args)


if __name__ == "__main__":
    server = ThreadingHTTPServer((HOST, PORT), RelayHandler)
    print(f"WT relay listening on http://{HOST}:{PORT} -> {UPSTREAM}")
    server.serve_forever()
