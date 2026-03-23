from typing import List
from pydantic import BaseModel

class PlayerStatsResponse(BaseModel):
    player_id: str
    username: str
    matches_played: int
    wins: int
    losses: int
    win_rate: float
    total_kills: int
    total_deaths: int
    total_assists: int
    total_score: float
    kd_ratio: float
    rating: float

class LeaderboardEntry(BaseModel):
    rank: int
    player_id: str
    username: str
    rating: float
    wins: int
    matches_played: int
    win_rate: float

class LeaderboardResponse(BaseModel):
    scope: str
    entries: List[LeaderboardEntry]
