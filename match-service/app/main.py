from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.match import router as match_router

app = FastAPI(
    title="Match Service",
    description="Manages match lifecycle, player assignment, and result submission.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(match_router)

@app.get("/health")
def health():
    return {"service": "match", "status": "ok"}
