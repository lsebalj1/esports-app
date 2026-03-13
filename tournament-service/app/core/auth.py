import httpx
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from app.core.config import settings

bearer = HTTPBearer(auto_error=False)

async def require_auth(credentials: HTTPAuthorizationCredentials = Depends(bearer)) -> dict:
    if not credentials:
        raise HTTPException(status_code=401, detail="Missing token")
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{settings.auth_service_url}/auth/verify",
            headers={"Authorization": f"Bearer {credentials.credentials}"},
            timeout=5.0,
        )
    data = resp.json()
    if not data.get("valid"):
        raise HTTPException(status_code=401, detail="Invalid token")
    return data

async def require_organizer(user: dict = Depends(require_auth)) -> dict:
    if user["role"] not in ("organizer", "admin"):
        raise HTTPException(status_code=403, detail="Organizer role required")
    return user