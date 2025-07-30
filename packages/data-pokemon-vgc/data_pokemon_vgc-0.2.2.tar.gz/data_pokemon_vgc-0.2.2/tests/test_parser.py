import pytest
from unittest.mock import patch, Mock
from parser.parser import create_tournament
import os


TEST_HTML_PATH = os.path.join(os.path.dirname(__file__), "testdata", "tournament_page.html")

def load_html(filepath: str) -> str:
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()

@patch("tournament_parser.parser.requests.get")
@patch("tournament_parser.parser.get_players", return_value=[])
@patch("tournament_parser.parser.get_all_pairings", return_value=[])
def test_parse_dates_from_local_html(mock_pairings, mock_players, mock_requests_get):
    # Charge le fichier de test local
    html = load_html(TEST_HTML_PATH)

    # Mock la réponse de requests.get
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.content = html.encode("utf-8")
    mock_requests_get.return_value = mock_response

    # Appelle la fonction
    tournament = create_tournament("dummy-code")

    # Vérifie les dates extraites
    assert tournament.start_date == "2025-06-13"
    assert tournament.end_date == "2025-06-15"
