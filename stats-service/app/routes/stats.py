from typing import List
from boto3.dynamodb.conditions import Key
from fastapi import APIRouter, HTTPException, Query
from app.core.database import get_table
from app.schemas.stats import LeaderboardEntry, LeaderboardResponse, PlayerStatsResponse

router = APIRouter(prefix="/stats", tags=["statistics"])

def _safe_float(val, default=0.0) -> float:
    try:
        return float(val)
    except (TypeError, ValueError):
        return default

def _safe_int(val, default=0) -> int:
    try:
        return int(val)
    except (TypeError, ValueError):
        return default

@router.get("/player/{player_id}", response_model=PlayerStatsResponse)
def get_player_stats(player_id: str):
    item = get_table("PlayerStats").get_item(Key={"player_id": player_id}).get("Item")
    if not item:
        raise HTTPException(status_code=404, detail="Player stats not found")
    return PlayerStatsResponse(
        player_id=item["player_id"],
        username=item.get("username", player_id),
        matches_played=_safe_int(item.get("matches_played")),
        wins=_safe_int(item.get("wins")),
        losses=_safe_int(item.get("losses")),
        win_rate=_safe_float(item.get("win_rate")),
        total_kills=_safe_int(item.get("total_kills")),
        total_deaths=_safe_int(item.get("total_deaths")),
        total_assists=_safe_int(item.get("total_assists")),
        total_score=_safe_float(item.get("total_score")),
        kd_ratio=_safe_float(item.get("kd_ratio")),
        rating=_safe_float(item.get("rating", 1000)),
    )

@router.get("/leaderboard", response_model=LeaderboardResponse)
def get_global_leaderboard(limit: int = Query(50, ge=1, le=200)):
    resp = get_table("Leaderboard").query(
        KeyConditionExpression=Key("scope").eq("GLOBAL"),
        IndexName="rating-index",
        ScanIndexForward=False,  
        Limit=limit,
    )
    entries = resp.get("Items", [])
    ranked = [
        LeaderboardEntry(
            rank= i + 1,
            player_id=e["player_id"],
            username=e.get("username", e["player_id"]),
            rating=_safe_float(e.get("rating", 1000)),
            wins=_safe_int(e.get("wins")),
            matches_played=_safe_int(e.get("matches_played")),
            win_rate=_safe_float(e.get("win_rate")),
        )
        for i, e in enumerate(entries)
    ]
    return LeaderboardResponse(scope="GLOBAL", entries=ranked)

@router.get("/leaderboard/tournament/{tournament_id}", response_model=LeaderboardResponse)
def get_tournament_leaderboard(tournament_id: str, limit: int = Query(50, ge=1, le=200)):
    scope = f"TOURNAMENT#{tournament_id}"
    resp = get_table("Leaderboard").query(
        KeyConditionExpression=Key("scope").eq(scope),
        IndexName="rating-index",
        ScanIndexForward=False,
        Limit=limit,
    )
    entries = resp.get("Items", [])
    ranked = [
        LeaderboardEntry(
            rank=i + 1,
            player_id=e["player_id"],
            username=e.get("username", e["player_id"]),
            rating=_safe_float(e.get("rating", 1000)),
            wins=_safe_int(e.get("wins")),
            matches_played=_safe_int(e.get("matches_played")),
            win_rate=_safe_float(e.get("win_rate")),
        )
        for i, e in enumerate(entries)
    ]
    return LeaderboardResponse(scope=scope, entries=ranked)

@router.get("/players", response_model=List[PlayerStatsResponse])
def list_all_player_stats(limit: int = Query(100, ge=1, le=500)):
    resp = get_table("PlayerStats").scan(Limit=limit)
    items = resp.get("Items", [])
    return [
        PlayerStatsResponse(
            player_id=item["player_id"],
            username=item.get("username", item["player_id"]),
            matches_played=_safe_int(item.get("matches_played")),
            wins=_safe_int(item.get("wins")),
            losses=_safe_int(item.get("losses")),
            win_rate=_safe_float(item.get("win_rate")),
            total_kills=_safe_int(item.get("total_kills")),
            total_deaths=_safe_int(item.get("total_deaths")),
            total_assists=_safe_int(item.get("total_assists")),
            total_score=_safe_float(item.get("total_score")),
            kd_ratio=_safe_float(item.get("kd_ratio")),
            rating=_safe_float(item.get("rating", 1000)),
        )
        for item in items
    ]
