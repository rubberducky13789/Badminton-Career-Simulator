"""Local server with an atomic JSON save API for Badminton Career Simulator."""

from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import tempfile
from bwf_rankings import refresh as refresh_bwf_rankings


ROOT = Path(__file__).resolve().parent
SAVE_FILE = ROOT / "data.json"
HOST = "127.0.0.1"
PORT = 8765

DEFAULT_SAVE = {
    "player": {
        "name": "", "age": 14, "gender": "", "nationality": "",
        "skill": 40, "fitness": 40, "stamina": 70, "confidence": 50,
        "money": 1000, "ranking": 1000, "ranking_points": 0,
        "titles": 0, "wins": 0, "runner_ups": 0, "career_earnings": 0,
    },
    "career": {"week": 1, "season": 1, "status": "active"},
    "tournaments": [],
    "rankings": [],
}


def valid_save(data):
    """Accept only the expected top-level save structure."""
    return (
        isinstance(data, dict)
        and isinstance(data.get("player"), dict)
        and isinstance(data.get("career"), dict)
        and isinstance(data.get("tournaments"), list)
        and isinstance(data.get("rankings"), list)
    )


def atomic_write(data):
    """Write a complete save to a temporary file, then replace atomically."""
    fd, temp_name = tempfile.mkstemp(prefix="data-", suffix=".json", dir=ROOT)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, SAVE_FILE)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def load_or_reset():
    """Load the save, safely resetting missing or malformed files."""
    try:
        with SAVE_FILE.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        if not valid_save(data):
            raise ValueError("Unexpected save structure")
        return data
    except (OSError, ValueError, json.JSONDecodeError):
        atomic_write(DEFAULT_SAVE)
        return DEFAULT_SAVE


class GameHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def send_json(self, data, status=200):
        payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        if self.path == "/api/bwf-players":
            self.send_json(refresh_bwf_rankings())
            return
        if self.path == "/api/save":
            self.send_json(load_or_reset())
            return
        super().do_GET()

    def do_POST(self):
        if self.path == "/api/bwf-refresh":
            self.send_json(refresh_bwf_rankings(force=True, rebuild=True))
            return
        if self.path != "/api/save":
            self.send_error(404)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > 20_000_000:
                raise ValueError("Invalid save size")
            data = json.loads(self.rfile.read(length).decode("utf-8"))
            if not valid_save(data):
                raise ValueError("Invalid save structure")
            atomic_write(data)
            self.send_json({"ok": True})
        except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as error:
            self.send_json({"ok": False, "error": str(error)}, 400)

    def log_message(self, format_string, *args):
        print(f"[game] {format_string % args}")


if __name__ == "__main__":
    load_or_reset()
    print(f"Badminton Career Simulator: http://{HOST}:{PORT}")
    ThreadingHTTPServer((HOST, PORT), GameHandler).serve_forever()
