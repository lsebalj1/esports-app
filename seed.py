import asyncio
import aioboto3
import boto3
import uuid
import random
import time
from datetime import datetime, timezone, timedelta
from passlib.context import CryptContext
import os

ENDPOINT = os.getenv("DYNAMODB_ENDPOINT", "http://localhost:8000")
REGION = "eu-central-1"
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
if not ADMIN_PASSWORD:
    raise RuntimeError("ADMIN_PASSWORD env varijabla mora biti postavljena.")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

AWS_OPTS = dict(
    endpoint_url=ENDPOINT,
    region_name=REGION,
    aws_access_key_id="local",
    aws_secret_access_key="local",
)

session = aioboto3.Session()

CONCURRENCY = 20
sem = asyncio.Semaphore(CONCURRENCY)


def wait_for_table(table_name: str, retries: int = 30, delay: float = 2.0):
    client = boto3.client("dynamodb", **AWS_OPTS)
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

print("Cekanje na DynamoDB tablice...")
for t in REQUIRED_TABLES:
    wait_for_table(t)
print("Sve tablice dostupne. Pocinjem seed...\n")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def now(offset_days=0):
    return (datetime.now(timezone.utc) + timedelta(days=offset_days)).isoformat()

def uid():
    return str(uuid.uuid4())


