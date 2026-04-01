import boto3
import uuid
import random
import time
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from passlib.context import CryptContext
import os

ENDPOINT = os.getenv("DYNAMODB_ENDPOINT", "http://localhost:8000")
REGION = "eu-central-1"
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
if not ADMIN_PASSWORD:
    raise RuntimeError("ADMIN_PASSWORD env varijabla mora biti postavljena.")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

dynamodb = boto3.resource(
    "dynamodb",
    endpoint_url=ENDPOINT,
    region_name=REGION,
    aws_access_key_id="local",
    aws_secret_access_key="local",
)

def wait_for_table(table_name: str, retries: int = 30, delay: float = 2.0):
    client = boto3.client(
        "dynamodb",
        endpoint_url=ENDPOINT,
        region_name=REGION,
        aws_access_key_id="local",
        aws_secret_access_key="local",
    )
    for attempt in range(retries):
        try:
            tables = client.list_tables()["TableNames"]
            if table_name in tables:
                return
        except Exception:
            pass
        print(f"  Waiting for table '{table_name}'... ({attempt + 1}/{retries})")
        time.sleep(delay)
    raise RuntimeError(f"Table '{table_name}' not available after {retries * delay}s")


REQUIRED_TABLES = ["Users", "Tournaments", "Matches", "PlayerStats", "Leaderboard"]

print("Čekanje na DynamoDB tablice...")
for t in REQUIRED_TABLES:
    wait_for_table(t)
print("Sve tablice dostupne. Počinjem seed...\n")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def now(offset_days=0):
    return (datetime.now(timezone.utc) + timedelta(days=offset_days)).isoformat()

def uid():
    return str(uuid.uuid4())

GAME_TEAM_SIZE = {
    "CS2": 5,
    "Valorant": 5,
    "League of Legends": 5,
    "Dota 2": 5,
    "Fortnite": 4,
    "Rocket League": 3,
    "Overwatch 2": 5,
    "Apex Legends": 3,
    "Rainbow Six Siege": 5,
    "Marvel Rivals": 6,
}

TEAM_NAMES = [
    "Natus Vincere", "G2 Esports", "FaZe Clan", "Team Liquid", "Cloud9",
    "Fnatic", "Evil Geniuses", "100 Thieves", "TSM", "Gen.G",
    "T1", "DRX", "LOUD", "Paper Rex", "Sentinels",
    "NRG", "Vitality", "BIG", "MOUZ", "Heroic",
    "ENCE", "Astralis", "Complexity", "OG", "Team Spirit",
]

PLAYER_NAMES = [
    "s1mple", "ZywOo", "NiKo", "dev1ce", "m0NESY", "sh1ro", "blameF", "ropz", "Twistzz", "EliGE",
    "TenZ", "yay", "Derke", "cNed", "ScreaM", "Chronicle", "nAts", "Sacy", "aspas", "Less",
    "Faker", "Caps", "Chovy", "ShowMaker", "Knight", "Ruler", "Gumayusi", "Viper", "Keria", "Zeus",
    "Topson", "ana", "Miracle", "Ame", "NothingToSay", "Faith_bian", "y`", "XinQ", "Yatoro", "Miposhka",
    "Lethamyr", "jstn", "Squishy", "GarrettG", "Firstkiller", "Monkey Moon", "rise", "Vatira", "zen", "Seikoo",
    "Proper", "Kevster", "Lip", "Fleta", "Shy", "Profit", "Leave", "Pelican", "Mer1t", "Kilo",
]

print("Kreiranje korisnika...")

users_table = dynamodb.Table("Users")

USERS = [
    {"username": "admin", "email": "admin@esports.com", "role": "admin"},
    {"username": "mod_marko", "email": "marko@esports.com", "role": "admin"},
]

def _get_user_by_email(email):
    resp = users_table.query(
        IndexName="email-index",
        KeyConditionExpression=boto3.dynamodb.conditions.Key("email").eq(email),
    )
    items = resp.get("Items", [])
    return items[0] if items else None

