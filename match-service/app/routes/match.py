from datetime import datetime, timezone
from typing import List, Optional
from boto3.dynamodb.conditions import Key
from fastapi import APIRouter, Depends, HTTPException
from app.core.auth import require_admin
from app.core.database import get_table
from app.core.events import publish_event
from app.schemas.match import CreateMatchInternal, MatchResponse, SubmitResultRequest, UpdateMatchRequest

router = APIRouter(prefix="/matches", tags=["matches"])


def _item_to_response(item: dict) -> MatchResponse:
    return MatchResponse(
        match_id=item["match_id"],
        tournament_id=item["tournament_id"],
        round=int(item["round"]),
        position=int(item["position"]),
        match_format=item.get("match_format", "bo3"),
        team1_id=item.get("team1_id"),
        team1_name=item.get("team1_name"),
        team1_players=item.get("team1_players"),
        team2_id=item.get("team2_id"),
        team2_name=item.get("team2_name"),
        team2_players=item.get("team2_players"),
        winner_id=item.get("winner_id"),
        team1_maps_won=int(item.get("team1_maps_won", 0)),
        team2_maps_won=int(item.get("team2_maps_won", 0)),
        map_results=item.get("map_results"),
        team1_stats=item.get("team1_stats"),
        team2_stats=item.get("team2_stats"),
        status=item["status"],
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
        "match_format": match.match_format.value,
        "team1_id": None,
        "team1_name": None,
        "team1_players": None,
        "team2_id": None,
        "team2_name": None,
        "team2_players": None,
        "winner_id": None,
        "team1_maps_won": 0,
        "team2_maps_won": 0,
        "map_results": None,
        "team1_stats": None,
        "team2_stats": None,
        "status": "pending",
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


@router.patch("/{match_id}/teams")
def assign_teams(
    match_id: str,
    team1_id: Optional[str] = None,
    team1_name: Optional[str] = None,
    team1_players: Optional[List[dict]] = None,
    team2_id: Optional[str] = None,
    team2_name: Optional[str] = None,
    team2_players: Optional[List[dict]] = None,
    _user: dict = Depends(require_admin)
):
    table = get_table("Matches")
    item = table.get_item(Key={"match_id": match_id}).get("Item")
    if not item:
        raise HTTPException(status_code=404, detail="Match not found")

    updates: dict = {}
    if team1_id:
        updates["team1_id"] = team1_id
    if team1_name:
        updates["team1_name"] = team1_name
    if team1_players:
        updates["team1_players"] = team1_players
    if team2_id:
        updates["team2_id"] = team2_id
    if team2_name:
        updates["team2_name"] = team2_name
    if team2_players:
        updates["team2_players"] = team2_players

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
    return {"message": "Teams assigned"}


@router.post("/{match_id}/result", response_model=MatchResponse)
async def submit_result(match_id: str, result: SubmitResultRequest, user: dict = Depends(require_admin)):
    table = get_table("Matches")
    item = table.get_item(Key={"match_id": match_id}).get("Item")
    if not item:
        raise HTTPException(status_code=404, detail="Match not found")
    if item["status"] == "completed":
        raise HTTPException(status_code=400, detail="Match already completed")

    valid_teams = {item.get("team1_id"), item.get("team2_id")} - {None}
    if result.winner_id not in valid_teams:
        raise HTTPException(status_code=400, detail="winner_id must be a match participant")

    now = datetime.now(timezone.utc).isoformat()
    t1_stats = result.team1_stats.model_dump() if result.team1_stats else None
    t2_stats = result.team2_stats.model_dump() if result.team2_stats else None
    map_results = [m.model_dump() for m in result.map_results] if result.map_results else None

    table.update_item(
        Key={"match_id": match_id},
        UpdateExpression=(
            "SET winner_id = :w, #s = :s, "
            "team1_maps_won = :t1m, team2_maps_won = :t2m, "
            "map_results = :mr, team1_stats = :t1s, team2_stats = :t2s, "
            "completed_at = :ca, duration_seconds = :d"
        ),
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={
            ":w": result.winner_id,
            ":s": "completed",
            ":t1m": result.team1_maps_won,
            ":t2m": result.team2_maps_won,
            ":mr": map_results,
            ":t1s": t1_stats,
            ":t2s": t2_stats,
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
                item.get("team2_id")
                if result.winner_id == item.get("team1_id")
                else item.get("team1_id")
            ),
            "team1_id": item.get("team1_id"),
            "team1_name": item.get("team1_name"),
            "team1_maps_won": result.team1_maps_won,
            "team2_id": item.get("team2_id"),
            "team2_name": item.get("team2_name"),
            "team2_maps_won": result.team2_maps_won,
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

@router.patch("/{match_id}", response_model=MatchResponse)
def update_match(match_id: str, payload: UpdateMatchRequest, _user: dict = Depends(require_admin)):
    table = get_table("Matches")
    item = table.get_item(Key={"match_id": match_id}).get("Item")
    if not item:
        raise HTTPException(status_code=404, detail="Match not found")

    updates = payload.model_dump(exclude_none=True)
    if not updates:
        return _item_to_response(item)

    if "status" in updates:
        allowed = {"pending", "in_progress", "completed", "cancelled"}
        if updates["status"] not in allowed:
            raise HTTPException(status_code=400, detail=f"Status must be one of {allowed}")
        if updates["status"] == "completed" and not updates.get("winner_id") and not item.get("winner_id"):
            raise HTTPException(status_code=400, detail="Cannot complete match without a winner")

    if updates.get("status") == "completed" or (updates.get("winner_id") and "status" not in updates):
        updates["status"] = "completed"
        updates["completed_at"] = datetime.now(timezone.utc).isoformat()

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
    updated = table.get_item(Key={"match_id": match_id})["Item"]
    return _item_to_response(updated)