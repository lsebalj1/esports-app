from enum import Enum
from typing import Optional, List
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

GAME_TEAM_SIZE = {
    "CS2": 5,
    "Valorant": 5,
    "League of Legends": 5,
    "Dota 2": 5,
    "Fortnite": 4,  # Squad mode
    "Rocket League": 3,
    "Overwatch 2": 5,
    "Apex Legends": 3,
    "Rainbow Six Siege": 5,
    "Marvel Rivals": 6,
}

class MatchFormatEnum(str, Enum):
    bo1 = "bo1"
    bo3 = "bo3"
    bo5 = "bo5"

class TournamentFormat(str, Enum):
    single_elimination = "single_elimination"
    double_elimination = "double_elimination"
    round_robin        = "round_robin"

class TeamPlayer(BaseModel):
    player_id: str
    player_name: str
    role: Optional[str] = None  # e.g., "IGL", "Entry", "Support", "AWP"

class Team(BaseModel):
    team_id: str
    team_name: str
    players: List[TeamPlayer]
    logo_url: Optional[str] = None

class CreateTournamentRequest(BaseModel):
    name: str
    game: GameEnum
    format: TournamentFormat
    match_format: MatchFormatEnum = MatchFormatEnum.bo3
    max_teams: int = 8
    prize_pool: Optional[float] = None
    start_date: str
    description: Optional[str] = None

class UpdateTournamentRequest(BaseModel):
    name: Optional[str] = None
    game: Optional[GameEnum] = None
    status: Optional[str] = None
    match_format: Optional[MatchFormatEnum] = None
    prize_pool: Optional[float] = None
    start_date: Optional[str] = None
    description: Optional[str] = None

class TournamentResponse(BaseModel):
    tournament_id: str
    name: str
    game: str
    team_size: int
    format: str
    match_format: str
    max_teams: int
    current_teams: int
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
    match_format: str
    team1_id: Optional[str] = None
    team1_name: Optional[str] = None
    team2_id: Optional[str] = None
    team2_name: Optional[str] = None
    winner_id: Optional[str] = None
    team1_maps_won: int = 0
    team2_maps_won: int = 0
    status: str

class BracketResponse(BaseModel):
    tournament_id: str
    rounds: int
    match_format: str
    matches: List[BracketMatch]