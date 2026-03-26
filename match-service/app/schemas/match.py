from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field

class MatchStatus(str, Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"

class MatchFormat(str, Enum):
    bo1 = "bo1"
    bo3 = "bo3"
    bo5 = "bo5"

class PlayerMatchStats(BaseModel):
    player_id: str
    player_name: str
    kills: int = Field(0, ge=0)
    deaths: int = Field(0, ge=0)
    assists: int = Field(0, ge=0)
    score: float = Field(0.0, ge=0)

class TeamMatchStats(BaseModel):
    players: List[PlayerMatchStats] = []
    total_kills: int = 0
    total_deaths: int = 0
    total_score: float = 0

class MapResult(BaseModel):
    map_number: int
    map_name: Optional[str] = None
    winner_team_id: str
    team1_score: int = 0  # rounds won
    team2_score: int = 0

class CreateMatchInternal(BaseModel):
    match_id: str
    tournament_id: str
    round: int
    position: int
    match_format: MatchFormat = MatchFormat.bo3


class SubmitResultRequest(BaseModel):
    winner_id: str
    team1_maps_won: int = Field(0, ge=0)
    team2_maps_won: int = Field(0, ge=0)
    map_results: Optional[List[MapResult]] = None
    team1_stats: Optional[TeamMatchStats] = None
    team2_stats: Optional[TeamMatchStats] = None
    duration_seconds: Optional[int] = None
    notes: Optional[str] = None


class MatchResponse(BaseModel):
    match_id: str
    tournament_id: str
    round: int
    position: int
    match_format: str
    # Team 1
    team1_id: Optional[str]
    team1_name: Optional[str]
    team1_players: Optional[List[dict]] = None
    # Team 2
    team2_id: Optional[str]
    team2_name: Optional[str]
    team2_players: Optional[List[dict]] = None
    # Result
    winner_id: Optional[str]
    team1_maps_won: int = 0
    team2_maps_won: int = 0
    map_results: Optional[List[dict]] = None
    # Stats
    team1_stats: Optional[dict] = None
    team2_stats: Optional[dict] = None
    status: str
    duration_seconds: Optional[int] = None
    scheduled_at: str
    completed_at: Optional[str] = None