GAME_TEAM_SIZE = {
    "CS2": 5, "Valorant": 5, "League of Legends": 5, "Dota 2": 5,
    "Fortnite": 4, "Rocket League": 3, "Overwatch 2": 5,
    "Apex Legends": 3, "Rainbow Six Siege": 5, "Marvel Rivals": 6,
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

USERS = [
    {"username": "admin", "email": "admin@esports.com", "role": "admin"},
    {"username": "mod_marko", "email": "marko@esports.com", "role": "admin"},
]

TOURNAMENTS = [
    {"name": "Zagreb Major 2025", "game": "CS2", "format": "single_elimination", "match_format": "bo3", "max_teams": 8, "prize_pool": "50000.00", "status": "completed", "start_date": now(-14), "description": "Najveci CS2 turnir u regiji."},
    {"name": "Balkan Pro League", "game": "CS2", "format": "single_elimination", "match_format": "bo3", "max_teams": 8, "prize_pool": "25000.00", "status": "in_progress", "start_date": now(-3), "description": "Profesionalna CS2 liga."},
    {"name": "CS2 Masters Cup", "game": "CS2", "format": "single_elimination", "match_format": "bo5", "max_teams": 16, "prize_pool": "100000.00", "status": "registration", "start_date": now(14), "description": "Elite CS2 turnir."},
    {"name": "Valorant Champions HR", "game": "Valorant", "format": "single_elimination", "match_format": "bo3", "max_teams": 8, "prize_pool": "30000.00", "status": "completed", "start_date": now(-21), "description": "Hrvatski Valorant sampionat."},
    {"name": "Split Invitational", "game": "Valorant", "format": "single_elimination", "match_format": "bo3", "max_teams": 8, "prize_pool": "15000.00", "status": "in_progress", "start_date": now(-5), "description": "Valorant turnir u Splitu."},
    {"name": "Valorant Rising Stars", "game": "Valorant", "format": "double_elimination", "match_format": "bo3", "max_teams": 16, "prize_pool": "10000.00", "status": "registration", "start_date": now(7), "description": "Turnir za nove timove."},
    {"name": "LoL Adriatic League", "game": "League of Legends", "format": "single_elimination", "match_format": "bo5", "max_teams": 8, "prize_pool": "40000.00", "status": "completed", "start_date": now(-28), "description": "Regionalna LoL liga."},
    {"name": "Summoner's Cup", "game": "League of Legends", "format": "single_elimination", "match_format": "bo3", "max_teams": 8, "prize_pool": "20000.00", "status": "in_progress", "start_date": now(-7), "description": "LoL turnir."},
    {"name": "Dota 2 Balkan Championship", "game": "Dota 2", "format": "single_elimination", "match_format": "bo3", "max_teams": 8, "prize_pool": "35000.00", "status": "completed", "start_date": now(-35), "description": "Balkanski Dota 2 turnir."},
    {"name": "Ancient Wars Cup", "game": "Dota 2", "format": "single_elimination", "match_format": "bo5", "max_teams": 8, "prize_pool": "25000.00", "status": "in_progress", "start_date": now(-4), "description": "Kompetitivni Dota turnir."},
    {"name": "Rocket League HR Open", "game": "Rocket League", "format": "single_elimination", "match_format": "bo5", "max_teams": 8, "prize_pool": "8000.00", "status": "completed", "start_date": now(-18), "description": "Hrvatski RL turnir."},
    {"name": "Aerial Masters", "game": "Rocket League", "format": "single_elimination", "match_format": "bo5", "max_teams": 8, "prize_pool": "12000.00", "status": "in_progress", "start_date": now(-2), "description": "RL masters turnir."},
    {"name": "Marvel Rivals Showdown", "game": "Marvel Rivals", "format": "single_elimination", "match_format": "bo3", "max_teams": 8, "prize_pool": "15000.00", "status": "completed", "start_date": now(-10), "description": "Prvi Marvel Rivals turnir."},
    {"name": "Heroes Clash Zagreb", "game": "Marvel Rivals", "format": "single_elimination", "match_format": "bo3", "max_teams": 8, "prize_pool": "20000.00", "status": "in_progress", "start_date": now(-1), "description": "Marvel Rivals u Zagrebu."},
    {"name": "Overwatch Balkan Cup", "game": "Overwatch 2", "format": "single_elimination", "match_format": "bo5", "max_teams": 8, "prize_pool": "18000.00", "status": "completed", "start_date": now(-25), "description": "OW2 regionalni turnir."},
    {"name": "Heroes United", "game": "Overwatch 2", "format": "single_elimination", "match_format": "bo3", "max_teams": 8, "prize_pool": "12000.00", "status": "in_progress", "start_date": now(-3), "description": "OW2 liga."},
    {"name": "Apex Predators HR", "game": "Apex Legends", "format": "single_elimination", "match_format": "bo3", "max_teams": 8, "prize_pool": "10000.00", "status": "completed", "start_date": now(-15), "description": "Hrvatski Apex turnir."},
    {"name": "Siege Masters", "game": "Rainbow Six Siege", "format": "single_elimination", "match_format": "bo3", "max_teams": 8, "prize_pool": "15000.00", "status": "in_progress", "start_date": now(-6), "description": "R6 Siege masters."},
]

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
                "role": ["IGL", "Entry", "Support", "AWP", "Lurk", "Flex"][j % 6],
            })
        teams.append({"team_id": uid(), "team_name": team_name, "players": players})
    return teams


def make_player_stats(won=False):
    if won:
        return {"kills": random.randint(18, 30), "deaths": random.randint(5, 14), "assists": random.randint(3, 10), "score": random.randint(2500, 4000)}
    return {"kills": random.randint(5, 17), "deaths": random.randint(15, 28), "assists": random.randint(1, 8), "score": random.randint(800, 2400)}


def make_team_stats(players, won=False):
    player_stats = []
    total_kills = total_deaths = total_score = 0
    for p in players:
        stats = make_player_stats(won)
        player_stats.append({"player_id": p["player_id"], "player_name": p["player_name"], **stats})
        total_kills += stats["kills"]
        total_deaths += stats["deaths"]
        total_score += stats["score"]
    return {"players": player_stats, "total_kills": total_kills, "total_deaths": total_deaths, "total_score": total_score}