created_users = []
for u in USERS:
    existing = _get_user_by_email(u["email"])
    if existing:
        users_table.update_item(
            Key={"user_id": existing["user_id"]},
            UpdateExpression="SET password_hash = :ph",
            ExpressionAttributeValues={":ph": hash_password(ADMIN_PASSWORD)},
        )
        print(f"  {u['role']:10} {u['username']:15} — vec postoji, lozinka azurirana")
        created_users.append(existing)
        continue
    user_id = uid()
    item = {
        "user_id": user_id,
        "username": u["username"],
        "email": u["email"],
        "password_hash": hash_password(ADMIN_PASSWORD),
        "role": u["role"],
        "is_active": True,
        "created_at": now(-30),
        "updated_at": now(-30),
    }
    users_table.put_item(Item=item)
    created_users.append(item)
    print(f"  {u['role']:10} {u['username']:15} — {u['email']}")

admins = [u for u in created_users if u["role"] == "admin"]
admin = admins[0]

print("\nKreiranje timova...")

def create_teams_for_game(game: str, count: int = 8):
    team_size = GAME_TEAM_SIZE.get(game, 5)
    teams = []
    available_names = TEAM_NAMES.copy()
    available_players = PLAYER_NAMES.copy()
    random.shuffle(available_names)
    random.shuffle(available_players)

    for i in range(count):
        team_name = available_names[i % len(available_names)]
        if i >= len(available_names):
            team_name = f"{team_name} {i // len(available_names) + 1}"

        players = []
        for j in range(team_size):
            player_idx = (i * team_size + j) % len(available_players)
            players.append({
                "player_id": uid(),
                "player_name": available_players[player_idx],
                "role": ["IGL", "Entry", "Support", "AWP", "Lurk", "Flex"][j % 6]
            })

        teams.append({
            "team_id": uid(),
            "team_name": team_name,
            "players": players,
        })

    return teams

print("\nKreiranje turnira...")

