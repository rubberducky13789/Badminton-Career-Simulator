"""Local web interface for browsing and updating BWF rankings."""

from __future__ import annotations

import csv
import subprocess
import sys
import threading
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, render_template, request

from lookup_aiscore_ranking import normalize_name


PROJECT_DIR = Path(__file__).resolve().parent
RANKINGS_FILE = PROJECT_DIR / "aiscore_bwf_all_rankings.csv"
CHANGES_FILE = PROJECT_DIR / "aiscore_bwf_ranking_changes.csv"
UPDATE_SCRIPT = PROJECT_DIR / "update_rankings.py"

app = Flask(__name__)
update_lock = threading.Lock()


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as input_file:
        return list(csv.DictReader(input_file))


def filter_rankings(
    rows: list[dict[str, str]], query: str = "", category: str = ""
) -> list[dict[str, str]]:
    query_tokens = set(normalize_name(query).split())
    filtered = []
    for row in rows:
        if category and row.get("category") != category:
            continue
        name_tokens = set(normalize_name(row.get("name", "")).split())
        if query_tokens and not query_tokens.issubset(name_tokens):
            continue
        filtered.append(row)
    return filtered


def concise_update_error(result: subprocess.CompletedProcess[str]) -> str:
    output = (result.stderr or result.stdout or "").strip()
    last_line = output.splitlines()[-1] if output else "No error details were returned."
    lowered = output.lower()
    if "playwright" in lowered or "browser" in lowered or "chrome" in lowered:
        return f"Playwright or Chrome failed: {last_line}"
    if any(term in lowered for term in ("timeout", "network", "connection", "name resolution")):
        return f"The ranking website could not be accessed: {last_line}"
    return f"The update script failed: {last_line}"


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/rankings")
def rankings():
    rows = read_csv_rows(RANKINGS_FILE)
    rows = filter_rankings(
        rows,
        query=request.args.get("query", ""),
        category=request.args.get("category", ""),
    )
    return jsonify({"rankings": rows, "count": len(rows)})


@app.post("/api/update")
def update_rankings():
    if not update_lock.acquire(blocking=False):
        return jsonify({"error": "A ranking update is already running."}), 409

    try:
        try:
            result = subprocess.run(
                [sys.executable, "-u", str(UPDATE_SCRIPT)],
                cwd=PROJECT_DIR,
                text=True,
                capture_output=True,
                timeout=600,
            )
        except subprocess.TimeoutExpired:
            return jsonify({"error": "The ranking update timed out after 10 minutes."}), 504
        except Exception as error:
            return jsonify({"error": f"Could not start the update script: {error}"}), 500

        if result.returncode != 0:
            return jsonify({"error": concise_update_error(result)}), 502

        changes = len(read_csv_rows(CHANGES_FILE))
        ranking_count = len(read_csv_rows(RANKINGS_FILE))
        completed_at = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
        return jsonify(
            {
                "message": "Rankings updated successfully.",
                "completed_at": completed_at,
                "changes": changes,
                "ranking_count": ranking_count,
            }
        )
    finally:
        update_lock.release()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False, threaded=True)
