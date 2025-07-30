import os
import json
from dataclasses import asdict
from urllib.parse import urlparse
from .models import Tournament, PairingStatus

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, PairingStatus):
            return obj.value
        return super().default(obj)

def _extract_tournament_code(url: str) -> str:
    path = urlparse(url).path  # ex: /tournament/WCS02wi0zpmUDdrwWkd1
    return path.strip("/").split("/")[-1]

def save_players(tournament: Tournament):
    tournament_code = _extract_tournament_code(tournament.url)
    output_dir = "data"
    os.makedirs(output_dir, exist_ok=True)
    filename = f"{tournament_code}_players.json"
    output_path = os.path.join(output_dir, filename)

    data = [asdict(player) for player in tournament.players]
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, cls=CustomJSONEncoder)
    print(f"✅ Players saved to {output_path}")

def save_pairings(pairings, tournament_url: str):
    tournament_code = _extract_tournament_code(tournament_url)
    output_dir = "data"
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, f"{tournament_code}_pairings.json")

    serializable_pairings = []
    for round_pairings in pairings:
        round_data = []
        for pairing in round_pairings:
            round_data.append({
                "player1": pairing.player1,
                "player2": pairing.player2,
                "status": pairing.status.value,
                "is_bye": pairing.is_bye,
            })
        serializable_pairings.append(round_data)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(serializable_pairings, f, indent=2, ensure_ascii=False)
    print(f"✅ Pairings saved to {filepath}")

def save_info(tournament: Tournament):
    tournament_code = _extract_tournament_code(tournament.url)
    output_dir = "data"
    os.makedirs(output_dir, exist_ok=True)
    info_file = os.path.join(output_dir, f"{tournament_code}_info.json")

    info_data = {
        "name": tournament.name,
        "url": tournament.url,
        "start_date": tournament.start_date,
        "end_date": tournament.end_date,
    }

    with open(info_file, "w", encoding="utf-8") as f:
        json.dump(info_data, f, indent=2, ensure_ascii=False)

    print(f"ℹ️ Tournament info saved to {info_file}")
