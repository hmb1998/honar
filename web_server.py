import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PORT = int(os.getenv("PORT", "10000"))


class PolicyHandler(BaseHTTPRequestHandler):
    def send_file(self, filename, content_type="text/html", head_only=False):
        file_path = ROOT / filename

        if not file_path.is_file():
            self.send_error(404, "Not Found")
            return

        data = file_path.read_bytes()

        self.send_response(200)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()

        if not head_only:
            self.wfile.write(data)

    def health_check(self, head_only=False):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", "2")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()

        if not head_only:
            self.wfile.write(b"OK")

    def do_GET(self):
        path = self.path.split("?", 1)[0].rstrip("/") or "/"

        if path == "/healthz":
            self.health_check()
        elif path in ("/", "/terms.html"):
            self.send_file("terms.html")
        elif path == "/privacy.html":
            self.send_file("privacy.html")
        else:
            self.send_error(404, "Not Found")

    def do_HEAD(self):
        path = self.path.split("?", 1)[0].rstrip("/") or "/"

        if path == "/healthz":
            self.health_check(head_only=True)
        elif path in ("/", "/terms.html"):
            self.send_file("terms.html", head_only=True)
        elif path == "/privacy.html":
            self.send_file("privacy.html", head_only=True)
        else:
            self.send_error(404, "Not Found")

    def log_message(self, fmt, *args):
        print(
            f"[WEB] {self.address_string()} - {fmt % args}",
            flush=True
        )


if __name__ == "__main__":
    server = ThreadingHTTPServer(("0.0.0.0", PORT), PolicyHandler)
    print(f"HMB Policy Server running on port {PORT}", flush=True)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
