"""Build and refresh the local BWF opponent database.

The game should not hand-maintain opponent ranking numbers. This module treats
official BWF ranking/profile pages as the source of truth, then writes a single
atomic JSON cache used by the website.
"""

from datetime import date, datetime, timezone
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import tempfile
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlencode, urljoin, urlparse
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent
DATA_FILE = ROOT / "bwf-players.json"
BWF_BASE = "https://bwfbadminton.com"
WORLD_RANKING_SOURCE = "https://bwfbadminton.com/rankings/?id=2"
RACE_TO_FINALS_SOURCE = "https://bwfworldtour.bwfbadminton.com/rankings/?id=9&cat_id=57&ryear=2026&week=28&page_size=25&page_no=1"

# BWF commonly uses these category IDs across ranking pages. If BWF changes the
# IDs later, the page itself is still parsed generically; this list just lets us
# request men/women singles directly.
RANKING_CATEGORIES = [
    {"cat_id": 57, "event": "MS", "gender": "Male", "label": "Men's Singles"},
    {"cat_id": 58, "event": "WS", "gender": "Female", "label": "Women's Singles"},
]

COUNTRY_CODES = {
    "CAN": "Canada", "JPN": "Japan", "CHN": "China", "KOR": "Korea",
    "DEN": "Denmark", "FRA": "France", "INA": "Indonesia", "IND": "India",
    "MAS": "Malaysia", "SGP": "Singapore", "THA": "Thailand", "TPE": "Chinese Taipei",
    "USA": "United States", "ESA": "El Salvador", "GUA": "Guatemala", "ENG": "England",
    "SCO": "Scotland", "UGA": "Uganda", "ZAM": "Zambia",
}


class RankingTableParser(HTMLParser):
    """Extract table rows, cell text, and player links from ranking pages."""

    def __init__(self):
        super().__init__()
        self.rows = []
        self.row = None
        self.cell = None
        self.in_cell = False
        self.in_row = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "tr":
            self.row = []
            self.in_row = True
        elif tag in ("td", "th") and self.in_row:
            self.cell = {"text": [], "links": []}
            self.in_cell = True
        elif self.in_cell and tag == "a":
            href = attrs.get("href", "")
            if "/player/" in href:
                self.cell["links"].append(href)
        elif self.in_cell and tag == "img":
            for attr in ("alt", "title"):
                value = attrs.get(attr, "")
                if value:
                    self.cell["text"].append(value)

    def handle_data(self, data):
        if self.in_cell:
            cleaned = " ".join(data.split())
            if cleaned:
                self.cell["text"].append(cleaned)

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self.in_cell:
            text = " ".join(" ".join(self.cell["text"]).split())
            self.row.append({"text": text, "links": list(self.cell["links"])})
            self.cell = None
            self.in_cell = False
        elif tag == "tr" and self.in_row:
            if self.row:
                self.rows.append(self.row)
            self.row = None
            self.in_row = False


class TextParser(HTMLParser):
    """Flatten profile page text while keeping image alt/title text."""

    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag == "img":
            attrs = dict(attrs)
            for attr in ("alt", "title"):
                value = attrs.get(attr, "")
                if value:
                    self.parts.append(value)

    def handle_data(self, data):
        cleaned = " ".join(data.split())
        if cleaned:
            self.parts.append(cleaned)


def empty_database():
    return {
        "updated_at": None,
        "last_refresh_attempt": None,
        "refresh_hours": 24,
        "sources": {
            "world_ranking": WORLD_RANKING_SOURCE,
            "hsbc_race_to_finals": RACE_TO_FINALS_SOURCE,
        },
        "players": [],
        "verification": {},
    }


def load_database():
    try:
        with DATA_FILE.open(encoding="utf-8") as handle:
            data = json.load(handle)
        if not isinstance(data.get("players"), list):
            raise ValueError("Missing players list")
        return {**empty_database(), **data}
    except (OSError, ValueError, json.JSONDecodeError):
        return empty_database()


def atomic_write(data):
    fd, temporary = tempfile.mkstemp(prefix="bwf-players-", suffix=".json", dir=ROOT)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, DATA_FILE)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def request_headers():
    return {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": BWF_BASE + "/",
    }


def fetch_html(url, timeout=15):
    request = Request(url, headers=request_headers())
    with urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", "replace")


def with_query(url, **params):
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    for key, value in params.items():
        if value is not None:
            query[key] = [str(value)]
    return parsed._replace(query=urlencode(query, doseq=True)).geturl()


def normalize_name(value):
    value = value.casefold()
    value = re.sub(r"[\u0300-\u036f]", "", value)
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return " ".join(value.split())


def name_tokens(value):
    return normalize_name(value).split()


def name_key(value):
    tokens = name_tokens(value)
    if not tokens:
        return ""
    if len(tokens) == 1:
        return tokens[0]
    return f"{tokens[0]} {tokens[-1]}"


