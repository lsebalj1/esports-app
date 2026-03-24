import asyncio
import json
import logging
from decimal import Decimal
import redis.asyncio as aioredis
from app.core.config import settings
from app.core.database import get_table

logger = logging.getLogger("stats.event_processor")

CHANNELS = ["match-events", "tournament-events"]

def _process_match_completed(event_data: dict):
    tournament_id = event_data["tournament_id"]
    winner_id = event_data.get("winner_id")

    players = {
        event_data.get("player1_id"): {
            "stats": event_data.get("player1_stats") or {},
            "won": event_data.get("player1_id") == winner_id,
            "name": event_data.get("player1_name", ""),
        },
        event_data.get("player2_id"): {
            "stats": event_data.get("player2_stats") or {},
            "won": event_data.get("player2_id") == winner_id,
            "name": event_data.get("player2_name", ""),
        },
    }
    players.pop(None, None)

    stats_table = get_table("PlayerStats")
    lb_table = get_table("Leaderboard")

    for player_id, info in players.items():
        existing = stats_table.get_item(Key={"player_id": player_id}).get("Item", {})
        raw = info["stats"]

        updated = {
            "player_id": player_id,
            "username": info["name"] or existing.get("username", player_id),
            "matches_played": int(existing.get("matches_played", 0)) + 1,
            "wins": int(existing.get("wins", 0)) + (1 if info["won"] else 0),
            "losses": int(existing.get("losses", 0)) + (0 if info["won"] else 1),
            "total_kills": int(existing.get("total_kills", 0)) + int(raw.get("kills", 0)),
            "total_deaths": int(existing.get("total_deaths", 0)) + int(raw.get("deaths", 0)),
            "total_assists": int(existing.get("total_assists", 0)) + int(raw.get("assists", 0)),
        }

        mp = updated["matches_played"]
        updated["win_rate"] = round(updated["wins"] / mp, 4) if mp else 0.0
        deaths = updated["total_deaths"]
        updated["kd_ratio"] = round(updated["total_kills"] / deaths, 4) if deaths else float(updated["total_kills"])

        current_rating = float(existing.get("rating", 1000))
        updated["rating"] = max(0.0, current_rating + (25 if info["won"] else -15))

        stats_table.put_item(Item={
            k: Decimal(str(v)) if isinstance(v, float) else v
            for k, v in updated.items()
        })

        lb_table.put_item(Item={
            "scope": "GLOBAL",
            "player_id": player_id,
            "username": updated["username"],
            "rating": Decimal(str(updated["rating"])),
            "wins": updated["wins"],
            "matches_played": mp,
            "win_rate": Decimal(str(updated["win_rate"])),
        })

        lb_table.put_item(Item={
            "scope": f"TOURNAMENT#{tournament_id}",
            "player_id": player_id,
            "username": updated["username"],
            "rating": Decimal(str(updated["rating"])),
            "wins": updated["wins"],
            "matches_played": mp,
            "win_rate": Decimal(str(updated["win_rate"])),
        })

    logger.info(f"Stats updated for match {event_data['match_id']}")

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
                    logger.error(f"Error processing event: {e}")

        except Exception as e:
            logger.error(f"Event processor connection error: {e}. Retrying in 5s...")
            await asyncio.sleep(5)