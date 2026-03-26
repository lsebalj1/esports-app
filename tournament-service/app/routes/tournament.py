import math
import uuid
import random
from datetime import datetime, timezone
from typing import List, Optional
import httpx
from boto3.dynamodb.conditions import Key
from fastapi import APIRouter, Depends, HTTPException, Query
from app.core.auth import require_admin
from app.core.config import settings
from app.core.database import get_table
from app.core.events import publish_event
from app.schemas.tournament import (
    BracketMatch, BracketResponse, CreateTournamentRequest, 
    TournamentResponse, UpdateTournamentRequest, GAME_TEAM_SIZE
)

router = APIRouter(prefix="/tournaments", tags=["tournaments"])

def _tournament_to_response(item: dict) -> TournamentResponse:
    game = item["game"]
    team_size = GAME_TEAM_SIZE.get(game, 5)
    return TournamentResponse(
        tournament_id=item["tournament_id"],
        name=item["name"],
        game=game,
        team_size=team_size,
        format=item["format"],
        match_format=item.get("match_format", "bo3"),
        max_teams=int(item.get("max_teams", item.get("max_participants", 8))),
        current_teams=int(item.get("current_teams", item.get("current_participants", 0))),
        prize_pool=float(item["prize_pool"]) if item.get("prize_pool") else None,
        start_date=item["start_date"],
        status=item["status"],
        admin_id=item["admin_id"],
        admin_name=item["admin_name"],
        description=item.get("description"),
        created_at=item["created_at"],
    )

async def _create_match_in_service(tournament_id: str, round_num: int, position: int, match_format: str = "bo3") -> str:
    match_id = str(uuid.uuid4())
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{settings.match_service_url}/matches/internal",
                json={
                    "match_id": match_id,
                    "tournament_id": tournament_id,
                    "round": round_num,
                    "position": position,
                    "match_format": match_format,
                },
                timeout=5.0,
            )
    except Exception:
        pass
    return match_id

@router.post("", response_model=TournamentResponse, status_code=201)
async def create_tournament(payload: CreateTournamentRequest, user: dict = Depends(require_admin)):
    tournament_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    game = payload.game.value
    team_size = GAME_TEAM_SIZE.get(game, 5)
    
    item = {
        "tournament_id": tournament_id,
        "name": payload.name,
        "game": game,
        "team_size": team_size,
        "format": payload.format.value,
        "match_format": payload.match_format.value,
        "max_teams": payload.max_teams,
        "current_teams": 0,
        "teams": [],
        "prize_pool": str(payload.prize_pool) if payload.prize_pool else None,
        "start_date": payload.start_date,
        "status": "registration",
        "admin_id": user["user_id"],
        "admin_name": user["username"],
        "description": payload.description,
        "created_at": now,
        "updated_at": now,
    }
    get_table("Tournaments").put_item(Item=item)

    await publish_event(
        "tournament-events",
        "tournament_created",
        {
            "tournament_id": tournament_id,
            "name": payload.name,
            "game": game,
            "team_size": team_size,
            "admin_id": user["user_id"],
        },
    )
    return _tournament_to_response(item)

@router.get("", response_model=List[TournamentResponse])
def list_tournaments(status: Optional[str] = Query(None), game: Optional[str] = Query(None)):
    table = get_table("Tournaments")
    if status:
        resp = table.query(
            IndexName="status-index",
            KeyConditionExpression=Key("status").eq(status),
        )
        items = resp.get("Items", [])
    else:
        resp = table.scan()
        items = resp.get("Items", [])

    if game:
        items = [i for i in items if i.get("game", "").lower() == game.lower()]

    return [_tournament_to_response(i) for i in items]

@router.get("/{tournament_id}", response_model=TournamentResponse)
def get_tournament(tournament_id: str):
    item = get_table("Tournaments").get_item(
        Key={"tournament_id": tournament_id}
    ).get("Item")
    if not item:
        raise HTTPException(status_code=404, detail="Tournament not found")
    return _tournament_to_response(item)