def aliases_for_name(value):
    tokens = name_tokens(value)
    aliases = {normalize_name(value), name_key(value)}
    if len(tokens) > 2:
        first = tokens[0]
        for token in tokens[1:]:
            aliases.add(f"{first} {token}")
    return sorted(alias for alias in aliases if alias)


def slugify(value):
    return re.sub(r"(^-|-$)", "", re.sub(r"[^a-z0-9]+", "-", normalize_name(value)))


def clean_bwf_name(value):
    # BWF often returns uppercase surnames. Title-case gives the simulator a
    # professional display while aliases preserve matching accuracy.
    small_words = {"de", "del", "da", "van", "von"}
    words = []
    for word in " ".join(value.replace("\xa0", " ").split()).split(" "):
        lowered = word.casefold()
        words.append(lowered if lowered in small_words else word[:1].upper() + word[1:].lower())
    return " ".join(words)


def country_name(value):
    value = " ".join(value.split())
    if value.upper() in COUNTRY_CODES:
        return COUNTRY_CODES[value.upper()]
    return value.title() if value.isupper() else value


def parse_int(value):
    if value is None:
        return None
    digits = re.sub(r"[^0-9]", "", str(value))
    return int(digits) if digits else None


def player_id_from_link(href):
    match = re.search(r"/player/(\d+)(?:/|$)", href)
    return int(match.group(1)) if match else None


def extract_player_name_from_cell(cell):
    text = cell["text"]
    text = re.sub(r"\b\d{3,}\b", " ", text)
    text = re.sub(r"\b[A-Z]{3}\b", " ", text)
    text = re.sub(r"\s+", " ", text).strip(" -")
    return text


def row_to_player(row, gender, event):
    texts = [cell["text"] for cell in row]
    joined = " | ".join(texts)
    links = [link for cell in row for link in cell["links"] if "/player/" in link]
    if not links:
        return None
    member_id = player_id_from_link(links[0])
    if not member_id:
        return None

    numbers = [parse_int(text) for text in texts]
    numbers = [number for number in numbers if number is not None]
    rank = next((number for number in numbers if 0 < number < 5000), None)
    points = max((number for number in numbers if number and number > 5000 and number != member_id), default=None)
    highest_candidates = [number for number in numbers if number and 0 < number < 5000 and number != rank]
    highest = min(highest_candidates, default=rank)

    name_cell = next((cell for cell in row if cell["links"]), None)
    name = extract_player_name_from_cell(name_cell) if name_cell else ""
    if not name:
        # Fallback to the profile slug.
        path = urlparse(links[0]).path.rstrip("/").split("/")
        name = path[-1].replace("-", " ") if path else ""
    if not name:
        return None

    country = None
    for text in texts:
        token = text.strip()
        if token.upper() in COUNTRY_CODES:
            country = country_name(token)
            break
    if not country:
        country_match = re.search(r"\b([A-Z]{3})\b", joined)
        country = country_name(country_match.group(1)) if country_match else ""

    display_name = clean_bwf_name(name)
    profile_url = urljoin(BWF_BASE, links[0])
    return {
        "name": display_name,
        "bwf_name": name,
        "member_id": member_id,
        "country": country,
        "gender": gender,
        "event": event,
        "world_ranking": rank,
        "world_points": points,
        "highest_ranking": highest,
        "date_of_birth": None,
        "birth_date": None,
        "age": None,
        "nationality": country,
        "profile_url": profile_url,
        "aliases": aliases_for_name(display_name),
        "source": WORLD_RANKING_SOURCE,
    }


def parse_ranking_players(html, gender, event):
    parser = RankingTableParser()
    parser.feed(html)
    players = []
    seen = set()
    for row in parser.rows:
        player = row_to_player(row, gender, event)
        if not player or player["member_id"] in seen:
            continue
        seen.add(player["member_id"])
        players.append(player)
    return players


def fetch_category_players(category, page_size=100, max_pages=8):
    players = []
    seen = set()
    for page_no in range(1, max_pages + 1):
        url = with_query(WORLD_RANKING_SOURCE, cat_id=category["cat_id"], page_size=page_size, page_no=page_no)
        html = fetch_html(url)
        page_players = parse_ranking_players(html, category["gender"], category["event"])
        fresh = [player for player in page_players if player["member_id"] not in seen]
        if not fresh:
            break
        for player in fresh:
            seen.add(player["member_id"])
        players.extend(fresh)
        if len(page_players) < page_size:
            break
    return players


def flatten_profile_text(html):
    parser = TextParser()
    parser.feed(html)
    return " ".join(parser.parts)


def parse_birth_date(raw):
    if not raw:
        return None
    raw = " ".join(raw.replace(",", " ").split())
    for fmt in ("%d %B %Y", "%d %b %Y", "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(raw, fmt).date().isoformat()
        except ValueError:
            pass
    return None


def age_from_birth_date(birth_date):
    born = date.fromisoformat(birth_date)
    today = datetime.now(timezone.utc).date()
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))


