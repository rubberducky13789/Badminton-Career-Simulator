"""Test whether the public BWF rankings page is accessible without a browser."""

from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


URL = "https://bwfbadminton.com/rankings/?id=2"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0.0.0 Safari/537.36"
)


def main() -> None:
    request = Request(
        URL,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        },
    )

    try:
        with urlopen(request, timeout=30) as response:
            status_code = response.status
            html = response.read().decode(
                response.headers.get_content_charset() or "utf-8",
                errors="replace",
            )
    except HTTPError as error:
        status_code = error.code
        html = error.read().decode("utf-8", errors="replace")
    except URLError as error:
        print("HTTP status code: unavailable")
        print("Page loaded successfully: No")
        print(f"Request error: {error.reason}")
        return

    loaded_successfully = 200 <= status_code < 300
    normalized_html = html.lower()

    # These markers only test whether the initial HTML appears to contain the
    # rankings interface or player records. They do not extract ranking data.
    player_markers = ("player-profile", "player profile", "world ranking")
    found_markers = [
        marker for marker in player_markers if marker in normalized_html
    ]
    cloudflare_block = (
        "cloudflare" in normalized_html
        and (
            "attention required" in normalized_html
            or "/cdn-cgi/" in normalized_html
        )
    )

    print(f"HTTP status code: {status_code}")
    print(f"Page loaded successfully: {'Yes' if loaded_successfully else 'No'}")
    print("\nFirst 1000 characters of returned HTML:")
    print(html[:1000])
    print("\nPlayer-related data present in initial HTML:", end=" ")
    if found_markers:
        print(f"Yes (found marker(s): {', '.join(found_markers)})")
    else:
        print("No")
        if cloudflare_block:
            print(
                "Diagnosis: Cloudflare blocked the plain HTTP request, so the "
                "BWF ranking page HTML was not returned. A real browser via "
                "Playwright or Selenium may be required."
            )
        elif loaded_successfully:
            print(
                "Diagnosis: The page loaded, but player data was not visible "
                "in the initial HTML. It may be loaded by JavaScript, so "
                "Playwright or Selenium may be required."
            )
        else:
            print(
                "Diagnosis: The request failed, so player data could not be "
                "checked."
            )


if __name__ == "__main__":
    main()
