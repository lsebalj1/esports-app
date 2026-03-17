from datetime import datetime, timezone
from typing import List, Optional
from boto3.dynamodb.conditions import Key
from fastapi import APIRouter, Depends, HTTPException
from app.core.auth import require_admin
from app.core.database import get_table
from app.core.events import publish_event
from app.schemas.match import (CreateMatchInternal, MatchResponse, SubmitResultRequest)
 
router = APIRouter(prefix="/matches", tags=["matches"])
 
def _item_to_response(item: dict) -> MatchResponse:
    return MatchResponse(
        match_id=item["match_id"],
        tournament_id=item["tournament_id"],
        round=int(item["round"]),
        position=int(item["position"]),
        player1_id=item.get("player1_id"),
        player1_name=item.get("player1_name"),
        player2_id=item.get("player2_id"),
        player2_name=item.get("player2_name"),
        winner_id=item.get("winner_id"),
        status=item["status"],
        player1_stats=item.get("player1_stats"),
        player2_stats=item.get("player2_stats"),
        duration_seconds=int(item["duration_seconds"]) if item.get("duration_seconds") else None,
        scheduled_at=item["scheduled_at"],
        completed_at=item.get("completed_at"),
    )
 
@router.post("/internal", include_in_schema=False, status_code=201)
def create_match_internal(match: CreateMatchInternal):
    now = datetime.now(timezone.utc).isoformat()
    item = {
        "match_id": match.match_id,
        "tournament_id": match.tournament_id,
        "round": match.round,
        "position": match.position,
        "player1_id": None,
        "player1_name": None,
        "player2_id": None,
        "player2_name": None,
        "winner_id": None,
        "status": "pending",
        "player1_stats": None,
        "player2_stats": None,
        "duration_seconds": None,
        "scheduled_at": now,
        "completed_at": None,
    }
    get_table("Matches").put_item(Item=item)
    return {"match_id": match.match_id}
 
@router.get("/tournament/{tournament_id}", response_model=List[MatchResponse])
def list_matches_by_tournament(tournament_id: str):
    resp = get_table("Matches").query(
        IndexName="tournament-index",
        KeyConditionExpression=Key("tournament_id").eq(tournament_id),
    )
    items = sorted(resp.get("Items", []), key=lambda x: (int(x["round"]), int(x["position"])))
    return [_item_to_response(i) for i in items]
 
@router.get("/{match_id}", response_model=MatchResponse)
def get_match(match_id: str):
    item = get_table("Matches").get_item(Key={"match_id": match_id}).get("Item")
    if not item:
        raise HTTPException(status_code=404, detail="Match not found")
    return _item_to_response(item)
 
 
@router.patch("/{match_id}/players")
def assign_players(match_id: str, player1_id: Optional[str] = None, player1_name: Optional[str] = None, player2_id: Optional[str] = None, player2_name: Optional[str] = None, _user: dict = Depends(require_admin)):
    table = get_table("Matches")
    item = table.get_item(Key={"match_id": match_id}).get("Item")
    if not item:
        raise HTTPException(status_code=404, detail="Match not found")
 
    updates: dict = {}
    if player1_id:
        updates["player1_id"] = player1_id
    if player1_name:
        updates["player1_name"] = player1_name
    if player2_id:
        updates["player2_id"] = player2_id
    if player2_name:
        updates["player2_name"] = player2_name
 
    if not updates:
        return {"message": "Nothing to update"}
 
    expr_parts, names, values = [], {}, {}
    for i, (k, v) in enumerate(updates.items()):
        expr_parts.append(f"#{k} = :v{i}")
        names[f"#{k}"] = k
        values[f":v{i}"] = v
 
    table.update_item(
        Key={"match_id": match_id},
        UpdateExpression="SET " + ", ".join(expr_parts),
        ExpressionAttributeNames=names,
        ExpressionAttributeValues=values,
    )
    return {"message": "Players assigned"}
 
@router.post("/{match_id}/result", response_model=MatchResponse)
async def submit_result(match_id: str, result: SubmitResultRequest, user: dict = Depends(require_admin)):
    
    table = get_table("Matches")
    item = table.get_item(Key={"match_id": match_id}).get("Item")
    if not item:
        raise HTTPException(status_code=404, detail="Match not found")
    if item["status"] == "completed":
        raise HTTPException(status_code=400, detail="Match already completed")
 
    valid_players = {item.get("player1_id"), item.get("player2_id")} - {None}
    if result.winner_id not in valid_players:
        raise HTTPException(status_code=400, detail="winner_id must be a match participant")
 
    now = datetime.now(timezone.utc).isoformat()
    p1_stats = result.player1_stats.model_dump() if result.player1_stats else None
    p2_stats = result.player2_stats.model_dump() if result.player2_stats else None
 
    table.update_item(
        Key={"match_id": match_id},
        UpdateExpression=(
            "SET winner_id = :w, #s = :s, player1_stats = :p1, "
            "player2_stats = :p2, completed_at = :ca, duration_seconds = :d"
        ),
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={
            ":w": result.winner_id,
            ":s": "completed",
            ":p1": p1_stats,
            ":p2": p2_stats,
            ":ca": now,
            ":d": result.duration_seconds,
        },
    )
 
    updated = table.get_item(Key={"match_id": match_id})["Item"]
 
    await publish_event(
        "match-events",
        "match_completed",
        {
            "match_id": match_id,
            "tournament_id": item["tournament_id"],
            "round": int(item["round"]),
            "winner_id": result.winner_id,
            "loser_id": (
                item.get("player2_id")
                if result.winner_id == item.get("player1_id")
                else item.get("player1_id")
            ),
            "player1_id": item.get("player1_id"),
            "player1_name": item.get("player1_name"),
            "player1_stats": p1_stats,
            "player2_id": item.get("player2_id"),
            "player2_name": item.get("player2_name"),
            "player2_stats": p2_stats,
            "duration_seconds": result.duration_seconds,
            "completed_at": now,
        },
    )
 
    return _item_to_response(updated)
 
@router.patch("/{match_id}/status")
def update_match_status(match_id: str, status: str, _user: dict = Depends(require_admin)):

    table = get_table("Matches")
    item = table.get_item(Key={"match_id": match_id}).get("Item")
    if not item:
        raise HTTPException(status_code=404, detail="Match not found")
 
    allowed = {"pending", "in_progress", "cancelled"}
    if status not in allowed:
        raise HTTPException(status_code=400, detail=f"Status must be one of {allowed}")
 
    table.update_item(
        Key={"match_id": match_id},
        UpdateExpression="SET #s = :s",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={":s": status},
    )
    return {"message": f"Match status updated to {status}"}