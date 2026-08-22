import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PORT = int(os.getenv("PORT", "8080"))


class PolicyHandler(BaseHTTPRequestHandler):
    def send_file(self, filename, content_type="text/html"):
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
        self.wfile.write(data)

    def do_GET(self):
        path = self.path.split("?", 1)[0].rstrip("/") or "/"

        if path in ("/", "/terms.html"):
            self.send_file("terms.html")
        elif path == "/privacy.html":
            self.send_file("privacy.html")
        else:
            self.send_error(404, "Not Found")

    def log_message(self, fmt, *args):
        print(f"[WEB] {self.address_string()} - {fmt % args}", flush=True)


if __name__ == "__main__":
    server = ThreadingHTTPServer(("0.0.0.0", PORT), PolicyHandler)
    print(f"HMB Policy Server running on port {PORT}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
