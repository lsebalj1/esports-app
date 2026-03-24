import asyncio
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.event_processor import start_processor
from app.routes.stats import router as stats_router

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="Statistics Service",
    description="Consumes match events and maintains player stats and leaderboards.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(stats_router)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(start_processor())

@app.get("/health")
def health():
    return {"service": "statistics", "status": "ok"}