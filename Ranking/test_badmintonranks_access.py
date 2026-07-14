"""Test whether the Badminton Ranks BWF ranking page is directly accessible."""

import requests
from bs4 import BeautifulSoup


URL = (
    "https://badmintonranks.com/ranking/bwf"
    "?type=MS&rankDateStr=2026-07-07"
)
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def main() -> None:
    try:
        response = requests.get(URL, headers=HEADERS, timeout=30)
    except requests.RequestException as error:
        print("Status code: unavailable")
        print(f"Request failed: {error}")
        return

    response.encoding = response.apparent_encoding or "utf-8"
    html = response.text
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.get_text(strip=True) if soup.title else "Not found"

    page_text = soup.get_text(" ", strip=True).lower()
    ranking_markers = ("ranking", "rank", "player", "men's singles")
    found_markers = [marker for marker in ranking_markers if marker in page_text]

    # Structural elements provide extra evidence that records or a rankings
    # interface are included in the initial response. No records are extracted.
    has_ranking_structure = bool(
        soup.find("table")
        or soup.select_one("[class*='ranking'], [class*='player'], [id*='ranking']")
    )
    has_ranking_data = bool(found_markers and has_ranking_structure)

    print(f"Status code: {response.status_code}")
    print(f"Page title: {title}")
    print("\nFirst 1000 characters of HTML:")
    print(html[:1000])
    print("\nRanking/player data present in response:", end=" ")
    print("Yes" if has_ranking_data else "No")
    if found_markers:
        print(f"Relevant text marker(s): {', '.join(found_markers)}")
    print(f"Ranking-like HTML structure present: {'Yes' if has_ranking_structure else 'No'}")

    if response.ok and not has_ranking_data:
        print(
            "The page itself loaded, but ranking data was not confirmed in the "
            "initial HTML. It may be loaded with JavaScript."
        )


if __name__ == "__main__":
    main()
