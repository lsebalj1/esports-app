from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.tournament import router as tournament_router

app = FastAPI(
    title="Tournament Service",
    description="Manages tournaments, registrations, and bracket generation.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tournament_router)

@app.get("/health")
def health():
    return {"service": "tournament", "status": "ok"}
