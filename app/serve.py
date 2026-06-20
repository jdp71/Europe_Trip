#!/usr/bin/env python3
"""Serve the trip PWA locally for iPhone testing and offline caching."""
import http.server
import socket
import webbrowser
from pathlib import Path

PORT = 8080
DIR = Path(__file__).parent


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DIR), **kwargs)

    def end_headers(self):
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Service-Worker-Allowed", "/")
        super().end_headers()


def local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()


if __name__ == "__main__":
    ip = local_ip()
    print(f"\n  Europe Trip App")
    print(f"  ─────────────────────────────────")
    print(f"  On this computer:  http://localhost:{PORT}")
    print(f"  On your iPhone:    http://{ip}:{PORT}")
    print(f"\n  1. Make sure iPhone is on the same Wi-Fi")
    print(f"  2. Open the iPhone URL in Safari")
    print(f"  3. Tap Share → Add to Home Screen")
    print(f"  4. Open the app once to cache all PDFs offline\n")
    webbrowser.open(f"http://localhost:{PORT}")
    http.server.HTTPServer(("", PORT), Handler).serve_forever()
