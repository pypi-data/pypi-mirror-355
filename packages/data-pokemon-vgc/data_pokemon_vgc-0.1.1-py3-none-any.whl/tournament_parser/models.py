from dataclasses import dataclass
from typing import List
from enum import Enum

class PairingStatus(Enum):
    PLAYER1_WON = "PLAYER1_WON"
    PLAYER2_WON = "PLAYER2_WON"
    DRAW = "DRAW"
    IN_PROGRESS = "IN_PROGRESS"

@dataclass
class Pokemon:
    name: str
    tera_type: str
    ability: str
    item: str
    moves: List[str]

@dataclass
class Team:
    pokemons: List[Pokemon]

@dataclass
class Player:
    name: str
    team: Team

@dataclass
class Pairing:
    player1: str
    player2: str
    status: PairingStatus
    is_bye: bool

@dataclass
class Tournament:
    name: str
    url: str
    start_date: str
    end_date: str
    pairings: List[List[Pairing]]
    players: List[Player]
