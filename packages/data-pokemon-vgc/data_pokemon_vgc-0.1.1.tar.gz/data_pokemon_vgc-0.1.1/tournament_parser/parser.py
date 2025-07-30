import requests
from tqdm import tqdm
from bs4 import BeautifulSoup
from typing import List
from .models import Player, Team, Pokemon, Pairing, PairingStatus, Tournament
from .utils import (
    build_roster_url,
    build_pairings_url,
    build_tournament_url,
    build_team_url,
    parse_tournament_dates,
)


BASE_URL = "https://rk9.gg"

def get_players(tournament_code: str) -> List[Player]:
    url = build_roster_url(tournament_code)
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    players = []
    rows = soup.select("table tbody tr")

    # Filtrer d'abord les lignes "Masters" pour connaître le nombre total à traiter
    masters_rows = [row for row in rows if len(row.select("td")) >= 7 and row.select("td")[4].text.strip().lower() == "masters"]

    for row in tqdm(masters_rows, desc="Fetching teams"):
        cols = row.select("td")
        name = f"{cols[1].text.strip()} {cols[2].text.strip()} [{cols[3].text.strip()}]"
        try:
            team_href = cols[6].select_one("a")
            team_relative_url = team_href["href"] if team_href else None
            if team_relative_url:
                team = get_team(BASE_URL, team_relative_url)
            else:
                team = Team([])
            players.append(Player(name, team))
        except Exception as e:
            print(f"⚠️ Error parsing player {name}: {e}")
            continue

    return players



def get_team(base_url: str, team_relative_url: str) -> Team:
    url = build_team_url(base_url, team_relative_url)
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    pokemon_divs = soup.select("div#lang-EN div.pokemon.bg-light-green-50.p-3")
    pokemons = []

    for div in pokemon_divs:
        try:
            full_text = div.get_text(separator="\n")
            name = full_text.strip().split("\n")[0]
            tera_type = div.select_one("b:-soup-contains('Tera Type:')").next_sibling.strip()
            ability = div.select_one("b:-soup-contains('Ability:')").next_sibling.strip()
            item = div.select_one("b:-soup-contains('Held Item:')").next_sibling.strip()
            moves = [m.text for m in div.select("h5 span.badge")]

            pokemons.append(Pokemon(name, tera_type, ability, item, moves))
        except Exception as e:
            print(f"⚠️ Error parsing Pokémon: {e}")

    return Team(pokemons)


def get_number_of_rounds(tournament_code: str) -> int:
    url = build_pairings_url(tournament_code)
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    max_round = 0
    for a in soup.select("ul.nav.nav-pills li a"):
        text = a.text.strip()
        if "masters" in text.lower():
            try:
                round_num = int(text.strip().split()[-1])
                max_round = max(max_round, round_num)
            except ValueError:
                pass

    return max_round


def get_pairings_for_round(tournament_code: str, round_number: int, pod: int = 2) -> List[Pairing]:
    url = build_pairings_url(tournament_code, pod, round_number)
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    pairings = []
    matches = soup.select("div.row.row-cols-3.match.no-gutter.complete")

    for match in matches:
        player1_div = match.select_one("div.player1")
        player2_div = match.select_one("div.player2")

        player1_name = player1_div.select_one("span.name").text.strip() if player1_div.select_one("span.name") else ""
        
        player2_name_tag = player2_div.select_one("span.name")
        player2_name = player2_name_tag.text.strip() if player2_name_tag else ""

        is_bye = player2_name == ""

        player1_won = "winner" in player1_div.get("class", [])
        player2_won = "winner" in player2_div.get("class", [])
        tie = "tie" in player1_div.get("class", []) and "tie" in player2_div.get("class", [])

        if player1_won:
            status = PairingStatus.PLAYER1_WON
        elif player2_won:
            status = PairingStatus.PLAYER2_WON
        elif tie:
            status = PairingStatus.DRAW
        else:
            status = PairingStatus.IN_PROGRESS

        pairings.append(Pairing(player1_name, player2_name, status, is_bye))

    return pairings



def get_all_pairings(tournament_code: str) -> List[List[Pairing]]:
    num_rounds = get_number_of_rounds(tournament_code)
    return [get_pairings_for_round(tournament_code, rnd) for rnd in range(1, num_rounds + 1)]


def create_tournament(tournament_code: str, base_url: str = "https://rk9.gg") -> Tournament:
    tournament_url = f"{base_url}/tournament/{tournament_code}"
    response = requests.get(tournament_url)
    if response.status_code != 200:
        raise ValueError(f"[ERROR] Failed to load tournament page: {tournament_url}")
    doc = BeautifulSoup(response.content, "html.parser")

    name_tag = doc.select_one("h3.mb-0")
    if name_tag is None:
        raise ValueError("[ERROR] Could not find tournament name (h3.mb-0). The page structure may have changed.")
    name = name_tag.contents[0].strip() if name_tag else "Unknown Tournament"

    date_raw = name_tag.select_one("small").get_text(strip=True)
    date_clean = date_raw.split("Time zone")[0].strip()
    start_date, end_date = parse_tournament_dates(date_clean)

    players = get_players(tournament_code)
    pairings = get_all_pairings(tournament_code)

    return Tournament(name, tournament_url, start_date, end_date, pairings, players)