tournaments_table = dynamodb.Table("Tournaments")
TOURNAMENTS = [
    # CS2 turniri
    {
        "name": "Zagreb Major 2025",
        "game": "CS2",
        "format": "single_elimination",
        "match_format": "bo3",
        "max_teams": 8,
        "prize_pool": "50000.00",
        "status": "completed",
        "start_date": now(-14),
        "description": "Najveci CS2 turnir u regiji.",
    },
    {
        "name": "Balkan Pro League",
        "game": "CS2",
        "format": "single_elimination",
        "match_format": "bo3",
        "max_teams": 8,
        "prize_pool": "25000.00",
        "status": "in_progress",
        "start_date": now(-3),
        "description": "Profesionalna CS2 liga.",
    },
    {
        "name": "CS2 Masters Cup",
        "game": "CS2",
        "format": "single_elimination",
        "match_format": "bo5",
        "max_teams": 16,
        "prize_pool": "100000.00",
        "status": "registration",
        "start_date": now(14),
        "description": "Elite CS2 turnir.",
    },
    # Valorant turniri
    {
        "name": "Valorant Champions HR",
        "game": "Valorant",
        "format": "single_elimination",
        "match_format": "bo3",
        "max_teams": 8,
        "prize_pool": "30000.00",
        "status": "completed",
        "start_date": now(-21),
        "description": "Hrvatski Valorant šampionat.",
    },
    {
        "name": "Split Invitational",
        "game": "Valorant",
        "format": "single_elimination",
        "match_format": "bo3",
        "max_teams": 8,
        "prize_pool": "15000.00",
        "status": "in_progress",
        "start_date": now(-5),
        "description": "Valorant turnir u Splitu.",
    },
    {
        "name": "Valorant Rising Stars",
        "game": "Valorant",
        "format": "double_elimination",
        "match_format": "bo3",
        "max_teams": 16,
        "prize_pool": "10000.00",
        "status": "registration",
        "start_date": now(7),
        "description": "Turnir za nove timove.",
    },
    # League of Legends turniri
    {
        "name": "LoL Adriatic League",
        "game": "League of Legends",
        "format": "single_elimination",
        "match_format": "bo5",
        "max_teams": 8,
        "prize_pool": "40000.00",
        "status": "completed",
        "start_date": now(-28),
        "description": "Regionalna LoL liga.",
    },
    {
        "name": "Summoner's Cup",
        "game": "League of Legends",
        "format": "single_elimination",
        "match_format": "bo3",
        "max_teams": 8,
        "prize_pool": "20000.00",
        "status": "in_progress",
        "start_date": now(-7),
        "description": "LoL turnir.",
    },
    # Dota 2 turniri
    {
        "name": "Dota 2 Balkan Championship",
        "game": "Dota 2",
        "format": "single_elimination",
        "match_format": "bo3",
        "max_teams": 8,
        "prize_pool": "35000.00",
        "status": "completed",
        "start_date": now(-35),
        "description": "Balkanski Dota 2 turnir.",
    },
    {
        "name": "Ancient Wars Cup",
        "game": "Dota 2",
        "format": "single_elimination",
        "match_format": "bo5",
        "max_teams": 8,
        "prize_pool": "25000.00",
        "status": "in_progress",
        "start_date": now(-4),
        "description": "Kompetitivni Dota turnir.",
    },
    # Rocket League turniri
    {
        "name": "Rocket League HR Open",
        "game": "Rocket League",
        "format": "single_elimination",
        "match_format": "bo5",
        "max_teams": 8,
        "prize_pool": "8000.00",
        "status": "completed",
        "start_date": now(-18),
        "description": "Hrvatski RL turnir.",
    },
    {
        "name": "Aerial Masters",
        "game": "Rocket League",
        "format": "single_elimination",
        "match_format": "bo5",
        "max_teams": 8,
        "prize_pool": "12000.00",
        "status": "in_progress",
        "start_date": now(-2),
        "description": "RL masters turnir.",
    },
    # Marvel Rivals turniri
    {
        "name": "Marvel Rivals Showdown",
        "game": "Marvel Rivals",
        "format": "single_elimination",
        "match_format": "bo3",
        "max_teams": 8,
        "prize_pool": "15000.00",
        "status": "completed",
        "start_date": now(-10),
        "description": "Prvi Marvel Rivals turnir.",
    },
    {
        "name": "Heroes Clash Zagreb",
        "game": "Marvel Rivals",
        "format": "single_elimination",
        "match_format": "bo3",
        "max_teams": 8,
        "prize_pool": "20000.00",
        "status": "in_progress",
        "start_date": now(-1),
        "description": "Marvel Rivals u Zagrebu.",
    },
    # Overwatch 2 turniri
    {
        "name": "Overwatch Balkan Cup",
        "game": "Overwatch 2",
        "format": "single_elimination",
        "match_format": "bo5",
        "max_teams": 8,
        "prize_pool": "18000.00",
        "status": "completed",
        "start_date": now(-25),
        "description": "OW2 regionalni turnir.",
    },
    {
        "name": "Heroes United",
        "game": "Overwatch 2",
        "format": "single_elimination",
        "match_format": "bo3",
        "max_teams": 8,
        "prize_pool": "12000.00",
        "status": "in_progress",
        "start_date": now(-3),
        "description": "OW2 liga.",
    },
    # Apex Legends turniri
    {
        "name": "Apex Predators HR",
        "game": "Apex Legends",
        "format": "single_elimination",
        "match_format": "bo3",
        "max_teams": 8,
        "prize_pool": "10000.00",
        "status": "completed",
        "start_date": now(-15),
        "description": "Hrvatski Apex turnir.",
    },
    # Rainbow Six Siege turniri
    {
        "name": "Siege Masters",
        "game": "Rainbow Six Siege",
        "format": "single_elimination",
        "match_format": "bo3",
        "max_teams": 8,
        "prize_pool": "15000.00",
        "status": "in_progress",
        "start_date": now(-6),
        "description": "R6 Siege masters.",
    },
]

print("\nCistim sve turnire i meceve...")

matches_table = dynamodb.Table("Matches")

