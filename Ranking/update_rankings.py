"""Refresh all AiScore rankings and report changes from the prior export."""

from __future__ import annotations

import csv
import subprocess
import sys
from datetime import datetime
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent
COMBINED_FILE = PROJECT_DIR / "aiscore_bwf_all_rankings.csv"
CHANGES_FILE = PROJECT_DIR / "aiscore_bwf_ranking_changes.csv"
HISTORY_FILE = PROJECT_DIR / "aiscore_bwf_ranking_change_history.csv"
CHANGE_FIELDS = [
    "detected_at",
    "change_type",
    "category",
    "name",
    "old_rank",
    "new_rank",
    "old_points",
    "new_points",
    "old_country",
    "new_country",
]


def read_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as input_file:
        return list(csv.DictReader(input_file))


def row_key(row: dict[str, str]) -> tuple[str, str]:
    return row.get("category", ""), row.get("name", "")


def compare_rankings(
    old_rows: list[dict[str, str]], new_rows: list[dict[str, str]]
) -> list[dict[str, str]]:
    detected_at = datetime.now().astimezone().isoformat(timespec="seconds")
    old_by_key = {row_key(row): row for row in old_rows}
    new_by_key = {row_key(row): row for row in new_rows}
    changes = []

    for key in sorted(old_by_key.keys() | new_by_key.keys()):
        old = old_by_key.get(key, {})
        new = new_by_key.get(key, {})
        if not old:
            change_type = "added"
        elif not new:
            change_type = "removed"
        elif any(old.get(field, "") != new.get(field, "") for field in ("rank", "points", "country")):
            change_type = "changed"
        else:
            continue

        changes.append(
            {
                "detected_at": detected_at,
                "change_type": change_type,
                "category": key[0],
                "name": key[1],
                "old_rank": old.get("rank", ""),
                "new_rank": new.get("rank", ""),
                "old_points": old.get("points", ""),
                "new_points": new.get("points", ""),
                "old_country": old.get("country", ""),
                "new_country": new.get("country", ""),
            }
        )
    return changes


def write_changes(path: Path, changes: list[dict[str, str]], append: bool = False) -> None:
    existing_file = path.exists() and path.stat().st_size > 0
    mode = "a" if append else "w"
    with path.open(mode, newline="", encoding="utf-8-sig") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=CHANGE_FIELDS)
        if not append or not existing_file:
            writer.writeheader()
        writer.writerows(changes)


def main() -> int:
    old_rows = read_rows(COMBINED_FILE)
    command = [sys.executable, "-u", str(PROJECT_DIR / "export_aiscore_rankings.py")]
    result = subprocess.run(command, cwd=PROJECT_DIR, text=True, capture_output=True)
    if result.returncode != 0:
        print(result.stdout, end="")
        print(result.stderr, end="", file=sys.stderr)
        return result.returncode

    new_rows = read_rows(COMBINED_FILE)
    if not new_rows:
        print("The refresh produced no ranking rows.", file=sys.stderr)
        return 1

    changes = compare_rankings(old_rows, new_rows) if old_rows else []
    write_changes(CHANGES_FILE, changes)
    if changes:
        write_changes(HISTORY_FILE, changes, append=True)

    print(result.stdout, end="")
    print(f"Detected {len(changes)} ranking changes.")
    print(f"Latest change report: {CHANGES_FILE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
