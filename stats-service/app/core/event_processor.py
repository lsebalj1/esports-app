import asyncio
import json
import logging
from decimal import Decimal
import redis.asyncio as aioredis
from app.core.config import settings
from app.core.database import get_table

logger = logging.getLogger("stats.event_processor")

CHANNELS = ["match-events", "tournament-events"]


def _update_player_stats(
    player_id: str,
    player_name: str,
    raw_stats: dict,
    won: bool,
    tournament_id: str,
    match_id: str,
):
    stats_table = get_table("PlayerStats")
    lb_table = get_table("Leaderboard")

    existing = stats_table.get_item(Key={"player_id": player_id}).get("Item", {})

    updated = {
        "player_id": player_id,
        "username": player_name or existing.get("username", player_id),
        "matches_played": int(existing.get("matches_played", 0)) + 1,
        "wins": int(existing.get("wins", 0)) + (1 if won else 0),
        "losses": int(existing.get("losses", 0)) + (0 if won else 1),
        "total_kills": int(existing.get("total_kills", 0)) + int(raw_stats.get("kills", 0)),
        "total_deaths": int(existing.get("total_deaths", 0)) + int(raw_stats.get("deaths", 0)),
        "total_assists": int(existing.get("total_assists", 0)) + int(raw_stats.get("assists", 0)),
        "total_score": float(existing.get("total_score", 0)) + float(raw_stats.get("score", 0)),
    }

    mp = updated["matches_played"]
    updated["win_rate"] = round(updated["wins"] / mp, 4) if mp else 0.0
    deaths = updated["total_deaths"]
    updated["kd_ratio"] = (
        round(updated["total_kills"] / deaths, 4) if deaths else float(updated["total_kills"])
    )

    current_rating = float(existing.get("rating", 1000))
    updated["rating"] = max(0.0, current_rating + (25 if won else -15))

    stats_table.put_item(
        Item={
            k: Decimal(str(v)) if isinstance(v, float) else v
            for k, v in updated.items()
        }
    )

    lb_entry = {
        "player_id": player_id,
        "username": updated["username"],
        "rating": Decimal(str(updated["rating"])),
        "wins": updated["wins"],
        "matches_played": mp,
        "win_rate": Decimal(str(updated["win_rate"])),
    }

    lb_table.put_item(Item={"scope": "GLOBAL", **lb_entry})
    lb_table.put_item(Item={"scope": f"TOURNAMENT#{tournament_id}", **lb_entry})

    logger.debug(
        f"  player {player_id} ({player_name}): "
        f"{'WIN' if won else 'LOSS'}, rating={updated['rating']:.0f}"
    )


def _process_match_completed(event_data: dict):
    match_id = event_data.get("match_id")
    tournament_id = event_data.get("tournament_id")
    winner_id = event_data.get("winner_id")

    if not match_id or not tournament_id or not winner_id:
        logger.warning(f"match_completed event missing required fields: {event_data}")
        return

    match_item = get_table("Matches").get_item(Key={"match_id": match_id}).get("Item")
    if not match_item:
        logger.warning(f"Match {match_id} not found in DB, skipping stats update")
        return

    team1_id = match_item.get("team1_id")
    team2_id = match_item.get("team2_id")

    teams = {
        team1_id: {
            "stats": match_item.get("team1_stats") or {},
            "won": team1_id == winner_id,
        },
        team2_id: {
            "stats": match_item.get("team2_stats") or {},
            "won": team2_id == winner_id,
        },
    }
    teams.pop(None, None)

    for team_id, team_info in teams.items():
        team_stats = team_info["stats"]
        won = team_info["won"]

        players = team_stats.get("players") or []

        if not players:
            logger.info(f"No player stats for team {team_id} in match {match_id}, skipping")
            continue

        for p in players:
            player_id = p.get("player_id")
            if not player_id:
                continue
            _update_player_stats(
                player_id=player_id,
                player_name=p.get("player_name", ""),
                raw_stats=p,
                won=won,
                tournament_id=tournament_id,
                match_id=match_id,
            )

    logger.info(
        f"Stats updated for match {match_id} "
        f"(winner team: {winner_id}, "
        f"teams processed: {list(teams.keys())})"
    )

async def start_processor():
    logger.info("Event processor starting...")
    while True:
        try:
            r = aioredis.from_url(settings.redis_url, decode_responses=True)
            pubsub = r.pubsub()
            await pubsub.subscribe(*CHANNELS)
            logger.info(f"Subscribed to channels: {CHANNELS}")

            async for message in pubsub.listen():
                if message["type"] != "message":
                    continue
                try:
                    payload = json.loads(message["data"])
                    event_type = payload.get("event_type")
                    logger.info(f"[{message['channel']}] {event_type}")
                    if event_type == "match_completed":
                        _process_match_completed(payload["data"])
                except Exception as e:
                    logger.error(f"Error processing event: {e}", exc_info=True)

        except Exception as e:
            logger.error(f"Event processor connection error: {e}. Retrying in 5s...")
            await asyncio.sleep(5)