def wipe_all_tournaments_and_matches():
    deleted_matches = 0
    last_key = None
    while True:
        kwargs = {}
        if last_key:
            kwargs["ExclusiveStartKey"] = last_key
        resp = matches_table.scan(ProjectionExpression="match_id", **kwargs)
        for item in resp.get("Items", []):
            matches_table.delete_item(Key={"match_id": item["match_id"]})
            deleted_matches += 1
        last_key = resp.get("LastEvaluatedKey")
        if not last_key:
            break

    deleted_tournaments = 0
    last_key = None
    while True:
        kwargs = {"ConsistentRead": True}
        if last_key:
            kwargs["ExclusiveStartKey"] = last_key
        resp = tournaments_table.scan(ProjectionExpression="tournament_id", **kwargs)
        for item in resp.get("Items", []):
            tournaments_table.delete_item(Key={"tournament_id": item["tournament_id"]})
            deleted_tournaments += 1
        last_key = resp.get("LastEvaluatedKey")
        if not last_key:
            break

    return deleted_tournaments, deleted_matches

del_t, del_m = wipe_all_tournaments_and_matches()
print(f"  Obrisano {del_t} turnira i {del_m} meceva.")

created_tournaments = []
for t in TOURNAMENTS:
    t_id = uid()
    game = t.get("game", "CS2")
    teams = create_teams_for_game(game, t["max_teams"])

    item = {
        "tournament_id": t_id,
        "name": t["name"],
        "game": game,
        "team_size": GAME_TEAM_SIZE.get(game, 5),
        "format": t["format"],
        "match_format": t["match_format"],
        "max_teams": t["max_teams"],
        "current_teams": len(teams),
        "teams": teams,
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
    print(f"  [{t['status']:14}] {t['name']} ({game}, {t['match_format']})")

print("\nKreiranje meceva...")

matches_table = dynamodb.Table("Matches")

MAP_NAMES = {
    "CS2": ["Mirage", "Inferno", "Nuke", "Ancient", "Anubis", "Vertigo", "Dust2"],
    "Valorant": ["Bind", "Haven", "Split", "Ascent", "Icebox", "Breeze", "Fracture", "Pearl", "Lotus"],
    "League of Legends": ["Summoner's Rift"],
    "Dota 2": ["Default"],
    "Rocket League": ["DFH Stadium", "Mannfield", "Champions Field", "Urban Central", "Beckwith Park"],
    "Marvel Rivals": ["Tokyo", "New York", "Wakanda"],
    "Overwatch 2": ["King's Row", "Hollywood", "Eichenwalde", "Numbani", "Dorado", "Route 66"],
    "Apex Legends": ["World's Edge", "Storm Point", "Olympus", "Kings Canyon"],
    "Rainbow Six Siege": ["Bank", "Border", "Chalet", "Clubhouse", "Coastline", "Consulate"],
}

def make_player_stats(won=False):
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

def make_team_stats(players, won=False):
    player_stats = []
    total_kills = 0
    total_deaths = 0
    total_score = 0

    for p in players:
        stats = make_player_stats(won)
        player_stats.append({
            "player_id": p["player_id"],
            "player_name": p["player_name"],
            **stats
        })
        total_kills += stats["kills"]
        total_deaths += stats["deaths"]
        total_score += stats["score"]

    return {
        "players": player_stats,
        "total_kills": total_kills,
        "total_deaths": total_deaths,
        "total_score": total_score,
    }

def generate_bo_result(match_format: str, winner_team_id: str, team1_id: str, team2_id: str, game: str):
    if match_format == "bo1":
        wins_needed = 1
    elif match_format == "bo3":
        wins_needed = 2
    else:  # bo5
        wins_needed = 3

    maps = MAP_NAMES.get(game, ["Map 1", "Map 2", "Map 3"])
    random.shuffle(maps)

    t1_wins = 0
    t2_wins = 0
    map_results = []
    map_num = 0

    while t1_wins < wins_needed and t2_wins < wins_needed:
        map_num += 1

        if winner_team_id == team1_id:
            map_winner = team1_id if random.random() < 0.65 else team2_id
        else:
            map_winner = team2_id if random.random() < 0.65 else team1_id

        if map_winner == team1_id:
            t1_wins += 1
            t1_score = random.randint(13, 16)
            t2_score = random.randint(5, 12)
        else:
            t2_wins += 1
            t2_score = random.randint(13, 16)
            t1_score = random.randint(5, 12)

        map_results.append({
            "map_number": map_num,
            "map_name": maps[(map_num - 1) % len(maps)],
            "winner_team_id": map_winner,
            "team1_score": t1_score,
            "team2_score": t2_score,
        })

    return t1_wins, t2_wins, map_results

created_matches = []

def generate_bracket_for_tournament(t, is_completed=False):
    t_id = t["tournament_id"]
    teams = list(t.get("teams") or [])[:8]
    random.shuffle(teams)
    game = t.get("game", "CS2")
    match_format = t.get("match_format", "bo3")

    all_matches = []
    round_teams = teams
    round_num = 1

    while len(round_teams) > 1:
        next_round = []
        for pos, (t1, t2) in enumerate(zip(round_teams[::2], round_teams[1::2]), start=1):
            m_id = uid()

            if is_completed or round_num < 3:
                winner = random.choice([t1, t2])
                loser = t2 if winner == t1 else t1

                t1_wins, t2_wins, map_results = generate_bo_result(
                    match_format, winner["team_id"], t1["team_id"], t2["team_id"], game
                )

                match = {
                    "match_id": m_id,
                    "tournament_id": t_id,
                    "round": round_num,
                    "position": pos,
                    "match_format": match_format,
                    "team1_id": t1["team_id"],
                    "team1_name": t1["team_name"],
                    "team1_players": t1["players"],
                    "team2_id": t2["team_id"],
                    "team2_name": t2["team_name"],
                    "team2_players": t2["players"],
                    "winner_id": winner["team_id"],
                    "team1_maps_won": t1_wins,
                    "team2_maps_won": t2_wins,
                    "map_results": map_results,
                    "team1_stats": make_team_stats(t1["players"], winner == t1),
                    "team2_stats": make_team_stats(t2["players"], winner == t2),
                    "status": "completed",
                    "duration_seconds": random.randint(2400, 7200),
                    "scheduled_at": now(-10 + round_num),
                    "completed_at": now(-9 + round_num),
                }
                next_round.append(winner)
            else:
                match = {
                    "match_id": m_id,
                    "tournament_id": t_id,
                    "round": round_num,
                    "position": pos,
                    "match_format": match_format,
                    "team1_id": t1["team_id"] if t1 else None,
                    "team1_name": t1["team_name"] if t1 else None,
                    "team1_players": t1["players"] if t1 else None,
                    "team2_id": t2["team_id"] if t2 else None,
                    "team2_name": t2["team_name"] if t2 else None,
                    "team2_players": t2["players"] if t2 else None,
                    "winner_id": None,
                    "team1_maps_won": 0,
                    "team2_maps_won": 0,
                    "map_results": None,
                    "team1_stats": None,
                    "team2_stats": None,
                    "status": "pending",
                    "duration_seconds": None,
                    "scheduled_at": now(round_num),
                    "completed_at": None,
                }
                next_round.append(t1)

            matches_table.put_item(Item=match)
            created_matches.append(match)
            all_matches.append(match)

        round_teams = next_round
        round_num += 1

    tournaments_table.update_item(
        Key={"tournament_id": t_id},
        UpdateExpression="SET bracket = :b",
        ExpressionAttributeValues={":b": all_matches},
    )

    return all_matches

for t in created_tournaments:
    if t["status"] == "completed":
        matches = generate_bracket_for_tournament(t, is_completed=True)
        print(f" {t['name']}: {len(matches)} meceva (completed)")
    elif t["status"] == "in_progress":
        matches = generate_bracket_for_tournament(t, is_completed=False)
        print(f" {t['name']}: {len(matches)} meceva (in_progress)")

print("\n" + "=" * 60)
print("Seed zavrsен!")
print(f"Korisnici:  {len(created_users)}")
print(f"Turniri:    {len(created_tournaments)}")
print(f"Mecevi:     {len(created_matches)}")
print("=" * 60)
print(f"\nLogin podaci")
print("  admin@esports.com  — role: admin")