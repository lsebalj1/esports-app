import boto3
import uuid
import random
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import bcrypt
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

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

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
        "password_hash": hash_password("lozinka123"),
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
    # CS2 turniri
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
        "name": "Pro League Season 3",
        "game": "CS2",
        "format": "round_robin",
        "max_participants": 8,
        "prize_pool": "2000.00",
        "status": "draft",
        "start_date": now(30),
        "description": "Profesionalna liga — sezona 3.",
    },
    {
        "name": "Balkan Masters CS2",
        "game": "CS2",
        "format": "single_elimination",
        "max_participants": 16,
        "prize_pool": "5000.00",
        "status": "registration",
        "start_date": now(14),
        "description": "Najveci CS2 turnir na Balkanu.",
    },
    # Valorant turniri
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
        "name": "Valorant Rookie Cup",
        "game": "Valorant",
        "format": "double_elimination",
        "max_participants": 16,
        "prize_pool": "500.00",
        "status": "in_progress",
        "start_date": now(-5),
        "description": "Turnir za nove igrace.",
    },
    {
        "name": "Split Showdown",
        "game": "Valorant",
        "format": "single_elimination",
        "max_participants": 8,
        "prize_pool": "750.00",
        "status": "completed",
        "start_date": now(-21),
        "description": "Valorant turnir u Splitu.",
    },
    # Marvel Rivals turniri
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
        "name": "Heroes Clash Zagreb",
        "game": "Marvel Rivals",
        "format": "single_elimination",
        "max_participants": 16,
        "prize_pool": "1500.00",
        "status": "registration",
        "start_date": now(10),
        "description": "Marvel Rivals turnir u Zagrebu.",
    },
    # League of Legends turniri
    {
        "name": "LoL Balkan League",
        "game": "League of Legends",
        "format": "round_robin",
        "max_participants": 8,
        "prize_pool": "3000.00",
        "status": "in_progress",
        "start_date": now(-10),
        "description": "Regionalna liga za League of Legends.",
    },
    {
        "name": "Summoner's Cup HR",
        "game": "League of Legends",
        "format": "double_elimination",
        "max_participants": 16,
        "prize_pool": "2000.00",
        "status": "registration",
        "start_date": now(21),
        "description": "Hrvatski LoL turnir.",
    },
    # Dota 2 turniri
    {
        "name": "Dota Legends Open",
        "game": "Dota 2",
        "format": "single_elimination",
        "max_participants": 8,
        "prize_pool": "1500.00",
        "status": "completed",
        "start_date": now(-28),
        "description": "Otvoreni Dota 2 turnir.",
    },
    {
        "name": "Ancient Wars",
        "game": "Dota 2",
        "format": "double_elimination",
        "max_participants": 16,
        "prize_pool": "2500.00",
        "status": "registration",
        "start_date": now(18),
        "description": "Kompetitivni Dota 2 turnir.",
    },
    # Fortnite turniri
    {
        "name": "Fortnite Friday",
        "game": "Fortnite",
        "format": "single_elimination",
        "max_participants": 32,
        "prize_pool": "500.00",
        "status": "in_progress",
        "start_date": now(-1),
        "description": "Tjedni Fortnite turnir.",
    },
    {
        "name": "Victory Royale Cup",
        "game": "Fortnite",
        "format": "single_elimination",
        "max_participants": 64,
        "prize_pool": "1000.00",
        "status": "registration",
        "start_date": now(5),
        "description": "Veliki Fortnite turnir.",
    },
    # Rocket League turniri
    {
        "name": "Rocket Masters",
        "game": "Rocket League",
        "format": "double_elimination",
        "max_participants": 8,
        "prize_pool": "800.00",
        "status": "completed",
        "start_date": now(-35),
        "description": "Rocket League masters turnir.",
    },
    {
        "name": "Aerial Kings",
        "game": "Rocket League",
        "format": "single_elimination",
        "max_participants": 16,
        "prize_pool": "1200.00",
        "status": "registration",
        "start_date": now(12),
        "description": "Turnir za najbolje Rocket League igrace.",
    },
    # Overwatch 2 turniri
    {
        "name": "Overwatch Spring Cup",
        "game": "Overwatch 2",
        "format": "single_elimination",
        "max_participants": 8,
        "prize_pool": "600.00",
        "status": "in_progress",
        "start_date": now(-2),
        "description": "Proljetni OW2 turnir.",
    },
    {
        "name": "Heroes United",
        "game": "Overwatch 2",
        "format": "round_robin",
        "max_participants": 8,
        "prize_pool": "1000.00",
        "status": "registration",
        "start_date": now(25),
        "description": "OW2 liga.",
    },
    # Apex Legends turniri
    {
        "name": "Apex Predators HR",
        "game": "Apex Legends",
        "format": "single_elimination",
        "max_participants": 20,
        "prize_pool": "1500.00",
        "status": "completed",
        "start_date": now(-18),
        "description": "Hrvatski Apex turnir.",
    },
    {
        "name": "Battle Royale Championship",
        "game": "Apex Legends",
        "format": "single_elimination",
        "max_participants": 30,
        "prize_pool": "2000.00",
        "status": "registration",
        "start_date": now(8),
        "description": "Veliki Apex Legends turnir.",
    },
    # Rainbow Six Siege turniri
    {
        "name": "Siege Masters",
        "game": "Rainbow Six Siege",
        "format": "double_elimination",
        "max_participants": 8,
        "prize_pool": "1000.00",
        "status": "in_progress",
        "start_date": now(-4),
        "description": "R6 Siege masters turnir.",
    },
    {
        "name": "Tactical Ops Cup",
        "game": "Rainbow Six Siege",
        "format": "single_elimination",
        "max_participants": 16,
        "prize_pool": "1500.00",
        "status": "draft",
        "start_date": now(35),
        "description": "Takticka R6 liga.",
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

def generate_bracket_for_tournament(t, is_completed=False):
    """Generate bracket and matches for a tournament."""
    t_id = t["tournament_id"]
    players = observers.copy()
    random.shuffle(players)
    
    # Use only 8 players for simplicity
    players = players[:8]
    
    all_matches = []
    round_players = players
    round_num = 1
    
    while len(round_players) > 1:
        next_round = []
        for pos, (p1, p2) in enumerate(zip(round_players[::2], round_players[1::2]), start=1):
            m_id = uid()
            
            if is_completed or round_num < 3:  # Complete earlier rounds
                winner = random.choice([p1, p2])
                match = {
                    "match_id": m_id,
                    "tournament_id": t_id,
                    "round": round_num,
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
                    "scheduled_at": now(-10 + round_num),
                    "completed_at": now(-9 + round_num),
                }
                next_round.append(winner)
            else:  # Leave later rounds pending for in_progress
                match = {
                    "match_id": m_id,
                    "tournament_id": t_id,
                    "round": round_num,
                    "position": pos,
                    "player1_id": p1["user_id"] if p1 else None,
                    "player1_name": p1["username"] if p1 else None,
                    "player2_id": p2["user_id"] if p2 else None,
                    "player2_name": p2["username"] if p2 else None,
                    "winner_id": None,
                    "status": "pending",
                    "player1_stats": None,
                    "player2_stats": None,
                    "duration_seconds": None,
                    "scheduled_at": now(round_num),
                    "completed_at": None,
                }
                next_round.append(p1)  # placeholder
            
            matches_table.put_item(Item=match)
            created_matches.append(match)
            all_matches.append(match)
        
        round_players = next_round
        round_num += 1
    
    # Update tournament with bracket
    tournaments_table.update_item(
        Key={"tournament_id": t_id},
        UpdateExpression="SET bracket = :b",
        ExpressionAttributeValues={":b": all_matches},
    )
    
    return all_matches

# Generate brackets for completed and in_progress tournaments
for t in created_tournaments:
    if t["status"] == "completed":
        matches = generate_bracket_for_tournament(t, is_completed=True)
        print(f"  ✓ {t['name']}: {len(matches)} meceva (completed)")
    elif t["status"] == "in_progress":
        matches = generate_bracket_for_tournament(t, is_completed=False)
        print(f"  ⏳ {t['name']}: {len(matches)} meceva (in_progress)")

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