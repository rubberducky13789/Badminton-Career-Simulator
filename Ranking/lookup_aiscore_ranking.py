"""Look up a player's current AiScore BWF men's-singles ranking."""

from __future__ import annotations

import argparse
import re
import sys
import unicodedata

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright


RANKING_CATEGORIES = {
    "ms": (
        "Men's Singles",
        "https://m.aiscore.com/en/badminton/rankings/bwf-world-rankings",
    ),
    "ws": (
        "Women's Singles",
        "https://m.aiscore.com/en/badminton/rankings/bwf-world-rankings-women",
    ),
    "md": (
        "Men's Doubles",
        "https://m.aiscore.com/en/badminton/rankings/bwf-world-rankings-doubles",
    ),
    "wd": (
        "Women's Doubles",
        "https://m.aiscore.com/en/badminton/rankings/bwf-world-rankings-women-doubles",
    ),
    "xd": (
        "Mixed Doubles",
        "https://m.aiscore.com/en/badminton/rankings/bwf-world-rankings-mixed",
    ),
}


def normalize_name(value: str) -> str:
    """Make player names comparable across case, accents, and punctuation."""
    value = unicodedata.normalize("NFKD", value)
    value = "".join(character for character in value if not unicodedata.combining(character))
    return " ".join(re.findall(r"[a-z0-9]+", value.casefold()))


def read_rankings(page, rankings_url: str | None = None) -> list[dict[str, str]]:
    rankings_url = rankings_url or RANKING_CATEGORIES["ms"][1]
    page.goto(rankings_url, wait_until="domcontentloaded", timeout=60_000)
    page.wait_for_selector("ul.rankData > li", state="attached", timeout=60_000)

    return page.locator("ul.rankData > li").evaluate_all(
        """rows => rows.map(row => {
            const cells = Array.from(row.children);
            const playerLink = row.querySelector("a.teamData") || cells[1];
            const images = playerLink ? Array.from(playerLink.querySelectorAll("img")) : [];
            const href = playerLink?.href || "";
            return {
                rank: cells[0]?.textContent?.trim() || "",
                name: images[0]?.alt?.trim() || playerLink?.textContent?.trim() || "",
                country: images[1]?.alt?.trim() || "",
                points: cells[2]?.textContent?.trim() || "",
                movement: cells[3]?.textContent?.trim() || "",
                profile: href.startsWith("javascript:") ? "" : href
            };
        }).filter(row => row.rank && row.name)"""
    )


def find_matches(rankings: list[dict[str, str]], query: str) -> list[dict[str, str]]:
    normalized_query = normalize_name(query)
    exact = [row for row in rankings if normalize_name(row["name"]) == normalized_query]
    if exact:
        return exact
    query_tokens = set(normalized_query.split())
    return [
        row
        for row in rankings
        if query_tokens.issubset(set(normalize_name(row["name"]).split()))
    ]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Find a player or team in AiScore's current BWF ranking."
    )
    parser.add_argument("player", help="Full or partial player name")
    parser.add_argument(
        "--category",
        choices=RANKING_CATEGORIES,
        default="ms",
        help="ms, ws, md, wd, or xd (default: ms)",
    )
    parser.add_argument(
        "--show-browser",
        action="store_true",
        help="Show Chrome while loading the rankings page",
    )
    args = parser.parse_args()
    category_name, rankings_url = RANKING_CATEGORIES[args.category]

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
            rankings = read_rankings(page, rankings_url)
            browser.close()
    except PlaywrightTimeoutError:
        print(
            "Could not load the ranking rows. AiScore may have shown a "
            "Cloudflare challenge; retry with --show-browser.",
            file=sys.stderr,
        )
        return 1
    except Exception as error:
        print(f"Ranking lookup failed: {error}", file=sys.stderr)
        return 1

    matches = find_matches(rankings, args.player)
    if not matches:
        print(f'No player matching "{args.player}" was found.')
        return 2

    for row in matches:
        print(f"Category: {category_name}")
        print(f"Player: {row['name']}")
        if row["country"]:
            print(f"Country: {row['country']}")
        print(f"World ranking: {row['rank']}")
        print(f"Points: {row['points']}")
        if row["movement"]:
            print(f"Movement: {row['movement']}")
        if row["profile"]:
            print(f"Profile: {row['profile']}")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
