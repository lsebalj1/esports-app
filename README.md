# Esports Tournament Platform

Platforma za upravljanje esports turnirima s bracket generacijom, upravljanjem timovima, unosom rezultata i statistikama igraca.

## Arhitektura

Mikroservisna arhitektura s 4 backend servisa, Vue.js frontendom i DynamoDB bazom:

```
frontend (Vue 3 + Vite)  :5173
auth-service (FastAPI)    :8001  — registracija, login, JWT
tournament-service        :8002  — turniri, timovi, bracket generacija
match-service             :8003  — mecevi, rezultati
stats-service             :8004  — statistike igraca, leaderboard
dynamodb-local            :8000  — baza podataka
redis                     :6379  — pub/sub eventi izmedu servisa
```

## Pokretanje

### Preduvjeti

- Docker i Docker Compose
- Kreirati .env file u main folderu

### Pokretanje servisa

```bash
docker-compose up -d
```

### Pokretanje seeda (punjenje baze testnim podacima)

```bash
ADMIN_PASSWORD=tvojalozinka docker-compose --profile seed run seed
```

### Pristup aplikaciji

Frontend: http://localhost:5173

Login: `admin@esports.com` s lozinkom koju si postavio u `ADMIN_PASSWORD` u .env.

## Env varijable

| Varijabla | Opis | Default |
|-----------|------|---------|
| `ADMIN_PASSWORD` | Lozinka za admin korisnike (seed) | obavezno |
| `JWT_SECRET` | Secret za JWT potpisivanje | `dev-secret` |
| `DYNAMODB_ENDPOINT` | DynamoDB endpoint | `http://dynamodb-local:8000` |
| `REDIS_URL` | Redis URL | `redis://redis:6379` |

## Tech stack

**Backend:** Python, FastAPI, boto3/aioboto3, DynamoDB, Redis pub/sub

**Frontend:** Vue 3, Vue Router, Vite

**Infra:** Docker Compose, DynamoDB Local, Redis
