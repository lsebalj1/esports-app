import boto3
import uuid
import random
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from passlib.context import CryptContext
import os

ENDPOINT = os.getenv("DYNAMODB_ENDPOINT", "http://localhost:8000")
REGION = "eu-central-1"

dynamodb = boto3.resource(
    "dynamodb",
    endpoint_url=ENDPOINT,
    region_name=REGION,
    aws_access_key_id="local",
    aws_secret_access_key="local",
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def now(offset_days=0):
    return (datetime.now(timezone.utc) + timedelta(days=offset_days)).isoformat()

def uid():
    return str(uuid.uuid4())

print("Kreiranje korisnika...")

users_table = dynamodb.Table("Users")

USERS = [
    {"username": "admin",        "email": "admin@esports.com",  "role": "admin"},
    {"username": "mod_marko",    "email": "marko@esports.com",  "role": "admin"},
    {"username": "sniper_king",  "email": "sniper@test.com",    "role": "observer"},
    {"username": "headshot_hr",  "email": "headshot@test.com",  "role": "observer"},
    {"username": "rush_b_only",  "email": "rushb@test.com",     "role": "observer"},
    {"username": "pro_lurker",   "email": "lurker@test.com",    "role": "observer"},
    {"username": "awp_god",      "email": "awp@test.com",       "role": "observer"},
    {"username": "flash_out",    "email": "flash@test.com",     "role": "observer"},
    {"username": "smoke_master", "email": "smoke@test.com",     "role": "observer"},
    {"username": "entry_frag",   "email": "entry@test.com",     "role": "observer"},
]

created_users = []
for u in USERS:
    user_id = uid()
    item = {
        "user_id": user_id,
        "username": u["username"],
        "email": u["email"],
        "password_hash": pwd_context.hash("lozinka123"),
        "role": u["role"],
        "is_active": True,
        "created_at": now(-30),
        "updated_at": now(-30),
    }
    users_table.put_item(Item=item)
    created_users.append(item)
    print(f"  {u['role']:10} {u['username']:15} — {u['email']}")

admins = [u for u in created_users if u["role"] == "admin"]
observers = [u for u in created_users if u["role"] == "observer"]

print("\nKreiranje turnira...")

tournaments_table = dynamodb.Table("Tournaments")
admin = admins[0]

TOURNAMENTS = [
    {
        "name": "Zagreb Open 2025",
        "game": "CS2",
        "format": "single_elimination",
        "max_participants": 8,
        "prize_pool": "1000.00",
        "status": "completed",
        "start_date": now(-14),
        "description": "Otvoreni turnir za sve igrace iz Hrvatske.",
    },
    {
        "name": "Adriatic Cup",
        "game": "Marvel Rivals",
        "format": "single_elimination",
        "max_participants": 8,
        "prize_pool": "500.00",
        "status": "in_progress",
        "start_date": now(-3),
        "description": "Regionalni turnir Jadranskog podrucja.",
    },
    {
        "name": "Summer Frag Fest",
        "game": "Valorant",
        "format": "single_elimination",
        "max_participants": 8,
        "prize_pool": "250.00",
        "status": "registration",
        "start_date": now(7),
        "description": "Ljetni turnir u Valorantu.",
    },
    {
        "name": "Pro League Season 3",
        "game": "CS2",
        "format": "round_robin",
        "max_participants": 8,
        "prize_pool": "2000.00",
        "status": "draft",
        "start_date": now(30),
        "description": "Profesionalna liga — sezona 3.",
    },
]

created_tournaments = []
for t in TOURNAMENTS:
    t_id = uid()
    participants = [{"user_id": u["user_id"], "username": u["username"]} for u in observers]
    item = {
        "tournament_id": t_id,
        "name": t["name"],
        "game": t["game"],
        "format": t["format"],
        "max_participants": t["max_participants"],
        "current_participants": len(participants),
        "participants": participants,
        "prize_pool": t["prize_pool"],
        "status": t["status"],
        "admin_id": admin["user_id"],
        "admin_name": admin["username"],
        "start_date": t["start_date"],
        "description": t["description"],
        "created_at": now(-20),
        "updated_at": now(-1),
    }
    tournaments_table.put_item(Item=item)
    created_tournaments.append(item)
    print(f"[{t['status']:14}] {t['name']} ({t['game']})")

print("\nKreiranje meceva...")

matches_table = dynamodb.Table("Matches")

def make_stats(won=False):
    if won:
        return {
            "kills": random.randint(18, 30),
            "deaths": random.randint(5, 14),
            "assists": random.randint(3, 10),
            "score": random.randint(2500, 4000),
        }
    else:
        return {
            "kills": random.randint(5, 17),
            "deaths": random.randint(15, 28),
            "assists": random.randint(1, 8),
            "score": random.randint(800, 2400),
        }

created_matches = []

completed_t = created_tournaments[0]
t_players = observers.copy()
random.shuffle(t_players)

r1_winners = []
for pos, (p1, p2) in enumerate(zip(t_players[::2], t_players[1::2]), start=1):
    winner = random.choice([p1, p2])
    m_id = uid()
    match = {
        "match_id": m_id,
        "tournament_id": completed_t["tournament_id"],
        "round": 1,
        "position": pos,
        "player1_id": p1["user_id"],
        "player1_name": p1["username"],
        "player2_id": p2["user_id"],
        "player2_name": p2["username"],
        "winner_id": winner["user_id"],
        "status": "completed",
        "player1_stats": make_stats(p1 == winner),
        "player2_stats": make_stats(p2 == winner),
        "duration_seconds": random.randint(1200, 3600),
        "scheduled_at": now(-14),
        "completed_at": now(-13),
    }
    matches_table.put_item(Item=match)
    created_matches.append(match)
    r1_winners.append(winner)
    print(f"R1M{pos} {p1['username']:15} vs {p2['username']:15} -> {winner['username']}")

r2_winners = []
for pos, (p1, p2) in enumerate(zip(r1_winners[::2], r1_winners[1::2]), start=1):
    winner = random.choice([p1, p2])
    m_id = uid()
    match = {
        "match_id": m_id,
        "tournament_id": completed_t["tournament_id"],
        "round": 2,
        "position": pos,
        "player1_id": p1["user_id"],
        "player1_name": p1["username"],
        "player2_id": p2["user_id"],
        "player2_name": p2["username"],
        "winner_id": winner["user_id"],
        "status": "completed",
        "player1_stats": make_stats(p1 == winner),
        "player2_stats": make_stats(p2 == winner),
        "duration_seconds": random.randint(1800, 4200),
        "scheduled_at": now(-12),
        "completed_at": now(-11),
    }
    matches_table.put_item(Item=match)
    created_matches.append(match)
    r2_winners.append(winner)
    print(f"R2M{pos} {p1['username']:15} vs {p2['username']:15} -> {winner['username']}")

p1, p2 = r2_winners[0], r2_winners[1]
champion = random.choice([p1, p2])
m_id = uid()
final_match = {
    "match_id": m_id,
    "tournament_id": completed_t["tournament_id"],
    "round": 3,
    "position": 1,
    "player1_id": p1["user_id"],
    "player1_name": p1["username"],
    "player2_id": p2["user_id"],
    "player2_name": p2["username"],
    "winner_id": champion["user_id"],
    "status": "completed",
    "player1_stats": make_stats(p1 == champion),
    "player2_stats": make_stats(p2 == champion),
    "duration_seconds": random.randint(2400, 5400),
    "scheduled_at": now(-10),
    "completed_at": now(-10),
}
matches_table.put_item(Item=final_match)
created_matches.append(final_match)
print(f"FINALE {p1['username']:15} vs {p2['username']:15} -> pobjednik: {champion['username']}")

in_progress_t = created_tournaments[1]
t_players2 = observers.copy()
random.shuffle(t_players2)

r1w_2 = []
for pos, (p1, p2) in enumerate(zip(t_players2[::2], t_players2[1::2]), start=1):
    winner = random.choice([p1, p2])
    m_id = uid()
    match = {
        "match_id": m_id,
        "tournament_id": in_progress_t["tournament_id"],
        "round": 1,
        "position": pos,
        "player1_id": p1["user_id"],
        "player1_name": p1["username"],
        "player2_id": p2["user_id"],
        "player2_name": p2["username"],
        "winner_id": winner["user_id"],
        "status": "completed",
        "player1_stats": make_stats(p1 == winner),
        "player2_stats": make_stats(p2 == winner),
        "duration_seconds": random.randint(1200, 3600),
        "scheduled_at": now(-3),
        "completed_at": now(-2),
    }
    matches_table.put_item(Item=match)
    created_matches.append(match)
    r1w_2.append(winner)

for pos, (p1, p2) in enumerate(zip(r1w_2[::2], r1w_2[1::2]), start=1):
    m_id = uid()
    match = {
        "match_id": m_id,
        "tournament_id": in_progress_t["tournament_id"],
        "round": 2,
        "position": pos,
        "player1_id": p1["user_id"],
        "player1_name": p1["username"],
        "player2_id": p2["user_id"],
        "player2_name": p2["username"],
        "winner_id": None,
        "status": "pending",
        "player1_stats": None,
        "player2_stats": None,
        "duration_seconds": None,
        "scheduled_at": now(1),
        "completed_at": None,
    }
    matches_table.put_item(Item=match)
    created_matches.append(match)

print(f"Adriatic Cup: runda 1 zavrsena, runda 2 pending")

print("\nRacunanje statistika...")

player_stats_table = dynamodb.Table("PlayerStats")
leaderboard_table = dynamodb.Table("Leaderboard")

stats_agg = {}

for match in created_matches:
    if match["status"] != "completed":
        continue

    for pid, pname, pstats, is_winner in [
        (match["player1_id"], match["player1_name"], match.get("player1_stats"), match["winner_id"] == match["player1_id"]),
        (match["player2_id"], match["player2_name"], match.get("player2_stats"), match["winner_id"] == match["player2_id"]),
    ]:
        if not pid or not pstats:
            continue

        if pid not in stats_agg:
            stats_agg[pid] = {
                "player_id": pid,
                "username": pname,
                "matches_played": 0,
                "wins": 0,
                "losses": 0,
                "total_kills": 0,
                "total_deaths": 0,
                "total_assists": 0,
                "rating": 1000.0,
            }

        s = stats_agg[pid]
        s["matches_played"] += 1
        s["wins"] += 1 if is_winner else 0
        s["losses"] += 0 if is_winner else 1
        s["total_kills"] += pstats.get("kills", 0)
        s["total_deaths"] += pstats.get("deaths", 0)
        s["total_assists"] += pstats.get("assists", 0)
        s["rating"] += 25 if is_winner else -15
        s["rating"] = max(0.0, s["rating"])

for pid, s in stats_agg.items():
    mp = s["matches_played"]
    s["win_rate"] = round(s["wins"] / mp, 4) if mp else 0.0
    deaths = s["total_deaths"]
    s["kd_ratio"] = round(s["total_kills"] / deaths, 4) if deaths else float(s["total_kills"])

    player_stats_table.put_item(Item={
        k: Decimal(str(v)) if isinstance(v, float) else v
        for k, v in s.items()
    })

    leaderboard_table.put_item(Item={
        "scope": "GLOBAL",
        "player_id": pid,
        "username": s["username"],
        "rating": Decimal(str(s["rating"])),
        "wins": s["wins"],
        "matches_played": mp,
        "win_rate": Decimal(str(s["win_rate"])),
    })

    print(f"{s['username']:15} rating={s['rating']:.0f}  W/L={s['wins']}/{s['losses']}  K/D={s['kd_ratio']:.2f}")

print("\n" + "="*50)
print("Seed zavrsen!")
print(f"Korisnici:  {len(created_users)}")
print(f"Turniri:    {len(created_tournaments)}")
print(f"Mecevi:     {len(created_matches)}")
print(f"Statistike: {len(stats_agg)} igraca")
print("="*50)
print("\nLogin podaci (lozinka: lozinka123)")
print("  admin@esports.com  — role: admin")
print("  sniper@test.com    — role: observer")
print("  headshot@test.com  — role: observer")