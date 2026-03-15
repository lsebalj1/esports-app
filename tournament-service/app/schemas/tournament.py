from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field

class TournamentStatus(str, Enum):
    draft = "draft"
    registration = "registration"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"

class TournamentFormat(str, Enum):
    single_elimination = "single_elimination"
    double_elimination = "double_elimination"
    round_robin = "round_robin"

# Requests
class CreateTournamentRequest(BaseModel):
    name: str = Field(..., min_length=3, max_length=100)
    game: str = Field(..., min_length=2, max_length=50)
    format: TournamentFormat = TournamentFormat.single_elimination
    max_participants: int = Field(..., ge=2, le=256)
    prize_pool: Optional[float] = None
    start_date: str  
    description: Optional[str] = None

class UpdateTournamentRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    prize_pool: Optional[float] = None
    start_date: Optional[str] = None
    status: Optional[TournamentStatus] = None

# Responses 
class TournamentResponse(BaseModel):
    tournament_id: str
    name: str
    game: str
    format: str
    max_participants: int
    current_participants: int
    prize_pool: Optional[float]
    start_date: str
    status: str
    admin_id: str        
    admin_name: str      
    description: Optional[str]
    created_at: str

class BracketMatch(BaseModel):
    match_id: str
    round: int
    position: int
    player1_id: Optional[str] = None
    player1_name: Optional[str] = None
    player2_id: Optional[str] = None
    player2_name: Optional[str] = None
    winner_id: Optional[str] = None
    status: str = "pending"

class BracketResponse(BaseModel):
    tournament_id: str
    rounds: int
    matches: List[BracketMatch]
