import os
import socket
import urllib.request

def check_http(url: str) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=5) as r:
            return 200 <= r.status < 500
    except Exception:
        return False

print("=== HMB NEXUS STARTUP CHECK ===", flush=True)
print("Python OK", flush=True)
print("DISCORD_TOKEN:", "SET" if os.getenv("DISCORD_TOKEN") else "MISSING", flush=True)
print("PO provider:", "READY" if check_http("http://127.0.0.1:4416/ping") else "NOT READY", flush=True)
try:
    socket.create_connection(("127.0.0.1", 4416), 2).close()
    print("PO provider TCP: OK", flush=True)
except OSError:
    print("PO provider TCP: FAIL", flush=True)