@router.patch("/{tournament_id}", response_model=TournamentResponse)
def update_tournament(tournament_id: str, payload: UpdateTournamentRequest, user: dict = Depends(require_admin)):
    table = get_table("Tournaments")
    item = table.get_item(Key={"tournament_id": tournament_id}).get("Item")
    if not item:
        raise HTTPException(status_code=404, detail="Tournament not found")
    if item["admin_id"] != user["user_id"] and user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Not your tournament")

    updates = payload.model_dump(exclude_none=True)
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    if "game" in updates:
        updates["game"] = updates["game"].value
    if "match_format" in updates:
        updates["match_format"] = updates["match_format"].value

    expr_parts, names, values = [], {}, {}
    for i, (k, v) in enumerate(updates.items()):
        expr_parts.append(f"#{k} = :v{i}")
        names[f"#{k}"] = k
        values[f":v{i}"] = str(v) if isinstance(v, float) else v

    table.update_item(
        Key={"tournament_id": tournament_id},
        UpdateExpression="SET " + ", ".join(expr_parts),
        ExpressionAttributeNames=names,
        ExpressionAttributeValues=values,
    )
    updated = table.get_item(Key={"tournament_id": tournament_id})["Item"]
    return _tournament_to_response(updated)

@router.post("/{tournament_id}/bracket/generate", response_model=BracketResponse)
async def generate_bracket(tournament_id: str, user: dict = Depends(require_admin)):
    table = get_table("Tournaments")
    item = table.get_item(Key={"tournament_id": tournament_id}).get("Item")
    if not item:
        raise HTTPException(status_code=404, detail="Tournament not found")
    if item["admin_id"] != user["user_id"] and user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Not your tournament")
    if item["status"] not in ("registration", "draft"):
        raise HTTPException(status_code=400, detail="Cannot generate bracket now")

    teams: list = item.get("teams", [])
    if len(teams) < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 teams")

    random.shuffle(teams)
    match_format = item.get("match_format", "bo3")

    n = 2 ** math.ceil(math.log2(len(teams)))
    padded = teams + [None] * (n - len(teams))

    rounds = int(math.log2(n))
    all_matches: list[dict] = []

    round_teams = padded
    for round_num in range(1, rounds + 1):
        next_round = []
        for pos, (t1, t2) in enumerate(zip(round_teams[::2], round_teams[1::2]), start=1):
            match_id = await _create_match_in_service(tournament_id, round_num, pos, match_format)
            match = {
                "match_id": match_id,
                "tournament_id": tournament_id,
                "round": round_num,
                "position": pos,
                "match_format": match_format,
                "team1_id": t1["team_id"] if t1 else None,
                "team1_name": t1["team_name"] if t1 else "BYE",
                "team2_id": t2["team_id"] if t2 else None,
                "team2_name": t2["team_name"] if t2 else "BYE",
                "winner_id": None,
                "team1_maps_won": 0,
                "team2_maps_won": 0,
                "status": "pending",
            }

            if t1 and not t2:
                match["winner_id"] = t1["team_id"]
                match["status"] = "completed"
                next_round.append(t1)
            elif t2 and not t1:
                match["winner_id"] = t2["team_id"]
                match["status"] = "completed"
                next_round.append(t2)
            else:
                next_round.append(None)
            all_matches.append(match)
        round_teams = next_round

    table.update_item(
        Key={"tournament_id": tournament_id},
        UpdateExpression="SET #s = :s, bracket = :b",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={":s": "in_progress", ":b": all_matches},
    )

    await publish_event(
        "tournament-events",
        "bracket_generated",
        {"tournament_id": tournament_id, "rounds": rounds, "match_count": len(all_matches)},
    )

    return BracketResponse(
        tournament_id=tournament_id,
        rounds=rounds,
        match_format=match_format,
        matches=[BracketMatch(**m) for m in all_matches],
    )


@router.get("/{tournament_id}/bracket", response_model=BracketResponse)
def get_bracket(tournament_id: str):
    item = get_table("Tournaments").get_item(
        Key={"tournament_id": tournament_id}
    ).get("Item")
    if not item:
        raise HTTPException(status_code=404, detail="Tournament not found")
    bracket = item.get("bracket", [])
    if not bracket:
        raise HTTPException(status_code=404, detail="Bracket not generated yet")
    rounds = max(m["round"] for m in bracket) if bracket else 0
    match_format = item.get("match_format", "bo3")
    return BracketResponse(
        tournament_id=tournament_id,
        rounds=rounds,
        match_format=match_format,
        matches=[BracketMatch(**m) for m in bracket],
    )