def profile_value(text, labels):
    stop_words = (
        "Date of Birth", "Born", "Age", "Country", "Nationality", "Member ID",
        "BWF ID", "Highest Ranking", "Highest Rank", "Current Ranking",
        "World Ranking", "Career Wins", "Career Record", "Plays",
        "Handedness", "Height", "Profile", "Results", "Rankings",
    )
    stop = "|".join(re.escape(word) for word in stop_words)
    for label in labels:
        pattern = rf"{re.escape(label)}\s*:?\s*([A-Za-z0-9,.' /()-]+?)(?=\s+(?:{stop})\b|$)"
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return " ".join(match.group(1).split())
    return None


def update_from_profile(player):
    if not player.get("profile_url") and player.get("member_id"):
        player["profile_url"] = f"{BWF_BASE}/player/{player['member_id']}/{slugify(player['name'])}"
    if not player.get("profile_url"):
        return False

    html = fetch_html(player["profile_url"])
    text = flatten_profile_text(html)
    changed = False

    birth_value = profile_value(text, ("Date of Birth", "Born"))
    if not birth_value:
        match = re.search(r"\b(?:19|20)\d{2}-\d{2}-\d{2}\b", html)
        birth_value = match.group(0) if match else None
    birth_date = parse_birth_date(birth_value)
    if birth_date:
        for key in ("date_of_birth", "birth_date"):
            if player.get(key) != birth_date:
                player[key] = birth_date
                changed = True
        age = age_from_birth_date(birth_date)
        if player.get("age") != age:
            player["age"] = age
            changed = True

    country = profile_value(text, ("Country", "Nationality", "Representing"))
    if country and len(country) <= 40:
        country = country_name(country)
        if player.get("country") != country:
            player["country"] = country
            player["nationality"] = country
            changed = True

    highest = parse_int(profile_value(text, ("Highest Ranking", "Highest Rank")))
    if highest and 0 < highest < 5000 and player.get("highest_ranking") != highest:
        player["highest_ranking"] = highest
        changed = True

    current = parse_int(profile_value(text, ("Current Ranking", "World Ranking")))
    if current and 0 < current < 5000 and player.get("world_ranking") != current:
        player["world_ranking"] = current
        changed = True

    return changed


def build_database(include_profiles=True):
    errors = {}
    players_by_id = {}
    for category in RANKING_CATEGORIES:
        try:
            for player in fetch_category_players(category):
                players_by_id[player["member_id"]] = player
        except (HTTPError, URLError, TimeoutError, OSError) as error:
            errors[category["label"]] = str(error)

    players = sorted(players_by_id.values(), key=lambda item: (item["gender"], item["world_ranking"] or 9999, item["name"]))

    profile_updates = 0
    profile_errors = {}
    if include_profiles:
        for player in players:
            try:
                if update_from_profile(player):
                    profile_updates += 1
            except (HTTPError, URLError, TimeoutError, OSError, ValueError) as error:
                profile_errors[player["name"]] = str(error)

    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    verification = verify_players(players)
    return {
        **empty_database(),
        "updated_at": now if players else None,
        "last_refresh_attempt": now,
        "last_refresh_changes": {
            "ranking_players": len(players),
            "profiles": profile_updates,
        },
        "last_refresh_errors": {
            **errors,
            **({"profiles": profile_errors} if profile_errors else {}),
        },
        "players": players,
        "verification": verification,
    }


def verify_players(players, sample_size=10):
    sample = players[:sample_size]
    checked = []
    for player in sample:
        checked.append({
            "name": player["name"],
            "member_id": player["member_id"],
            "ranking_present": isinstance(player.get("world_ranking"), int),
            "points_present": isinstance(player.get("world_points"), int),
            "profile_exists": bool(player.get("profile_url")),
            "age_present": isinstance(player.get("age"), int),
        })
    return {
        "checked_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "sample_size": len(checked),
        "passed": sum(1 for item in checked if item["ranking_present"] and item["profile_exists"]),
        "players": checked,
    }


def refresh(force=False, rebuild=False):
    data = load_database()
    if not force and not rebuild and data.get("updated_at"):
        updated = datetime.fromisoformat(data["updated_at"].replace("Z", "+00:00"))
        age = (datetime.now(timezone.utc) - updated).total_seconds()
        if age < int(data.get("refresh_hours", 24)) * 3600:
            return data

    if rebuild or force or not data.get("players"):
        rebuilt = build_database(include_profiles=True)
        if rebuilt["players"]:
            atomic_write(rebuilt)
            return rebuilt
        # Keep a previous valid database if the official site blocks a refresh.
        data["last_refresh_attempt"] = rebuilt["last_refresh_attempt"]
        data["last_refresh_errors"] = rebuilt.get("last_refresh_errors", {})
        atomic_write(data)
        return data

    return data


if __name__ == "__main__":
    result = refresh(force=True, rebuild=True)
    print(json.dumps({
        "players": len(result.get("players", [])),
        "updated_at": result.get("updated_at"),
        "errors": result.get("last_refresh_errors", {}),
        "verification": result.get("verification", {}),
    }, indent=2))