def generate_bo_result(match_format, winner_team_id, team1_id, team2_id, game):
    wins_needed = {"bo1": 1, "bo3": 2}.get(match_format, 3)
    maps = MAP_NAMES.get(game, ["Map 1", "Map 2", "Map 3"])
    random.shuffle(maps)

    t1_wins = t2_wins = 0
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
            t1_score, t2_score = random.randint(13, 16), random.randint(5, 12)
        else:
            t2_wins += 1
            t2_score, t1_score = random.randint(13, 16), random.randint(5, 12)

        map_results.append({
            "map_number": map_num, "map_name": maps[(map_num - 1) % len(maps)],
            "winner_team_id": map_winner, "team1_score": t1_score, "team2_score": t2_score,
        })
    return t1_wins, t2_wins, map_results


def generate_bracket_data(t, is_completed=False):
    teams = list(t.get("teams") or [])[:8]
    random.shuffle(teams)
    game = t.get("game", "CS2")
    match_format = t.get("match_format", "bo3")
    t_id = t["tournament_id"]

    all_matches = []
    round_teams = teams
    round_num = 1

    while len(round_teams) > 1:
        next_round = []
        for pos, (t1, t2) in enumerate(zip(round_teams[::2], round_teams[1::2]), start=1):
            m_id = uid()
            if is_completed or round_num < 3:
                winner = random.choice([t1, t2])
                t1_wins, t2_wins, map_results = generate_bo_result(
                    match_format, winner["team_id"], t1["team_id"], t2["team_id"], game
                )
                match = {
                    "match_id": m_id, "tournament_id": t_id,
                    "round": round_num, "position": pos, "match_format": match_format,
                    "team1_id": t1["team_id"], "team1_name": t1["team_name"], "team1_players": t1["players"],
                    "team2_id": t2["team_id"], "team2_name": t2["team_name"], "team2_players": t2["players"],
                    "winner_id": winner["team_id"],
                    "team1_maps_won": t1_wins, "team2_maps_won": t2_wins,
                    "map_results": map_results,
                    "team1_stats": make_team_stats(t1["players"], winner == t1),
                    "team2_stats": make_team_stats(t2["players"], winner == t2),
                    "status": "completed", "duration_seconds": random.randint(2400, 7200),
                    "scheduled_at": now(-10 + round_num), "completed_at": now(-9 + round_num),
                }
                next_round.append(winner)
            else:
                match = {
                    "match_id": m_id, "tournament_id": t_id,
                    "round": round_num, "position": pos, "match_format": match_format,
                    "team1_id": t1["team_id"] if t1 else None, "team1_name": t1["team_name"] if t1 else None,
                    "team1_players": t1["players"] if t1 else None,
                    "team2_id": t2["team_id"] if t2 else None, "team2_name": t2["team_name"] if t2 else None,
                    "team2_players": t2["players"] if t2 else None,
                    "winner_id": None, "team1_maps_won": 0, "team2_maps_won": 0,
                    "map_results": None, "team1_stats": None, "team2_stats": None,
                    "status": "pending", "duration_seconds": None,
                    "scheduled_at": now(round_num), "completed_at": None,
                }
                next_round.append(t1)
            all_matches.append(match)
        round_teams = next_round
        round_num += 1
    return all_matches

async def async_put(table, item):
    async with sem:
        await table.put_item(Item=item)

async def async_delete(table, key):
    async with sem:
        await table.delete_item(Key=key)

async def async_update(table, key, **kwargs):
    async with sem:
        await table.update_item(Key=key, **kwargs)

async def scan_all_keys(table, key_name, consistent=False):
    keys = []
    last_key = None
    while True:
        kwargs = {"ProjectionExpression": key_name}
        if consistent:
            kwargs["ConsistentRead"] = True
        if last_key:
            kwargs["ExclusiveStartKey"] = last_key
        resp = await table.scan(**kwargs)
        keys.extend(item[key_name] for item in resp.get("Items", []))
        last_key = resp.get("LastEvaluatedKey")
        if not last_key:
            break
    return keys

async def wipe_table(table, key_name, consistent=False):
    keys = await scan_all_keys(table, key_name, consistent)
    if keys:
        await asyncio.gather(*[async_delete(table, {key_name: k}) for k in keys])
    return len(keys)

