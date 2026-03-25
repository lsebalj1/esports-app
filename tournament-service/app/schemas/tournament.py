from enum import Enum
from typing import Optional
from pydantic import BaseModel

class GameEnum(str, Enum):
    cs2            = "CS2"
    valorant       = "Valorant"
    league         = "League of Legends"
    dota2          = "Dota 2"
    fortnite       = "Fortnite"
    rocket_league  = "Rocket League"
    overwatch      = "Overwatch 2"
    apex           = "Apex Legends"
    r6             = "Rainbow Six Siege"
    marvel_rivals  = "Marvel Rivals"

class TournamentFormat(str, Enum):
    single_elimination = "single_elimination"
    double_elimination = "double_elimination"
    round_robin        = "round_robin"

class CreateTournamentRequest(BaseModel):
    name: str
    game: GameEnum
    format: TournamentFormat
    max_participants: int
    prize_pool: Optional[float] = None
    start_date: str
    description: Optional[str] = None

class UpdateTournamentRequest(BaseModel):
    name: Optional[str] = None
    game: Optional[GameEnum] = None
    status: Optional[str] = None
    prize_pool: Optional[float] = None
    start_date: Optional[str] = None
    description: Optional[str] = None

class TournamentResponse(BaseModel):
    tournament_id: str
    name: str
    game: str
    format: str
    max_participants: int
    current_participants: int
    prize_pool: Optional[float] = None
    start_date: str
    status: str
    admin_id: str
    admin_name: str
    description: Optional[str] = None
    created_at: str

class BracketMatch(BaseModel):
    match_id: str
    tournament_id: str
    round: int
    position: int
    player1_id: Optional[str] = None
    player1_name: Optional[str] = None
    player2_id: Optional[str] = None
    player2_name: Optional[str] = None
    winner_id: Optional[str] = None
    status: str

class BracketResponse(BaseModel):
    tournament_id: str
    rounds: int
    matches: list[BracketMatch]