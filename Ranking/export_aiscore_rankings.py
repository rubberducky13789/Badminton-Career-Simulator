"""Export all current AiScore BWF men's-singles rankings to a CSV file."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

from lookup_aiscore_ranking import RANKING_CATEGORIES, read_rankings


DEFAULT_OUTPUT = "aiscore_bwf_all_rankings.csv"
CATEGORY_FILENAMES = {
    "ms": "aiscore_bwf_mens_singles_rankings.csv",
    "ws": "aiscore_bwf_womens_singles_rankings.csv",
    "md": "aiscore_bwf_mens_doubles_rankings.csv",
    "wd": "aiscore_bwf_womens_doubles_rankings.csv",
    "xd": "aiscore_bwf_mixed_doubles_rankings.csv",
}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Export all five current AiScore BWF rankings to CSV."
    )
    parser.add_argument(
        "--output",
        default=DEFAULT_OUTPUT,
        help=f"CSV output path (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--show-browser",
        action="store_true",
        help="Show Chrome while loading the rankings page",
    )
    args = parser.parse_args()

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                channel="chrome",
                headless=not args.show_browser,
            )
            page = browser.new_page(
                user_agent=(
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/126.0.0.0 Safari/537.36"
                )
            )
            rankings_by_category = {}
            for code, (category_name, rankings_url) in RANKING_CATEGORIES.items():
                print(f"Loading {category_name}...", flush=True)
                category_rows = read_rankings(page, rankings_url)
                print(f"Loaded {len(category_rows)} rows.", flush=True)
                rankings_by_category[code] = [
                    {"category": category_name, **row} for row in category_rows
                ]
            browser.close()
    except PlaywrightTimeoutError:
        print(
            "Could not load the ranking rows. Retry with --show-browser.",
            file=sys.stderr,
        )
        return 1
    except Exception as error:
        print(f"Ranking export failed: {error}", file=sys.stderr)
        return 1

    output_path = Path(args.output).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "category",
        "rank",
        "name",
        "country",
        "points",
        "movement",
        "profile",
    ]
    rankings = [
        row
        for code in RANKING_CATEGORIES
        for row in rankings_by_category[code]
    ]
    with output_path.open("w", newline="", encoding="utf-8-sig") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rankings)

    for code, rows in rankings_by_category.items():
        category_path = output_path.parent / CATEGORY_FILENAMES[code]
        with category_path.open("w", newline="", encoding="utf-8-sig") as output_file:
            writer = csv.DictWriter(output_file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        print(f"{RANKING_CATEGORIES[code][0]}: {len(rows)} rows -> {category_path}")

    print(f"Combined: {len(rankings)} rows -> {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