async def main():
    start_time = time.time()

    async with session.resource("dynamodb", **AWS_OPTS) as ddb:
        users_table = await ddb.Table("Users")
        tournaments_table = await ddb.Table("Tournaments")
        matches_table = await ddb.Table("Matches")

        print("Kreiranje korisnika...")
        for u in USERS:
            resp = await users_table.query(
                IndexName="email-index",
                KeyConditionExpression=boto3.dynamodb.conditions.Key("email").eq(u["email"]),
            )
            existing = resp.get("Items", [])
            if existing:
                await users_table.update_item(
                    Key={"user_id": existing[0]["user_id"]},
                    UpdateExpression="SET password_hash = :ph",
                    ExpressionAttributeValues={":ph": hash_password(ADMIN_PASSWORD)},
                )
                print(f"  {u['role']:10} {u['username']:15} -- vec postoji, lozinka azurirana")
                admin_user = existing[0]
            else:
                user_id = uid()
                item = {
                    "user_id": user_id, "username": u["username"], "email": u["email"],
                    "password_hash": hash_password(ADMIN_PASSWORD), "role": u["role"],
                    "is_active": True, "created_at": now(-30), "updated_at": now(-30),
                }
                await users_table.put_item(Item=item)
                print(f"  {u['role']:10} {u['username']:15} -- {u['email']}")
                admin_user = item
        admin = admin_user

        print("\nCistim turnire i meceve (async)...")
        del_t, del_m = await asyncio.gather(
            wipe_table(tournaments_table, "tournament_id", consistent=True),
            wipe_table(matches_table, "match_id"),
        )
        print(f"  Obrisano {del_t} turnira i {del_m} meceva paralelno.")

        print("\nKreiram turnire...")
        tournament_items = []
        for t in TOURNAMENTS:
            t_id = uid()
            game = t.get("game", "CS2")
            teams = create_teams_for_game(game, t["max_teams"])
            item = {
                "tournament_id": t_id, "name": t["name"], "game": game,
                "team_size": GAME_TEAM_SIZE.get(game, 5),
                "format": t["format"], "match_format": t["match_format"],
                "max_teams": t["max_teams"], "current_teams": len(teams), "teams": teams,
                "prize_pool": t["prize_pool"], "status": t["status"],
                "admin_id": admin["user_id"], "admin_name": admin["username"],
                "start_date": t["start_date"], "description": t["description"],
                "created_at": now(-20), "updated_at": now(-1),
            }
            tournament_items.append(item)

        await asyncio.gather(*[async_put(tournaments_table, item) for item in tournament_items])
        for item in tournament_items:
            print(f"  [{item['status']:14}] {item['name']} ({item['game']}, {item['match_format']})")

        print("\nGeneriram bracketove...")
        all_matches = []
        bracket_updates = []
        for item in tournament_items:
            if item["status"] in ("completed", "in_progress"):
                is_completed = item["status"] == "completed"
                matches = generate_bracket_data(item, is_completed=is_completed)
                all_matches.extend(matches)
                bracket_updates.append((item["tournament_id"], matches))
                print(f"  {item['name']}: {len(matches)} meceva ({item['status']})")

        print(f"\nUpisujem {len(all_matches)} meceva paralelno...")
        await asyncio.gather(*[async_put(matches_table, m) for m in all_matches])

        await asyncio.gather(*[
            async_update(
                tournaments_table,
                {"tournament_id": t_id},
                UpdateExpression="SET bracket = :b",
                ExpressionAttributeValues={":b": matches},
            )
            for t_id, matches in bracket_updates
        ])

        elapsed = time.time() - start_time
        print("\n" + "=" * 60)
        print(f"Seed zavrsen za {elapsed:.1f}s")
        print(f"Korisnici:  {len(USERS)}")
        print(f"Turniri:    {len(tournament_items)}")
        print(f"Mecevi:     {len(all_matches)}")
        print("=" * 60)
        print("\nLogin podaci")
        print("  admin@esports.com  -- role: admin")

asyncio.run(main())