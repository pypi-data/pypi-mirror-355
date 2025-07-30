BASE_URL = "https://rk9.gg"

def build_roster_url(tournament_code: str) -> str:
    return f"{BASE_URL}/roster/{tournament_code}"

def build_pairings_url(tournament_code: str, pod: int = 2, round_number: int = None) -> str:
    url = f"{BASE_URL}/pairings/{tournament_code}?pod={pod}"
    if round_number is not None:
        url += f"&rnd={round_number}"
    return url

def build_tournament_url(tournament_code: str) -> str:
    return f"{BASE_URL}/tournament/{tournament_code}"

def build_player_url(player_name: str) -> str:
    player_name = player_name.replace(" ", "-").lower()
    return f"{BASE_URL}/player/{player_name}"

def build_team_url(base_url: str, team_relative_url: str) -> str:
    """
    Build the full URL to a team page by combining the base tournament URL
    and the relative team URL.

    Parameters:
    - base_url: str, the base URL of the tournament, e.g. "https://rk9.gg"
    - team_relative_url: str, the relative URL of the team, e.g. "/teamlist/public/..."

    Returns:
    - Full absolute URL as a string.
    """

    # If the relative URL is already a full URL, just return it
    if team_relative_url.startswith("http"):
        return team_relative_url

    # Ensure base_url does not end with a slash
    if base_url.endswith("/"):
        base_url = base_url[:-1]

    # Ensure relative URL starts with a slash
    if not team_relative_url.startswith("/"):
        team_relative_url = "/" + team_relative_url

    # print(f"Fetching team URL: {base_url + team_relative_url}")
    return base_url + team_relative_url

from datetime import datetime
from typing import Tuple

def parse_tournament_dates(date_str: str) -> Tuple[str, str]:
    """
    Parse a tournament date string like 'August 16-18, 2024'
    and return a tuple of (start_date, end_date) in 'YYYY-MM-DD' format.
    """
    try:
        # Split month from the day range
        parts = date_str.strip().split(" ", 1)  # ['August', '16-18, 2024']
        month = parts[0]
        day_and_year = parts[1]  # '16-18, 2024'

        # Split into start and end day
        if '-' in day_and_year:
            day_range, year = day_and_year.split(", ")
            start_day, end_day = day_range.split("-")
        else:
            # Only one day (e.g. "August 16, 2024")
            start_day = end_day = day_and_year.split(",")[0]
            year = day_and_year.split(",")[1].strip()

        # Create date strings
        start_str = f"{month} {start_day.strip()}, {year}"
        end_str = f"{month} {end_day.strip()}, {year}"

        # Convert to YYYY-MM-DD
        fmt_in = "%B %d, %Y"
        fmt_out = "%Y-%m-%d"
        start_date = datetime.strptime(start_str, fmt_in).strftime(fmt_out)
        end_date = datetime.strptime(end_str, fmt_in).strftime(fmt_out)

        return start_date, end_date

    except Exception as e:
        print(f"[ERROR] Failed to parse tournament dates: {date_str}")
        raise e

