from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

class MatchStatus(str, Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"

class PlayerMatchStats(BaseModel):
    kills: int = Field(0, ge=0)
    deaths: int = Field(0, ge=0)
    assists: int = Field(0, ge=0)
    score: float = Field(0.0, ge=0)

# Pozvano od Tournament
class CreateMatchInternal(BaseModel):
    match_id: str
    tournament_id: str
    round: int
    position: int

# Requests 
class SubmitResultRequest(BaseModel):
    winner_id: str
    player1_stats: Optional[PlayerMatchStats] = None
    player2_stats: Optional[PlayerMatchStats] = None
    duration_seconds: Optional[int] = None
    notes: Optional[str] = None

# Responses 
class MatchResponse(BaseModel):
    match_id: str
    tournament_id: str
    round: int
    position: int
    player1_id: Optional[str]
    player1_name: Optional[str]
    player2_id: Optional[str]
    player2_name: Optional[str]
    winner_id: Optional[str]
    status: str
    player1_stats: Optional[dict]
    player2_stats: Optional[dict]
    duration_seconds: Optional[int]
    scheduled_at: str
    completed_at: Optional[str]
